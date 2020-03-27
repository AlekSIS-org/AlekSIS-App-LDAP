from django.apps import apps
from django.contrib.auth import get_user_model

from constance import config


def ldap_create_user(sender, instance, created, raw, using, update_fields, **kwargs):
    """ Find ldap users by configurable matching fields and connect them to django users. """
    Person = apps.get_model("core", "Person")
    Group = apps.get_model("core", "Group")

    if config.ENABLE_LDAP_SYNC and (created or config.LDAP_SYNC_ON_UPDATE) and hasattr(instance, "ldap_user"):
        # Check if there is an existing person connected to the user.
        if not Person.objects.filter(user=instance).exists():
            if config.LDAP_MATCHING_FIELDS == "match-email":
                # Get or create a person matching to email field.
                person, created = Person.objects.get_or_create(
                    email=instance.email,
                    defaults={
                        "first_name": instance.first_name,
                        "last_name": instance.last_name,
                    },
                )
            elif config.LDAP_MATCHING_FIELDS == "match-name":
                # Get or create a person matching to the first and last name.
                person, created = Person.objects.get_or_create(
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    defaults={"email": instance.email},
                )
            elif config.LDAP_MATCHING_FIELDS == "match-email-name":
                # Get or create a person matching to the email and the first and last name.
                person, created = Person.objects.get_or_create(
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    email=instance.email,
                )

            # Save person if enabled in config or no new person was created.
            if config.LDAP_SYNC_CREATE or not created:
                person.user = instance
                person.save()

        if config.ENABLE_LDAP_GROUP_SYNC:
            group_objects = []
            groups = instance.ldap_user._get_groups()
            group_infos = list(groups._get_group_infos())
            for ldap_group in group_infos:
                group, created = Group.objects.get_or_create(
                    import_ref = ldap_group[0],
                    defaults = {
                        "short_name": ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_SHORT_NAME][0][-16:],
                        "name": ldap_group[1][config.LDAP_GROUP_SYNC_FIELD_NAME][0][:60]
                    }
                )

                if config.LDAP_SYNC_CREATE_GROUPS or not created:
                    group.save()
                    group_objects.append(group)

            instance.person.member_of.set(group_objects)
