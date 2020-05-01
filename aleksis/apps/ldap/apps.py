from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from dynamic_preferences.registries import preference_models

from aleksis.core.util.apps import AppConfig
from aleksis.core.registries import site_preferences_registry

from .util.ldap_sync import ldap_sync_user_on_login, update_constance_config_fields

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

        SitePreferenceModel = self.get_model('SitePreferenceModel')

        preference_models.register(SitePreferenceModel, site_preferences_registry)

        update_constance_config_fields()

        User = get_user_model()
        post_save.connect(ldap_sync_user_on_login, sender=User)
