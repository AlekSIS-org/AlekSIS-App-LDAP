from django.apps import apps
from django.contrib.auth import get_user_model

from constance import config


def ldap_create_user(sender, instance, created, raw, using, update_fields, **kwargs):
    """ Find ldap users by configurable matching fields and connect them to django users. """
    Person = apps.get_model("core", "Person")

    if config.ENABLE_LDAP_SYNC and (created or config.LDAP_SYNC_ON_UPDATE):
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

            # Sync additional fields if enabled in config.
            ldap_user = instance.ldap_user
            person.street = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_STREET]
            person.housenumber = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_HOUSENUMBER]
            person.postal_code = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_POSTAL_CODE]
            person.place = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_PLACE]
            person.phone_number = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_PHONE_NUMBER]
            person.mobile_number = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_MOBILE_NUMBER]
            person.date_of_birth = ldap_user.attrs.data[config.LDAP_SYNC_FIELD_DATE_OF_BIRTH]

            # Save person if enabled in config or no new person was created.
            if config.LDAP_SYNC_CREATE or not created:
                person.user = instance
                person.save()
