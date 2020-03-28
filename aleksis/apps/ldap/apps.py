from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from aleksis.core.util.apps import AppConfig

from .util.ldap_sync import ldap_sync_from_user, update_constance_config_fields

class LDAPConfig(AppConfig):
    name = "aleksis.apps.ldap"
    verbose_name = "AlekSIS — LDAP (General LDAP import/export)"

    def ready(self) -> None:
        super().ready()

        update_constance_config_fields()

        User = get_user_model()
        post_save.connect(ldap_sync_from_user, sender=User)
