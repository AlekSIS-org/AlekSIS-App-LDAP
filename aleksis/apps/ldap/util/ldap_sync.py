from django.apps import apps
from django.contrib.auth import get_user_model

from constance import config


def ldap_create_user(sender, instance, created, raw, using, update_fields, **kwargs):
    """ Find ldap users by configurable matching fields and connect them to django users. """
    Person = apps.get_model("core", "Person")

    if config.ENABLE_LDAP_SYNC and (created or config.LDAP_SYNC_ON_UPDATE):
        # Check if there is an existing person connected to the user.
        if not Person.objects.filter(user=instance).exists():
            if config.LDAP_MATCHING_FIELDS == 'match-email':
                # Get or create a person matching to email field.
                person, created = Person.objects.get_or_create(
                    email=instance.email,
                    defaults={
                        "first_name": instance.first_name,
                        "last_name": instance.last_name,
                    }
                )
            elif config.LDAP_MATCHING_FIELDS == 'match-name':
                # Get or create a person matching to the first and last name.
                person, created = Person.objects.get_or_create(
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    defaults={
                        "email": instance.email
                    }
                )
            elif config.LDAP_MATCHING_FIELDS == 'match-email-name':
                # Get or create a person matching to the email and the first and last name.
                person, created = Person.objects.get_or_create(
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    email=instance.email
                )

            # Save person if enabled in config or no new person was created.
            if config.LDAP_SYNC_CREATE or not created:
                person.user = instance
                person.save()
