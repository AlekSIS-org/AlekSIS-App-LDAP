from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from aleksis.core.util.apps import AppConfig

from .util.ldap_sync import ldap_sync_user_on_login, update_dynamic_preferences


class LDAPConfig(AppConfig):
    name = "aleksis.apps.ldap"
    verbose_name = "AlekSIS — LDAP (General LDAP import/export)"

    urls = {
        "Repository": "https://edugit.org/AlekSIS/official/AlekSIS-App-LDAP/",
    }
    licence = "EUPL-1.2+"
    copyright = (
        ([2020], "Dominik George", "dominik.george@teckids.org"),
        ([2020], "Tom Teichler", "tom.teichler@teckids.org"),
    )

    def ready(self) -> None:
        super().ready()

        update_dynamic_preferences()

        User = get_user_model()
        if get_site_preferences()["ldap__person_sync_on_login"]:
            post_save.connect(ldap_sync_user_on_login, sender=User)
