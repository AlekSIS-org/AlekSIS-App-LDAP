from aleksis.core.util.apps import AppConfig

from .util.ldap_sync import ldap_sync_user_on_login, update_dynamic_preferences


class LDAPConfig(AppConfig):
    name = "aleksis.apps.ldap"
    verbose_name = "AlekSIS — LDAP (General LDAP import/export)"

    urls = {
        "Repository": "https://edugit.org/AlekSIS/official/AlekSIS-App-LDAP/",
    }
    licence = "EUPL-1.2+"
    copyright_info = (
        ([2020], "Dominik George", "dominik.george@teckids.org"),
        ([2020], "Tom Teichler", "tom.teichler@teckids.org"),
    )

    def ready(self) -> None:
        super().ready()

        update_dynamic_preferences()

        from django_auth_ldap.backend import populate_user  # noqa

        populate_user.connect(ldap_sync_user_on_login)
