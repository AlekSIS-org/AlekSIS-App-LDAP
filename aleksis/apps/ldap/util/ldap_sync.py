from django.apps import apps
from django.contrib.auth import get_user_model

from constance import config

def ldap_create_user(sender, **kwargs):
    Person = apps.get_model("core", "Person")
    if config.ENABLE_LDAP_SYNC:
        if not sender.person:
            if config.LDAP_SYNC_STRATEGY == 'match-create':
                if not Person.objects.get(full_name=sender.get_full_name()) or not Person.objects.get(email=sender.email):
                    person = Person.objects.create(
                        first_name = sender.first_name,
                        last_name = sender.last_name,
                        email = sender.email,
                        sender = sender,
                    )
                    sender.person = person
                    sender.save()
                else:
                    if Person.objects.get(full_name=sender.get_full_name()):
                        person = Person.objects.get(full_name=sender.get_full_name())
                        sender.person = person
                        sender.save()
                    elif Person.objects.get(email=sender.email):
                        person = Person.objects.get(email=sender.email)
                        sender.person = person
                        sender.save()
            elif config.LDAP_SYNC_STRATEGY == 'match-only':
                if Person.objects.get(full_name=sender.get_full_name()):
                    person = Person.objects.get(full_name=sender.get_full_name())
                    sender.person = person
                    sender.save()
                elif Person.objects.get(email=sender.email):
                    person = Person.objects.get(email=sender.email)
                    sender.person = person
                    sender.save()
