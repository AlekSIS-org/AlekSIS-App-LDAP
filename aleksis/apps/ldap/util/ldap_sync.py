from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from constance import config


def setting_name_from_field(model, field):
    """ Generate a constance setting name from a model field """

    return "LDAP_ADDITIONAL_FIELD_%s_%s" % (model._meta.label, field.name)


def syncable_fields(model):
    """ Collect all fields that can be synced on a model """

    return [field for field in model._meta.fields if field.editable and not field.auto_created]


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
            setting_names.append(setting_name)

        # Add separate constance section if settings were generated
        if setting_names:
            fieldset_name = "LDAP-Sync: Additional fields for %s" % model._meta.verbose_name
            settings.CONSTANCE_CONFIG_FIELDSETS[fieldset_name] = setting_names


def ldap_sync_from_user(sender, instance, created, raw, using, update_fields, **kwargs):
    """ Synchronise Person meta-data and groups from ldap_user on User update. """

    # Semaphore to guard recursive saves within this signal
    if getattr(instance, "_skip_signal", False):
        return
    instance._skip_signal = True

    Person = apps.get_model("core", "Person")
    Group = apps.get_model("core", "Group")

    if config.ENABLE_LDAP_SYNC and (created or config.LDAP_SYNC_ON_UPDATE) and hasattr(instance, "ldap_user"):
        # Check if there is an existing person connected to the user.
        if not Person.objects.filter(user=instance).exists():
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
                return

            person.user = instance
            person.save()

        # Synchronise additional fields if enabled
        for field in syncable_fields(Person):
            setting_name = setting_name_from_field(Person, field)

            # Try sync if constance setting for this field is non-empty
            ldap_field = getattr(config, setting_name, "")
            if ldap_field and ldap_field in instance.ldap_user.attrs.data:
                setattr(instance.person, field.name, instance.ldap_user.attrs.data[ldap_field][0])

        instance.person.save()

        if config.ENABLE_LDAP_GROUP_SYNC:
            # Resolve Group objects from LDAP group objects
            group_objects = []
            groups = instance.ldap_user._get_groups()
            group_infos = list(groups._get_group_infos())
            for ldap_group in group_infos:
                group, created = Group.objects.update_or_create(
                    import_ref = ldap_group[0],
                    defaults = {
                        "short_name": ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME][0][-16:],
                        "name": ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_NAME][0][:60]
                    }
                )

                group_objects.append(group)

            # Replace linked groups of logged-in user completely
            instance.person.member_of.set(group_objects)

            # Sync additional fields if enabled in config.
            ldap_user = instance.ldap_user

    # Remove semaphore
    del instance._skip_signal
