import logging
import re

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import fields
from django.utils.translation import gettext as _

from constance import config


logger = logging.getLogger(__name__)


def setting_name_from_field(model, field):
    """ Generate a constance setting name from a model field """

    return "LDAP_ADDITIONAL_FIELD_%s_%s" % (model._meta.label, field.name)


def syncable_fields(model):
    """ Collect all fields that can be synced on a model """

    return [field for field in model._meta.fields if (
        field.editable and not field.auto_created and not field.is_relation)]


def from_ldap(value, field):
    """ Convert an LDAP value to the Python type of the target field

    This conversion is prone to error because LDAP deliberately breaks
    standards to cope with ASN.1 limitations.
    """

    from ldapdb.models.fields import datetime_from_ldap  # noqa

    # Pre-convert DateTimeField and DateField due to ISO 8601 limitations in RFC 4517
    if type(field) in (fields.DateField, fields.DateTimeField):
        # Be opportunistic, but keep old value if conversion fails
        value = datetime_from_ldap(value) or value

    # Finally, use field's conversion method as default
    return field.to_python(value)


def update_constance_config_fields():
    """ Auto-generate sync field settings from models """

    Person = apps.get_model("core", "Person")
    for model in (Person,):
        # Collect fields that are matchable
        setting_names = []
        for field in syncable_fields(model):
            setting_name = setting_name_from_field(model, field)
            setting_desc = field.verbose_name

            settings.CONSTANCE_CONFIG[setting_name] = ("", setting_desc, str)
            settings.CONSTANCE_CONFIG[setting_name + "_RE"] = ("", _("Regular expression to match LDAP value for %s against") % setting_desc, str)
            settings.CONSTANCE_CONFIG[setting_name + "_REPLACE"] = ("", _("Replacement template to apply to %s") % setting_desc, str)

            setting_names += [setting_name, setting_name + "_RE", setting_name + "_REPLACE"]

        # Add separate constance section if settings were generated
        if setting_names:
            fieldset_name = "LDAP-Sync: Additional fields for %s" % model._meta.verbose_name
            settings.CONSTANCE_CONFIG_FIELDSETS[fieldset_name] = setting_names


def apply_templates(value, patterns, templates, separator="|"):
    """ Regex-replace patterns in value in order """

    if isinstance(patterns, str):
        patterns = patterns.split(separator)
    if isinstance(templates, str):
        templates = templates.split(separator)

    for pattern, template in zip(patterns, templates):
        if not pattern or not template:
            continue

        match = re.fullmatch(pattern, value)
        if match:
            value = match.expand(template)

    return value


def ldap_sync_from_user(sender, instance, created, **kwargs):
    """ Synchronise Person meta-data and groups from ldap_user on User update. """

    # Semaphore to guard recursive saves within this signal
    if getattr(instance, "_skip_signal", False):
        return
    instance._skip_signal = True

    Person = apps.get_model("core", "Person")
    Group = apps.get_model("core", "Group")

    if config.ENABLE_LDAP_SYNC and (created or config.LDAP_SYNC_ON_UPDATE) and hasattr(instance, "ldap_user"):
        # Check if there is an existing person connected to the user.
        if Person.objects.filter(user=instance).exists():
            person = instance.person
            logger.info("Existing person %s already linked to user %s" % (str(person), instance.username))
        else:
            # Build filter criteria depending on config
            matches = {}
            if "-email" in config.LDAP_MATCHING_FIELDS:
                matches["email"] = instance.email
            if "-name" in config.LDAP_MATCHING_FIELDS:
                matches["first_name"] = instance.first_name
                matches["last_name"] = instance.last_name

            try:
                person = Person.objects.get(**matches)
            except Person.DoesNotExist:
                # Bail out of further processing
                logger.info("No matching person for user %s" % instance.username)
                return

            person.user = instance
            logger.info("Matching person %s linked to user %s" % (str(person), instance.username))

        # Synchronise additional fields if enabled
        for field in syncable_fields(Person):
            setting_name = setting_name_from_field(Person, field)

            # Try sync if constance setting for this field is non-empty
            ldap_field = getattr(config, setting_name, "").lower()
            if ldap_field and ldap_field in instance.ldap_user.attrs.data:
                value = instance.ldap_user.attrs.data[ldap_field][0]

                # Apply regex replace from config
                patterns = getattr(config, setting_name + "_RE", "")
                templates = getattr(config, setting_name + "_REPLACE", "")
                value = apply_templates(value, patterns, templates)

                # Opportunistically convert LDAP string value to Python object
                value = from_ldap(value, field)

                setattr(person, field.name, value)
                logger.debug("Field %s set to %s for %s" % (field.name, str(value), str(person)))

        if config.ENABLE_LDAP_GROUP_SYNC:
            # Resolve Group objects from LDAP group objects
            group_objects = []
            groups = instance.ldap_user._get_groups()
            group_infos = list(groups._get_group_infos())
            for ldap_group in group_infos:
                # Skip group if one of the name fields is missing
                if config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME not in ldap_group[1]:
                    logger.error("LDAP group with DN %s does not have field %s" % (
                        ldap_group[0],
                        config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME
                    ))
                    continue
                if config.LDAP_GROUP_SYNC_FIELD_NAME not in ldap_group[1]:
                    logger.error("LDAP group with DN %s does not have field %s" % (
                        ldap_group[0],
                        config.LDAP_GROUP_SYNC_FIELD_NAME
                    ))
                    continue

                # Apply regex replace from config
                short_name = apply_templates(
                    ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME][0],
                    config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME_RE,
                    config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME_REPLACE
                )
                name = apply_templates(
                    ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_NAME][0],
                    config.LDAP_GROUP_SYNC_FIELD_NAME_RE,
                    config.LDAP_GROUP_SYNC_FIELD_NAME_REPLACE
                )

                # Shorten names to fit into model fields
                short_name = short_name[:Group._meta.get_field("short_name").max_length]
                name = name[:Group._meta.get_field("name").max_length]

                group, created = Group.objects.update_or_create(
                    import_ref = ldap_group[0],
                    defaults = {
                        "short_name": short_name,
                        "name": name
                    }
                )
                logger.info("%s LDAP group %s for Django group %s" % (
                    ("Created" if created else "Updated"),
                    ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_NAME][0],
                    name
                ))

                group_objects.append(group)

            # Replace linked groups of logged-in user completely
            person.member_of.set(group_objects)
            logger.info("Replaced group memberships of %s" % str(person))

        try:
            person.save()
        except Exception as e:
            # Exceptions here are logged only because the synchronisation is optional
            # FIXME throw warning to user instead
            logger.error("Could not save person %s:\n%s" % (str(person), str(e)))

    # Remove semaphore
    del instance._skip_signal


def mass_ldap_import():
    """ Utility code for mass import from ldap """

    from django_auth_ldap.backend import LDAPBackend, _LDAPUser  # noqa

    # Abuse pre-configured search object to find all users by letting * pass
    backend = LDAPBackend()
    res = backend.settings.USER_SEARCH.execute(_LDAPUser(backend, "").connection, {"user": "*"}, escape=False)

    # Guess LDAP username field from user filter
    uid_field = re.search(r"([a-zA-Z]+)=%\(user\)s", backend.settings.USER_SEARCH.filterstr).group(1)

    uids = [entry[1][uid_field][0] for entry in res]

    for uid in uids:
        # Prepare an empty LDAPUser object with the target username
        ldap_user = _LDAPUser(backend, username=uid)

        # Find out whether the User object would be created, but do not save
        _, created = backend.get_or_build_user(uid, backend.ldap_to_django_username(ldap_user))
        logger.info("Will %s user %s in Django" % ("create" if created else "update", uid))

        # Run creation and/or population, like the auth backend would
        ldap_user._get_or_create_user()
        user = ldap_user._user

        # Trigger sync run like on login signal
        ldap_sync_from_user(user.__class__, user, created)

        logger.info("Successfully imported user %s" % uid)
