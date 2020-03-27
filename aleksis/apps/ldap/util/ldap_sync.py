from django.apps import apps
from django.contrib.auth import get_user_model

from constance import config


def ldap_sync_from_user(sender, instance, created, raw, using, update_fields, **kwargs):
    """ Synchronise Person meta-data and groups from ldap_user on User update. """

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
            person.street = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_STREET]
            person.housenumber = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_HOUSENUMBER]
            person.postal_code = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_POSTAL_CODE]
            person.place = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_PLACE]
            person.phone_number = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_PHONE_NUMBER]
            person.mobile_number = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_MOBILE_NUMBER]
            person.date_of_birth = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_DATE_OF_BIRTH]
