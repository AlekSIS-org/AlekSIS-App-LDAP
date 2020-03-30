import logging
import re

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DataError, IntegrityError, transaction
from django.db.models import fields
from django.utils.translation import gettext as _

from constance import config
from tqdm import tqdm


logger = logging.getLogger(__name__)

TQDM_DEFAULTS = {
 "disable": None,
 "unit": "obj",
 "dynamic_ncols": True,
}

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


@transaction.atomic
def ldap_sync_user_on_login(sender, instance, created, **kwargs):
    """ Synchronise Person meta-data and groups from ldap_user on User update. """

    # Semaphore to guard recursive saves within this signal
    if getattr(instance, "_skip_signal", False):
        return
    instance._skip_signal = True

    Person = apps.get_model("core", "Person")

    if config.ENABLE_LDAP_SYNC and (created or config.LDAP_SYNC_ON_UPDATE) and hasattr(instance, "ldap_user"):
        try:
            with transaction.atomic():
                person = ldap_sync_from_user(instance, instance.ldap_user.dn, instance.ldap_user.attrs.data)
        except Person.DoesNotExist:
            logger.warn("No matching person for user %s" % user.username)
            return
        except Person.MultipleObjectsReturned:
            logger.error("More than one matching person for user %s" % user.username)
            return
        except (DataError, IntegrityError, ValueError) as e:
            logger.error("Data error while synchronising user %s:\n%s" % (user.username, str(e)))
            return

        if config.ENABLE_LDAP_GROUP_SYNC:
            # Get groups from LDAP
            groups = instance.ldap_user._get_groups()
            group_infos = list(groups._get_group_infos())
            group_objects = get_ldap_groups(group_infos)

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


@transaction.atomic
def ldap_sync_from_user(user, dn, attrs):
    """ Synchronise person information from a User object (with ldap_user) to Django """

    Person = apps.get_model("core", "Person")

    # Check if there is an existing person connected to the user.
    if Person.objects.filter(user__username=user.username).exists():
        person = user.person
        created = False
        logger.info("Existing person %s already linked to user %s" % (str(person), user.username))
    # FIXME ALso account for existing person with DN here
    else:
        # Build filter criteria depending on config
        matches = {}
        defaults = {}
        if "-email" in config.LDAP_MATCHING_FIELDS:
            matches["email"] = user.email
            defaults["first_name"] = user.first_name
            defaults["last_name"] = user.last_name
        if "-name" in config.LDAP_MATCHING_FIELDS:
            matches["first_name"] = user.first_name
            matches["last_name"] = user.last_name
            defaults["email"] = user.email

        if config.LDAP_SYNC_CREATE_MISSING_PERSONS:
            person, created = Person.objects.get_or_create(**matches, defaults=defaults)
        else:
            person = Person.objects.get(**matches)
            created = False

        person.user = user
        logger.info("%s person %s linked to user %s" % ("New" if created else "Existing", str(person), user.username))

    person.ldap_dn = dn.lower()
    if not created:
        person.first_name = user.first_name
        person.last_name = user.last_name
        person.email = user.email

    # Synchronise additional fields if enabled
    for field in syncable_fields(Person):
        setting_name = setting_name_from_field(Person, field)

        # Try sync if constance setting for this field is non-empty
        ldap_field = getattr(config, setting_name, "").lower()
        if ldap_field and ldap_field in attrs:
            value = attrs[ldap_field][0]

            # Apply regex replace from config
            patterns = getattr(config, setting_name + "_RE", "")
            templates = getattr(config, setting_name + "_REPLACE", "")
            value = apply_templates(value, patterns, templates)

            # Opportunistically convert LDAP string value to Python object
            value = from_ldap(value, field)

            setattr(person, field.name, value)
            logger.debug("Field %s set to %s for %s" % (field.name, str(value), str(person)))

    person.save()
    return person


@transaction.atomic
def ldap_sync_from_groups(group_infos):
    """ Synchronise group information from LDAP results to Django """

    Group = apps.get_model("core", "Group")

    # Resolve Group objects from LDAP group objects
    group_objects = []
    for ldap_group in tqdm(group_infos, desc="Sync. group infos", **TQDM_DEFAULTS):
        # Skip group if one of the name fields is missing
        # FIXME Throw exceptions and catch outside
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

        # FIXME FInd a way to throw exceptions correctly but still continue import
        try:
            with transaction.atomic():
                group, created = Group.objects.update_or_create(
                    ldap_dn = ldap_group[0].lower(),
                    defaults = {
                        "short_name": short_name,
                        "name": name
                    }
                )
        except IntegrityError as e:
            logger.error("Integrity error while trying to import LDAP group %s:\n%s" % (ldap_group[0], str(e)))
            continue
        else:
            logger.info("%s LDAP group %s for Django group %s" % (
                ("Created" if created else "Updated"),
                ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_NAME][0],
                name
            ))

        group_objects.append(group)

    return group_objects


@transaction.atomic
def mass_ldap_import():
    """ Utility code for mass import from ldap """

    from django_auth_ldap.backend import LDAPBackend, _LDAPUser  # noqa

    Person = apps.get_model("core", "Person")

    # Abuse pre-configured search object as general LDAP interface
    backend = LDAPBackend()
    connection = _LDAPUser(backend, "").connection

    # Synchronise all groups first
    if config.ENABLE_LDAP_GROUP_SYNC:
        ldap_groups = backend.settings.GROUP_SEARCH.execute(connection)
        group_objects = ldap_sync_from_groups(ldap_groups)

    # Guess LDAP username field from user filter
    uid_field = re.search(r"([a-zA-Z]+)=%\(user\)s", backend.settings.USER_SEARCH.filterstr).group(1)

    # Synchronise user data for all found users
    ldap_users = backend.settings.USER_SEARCH.execute(connection, {"user": "*"}, escape=False)
    for dn, attrs in tqdm(ldap_users, desc="Sync. user infos", **TQDM_DEFAULTS):
        uid = attrs[uid_field][0]

        # Prepare an empty LDAPUser object with the target username
        ldap_user = _LDAPUser(backend, username=uid)

        # Find out whether the User object would be created, but do not save
        user, created = backend.get_or_build_user(uid, ldap_user)
        if created:
            user.save()

        if created or config.LDAP_SYNC_ON_UPDATE:
            try:
                with transaction.atomic():
                    person = ldap_sync_from_user(user, dn, attrs)
            except Person.DoesNotExist:
                logger.warn("No matching person for user %s" % user.username)
                continue
            except Person.MultipleObjectsReturned:
                logger.error("More than one matching person for user %s" % user.username)
                continue
            except (DataError, IntegrityError, ValueError) as e:
                logger.error("Data error while synchronising user %s:\n%s" % (user.username, str(e)))
                continue
            else:
                logger.info("Successfully imported user %s" % uid)

    # Synchronise group memberships now
    if config.ENABLE_LDAP_GROUP_SYNC:
        member_attr = getattr(backend.settings.GROUP_TYPE, "member_attr", "memberUid")
        owner_attr = config.LDAP_GROUP_SYNC_OWNER_ATTR

        for group, ldap_group in tqdm(zip(group_objects, ldap_groups), desc="Sync. group members", total=len(group_objects), **TQDM_DEFAULTS):
            dn, attrs = ldap_group
            ldap_members = [_.lower() for _ in attrs[member_attr]] if member_attr in attrs else []

            if member_attr.lower() == "memberUid":
                members = Person.objects.filter(user__username__in=ldap_members)
            else:
                members = Person.objects.filter(ldap_dn__in=ldap_members)

            if config.LDAP_GROUP_SYNC_OWNER_ATTR:
                ldap_owners = [_.lower() for _ in attrs[owner_attr]] if owner_attr in attrs else []
                if config.LDAP_GROUP_SYNC_OWNER_ATTR_TYPE == "uid":
                    owners = Person.objects.filter(user__username__in=ldap_owners)
                elif config.LDAP_GROUP_SYNC_OWNER_ATTR_TYPE == "dn":
                    owners = Person.objects.filter(ldap_dn__in=ldap_owners)

            group.members.set(members)
            if config.LDAP_GROUP_SYNC_OWNER_ATTR:
                group.owners.set(owners)
            group.save()
            logger.info("Set group members of group %s" % str(group))
