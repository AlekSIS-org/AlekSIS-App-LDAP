from django.utils.translation import gettext_lazy as _

CONSTANCE_ADDITIONAL_FIELDS = {
    "matching-fields-select": [
        "django.forms.fields.ChoiceField",
        {
            "widget": "django.forms.Select",
            "choices": (
                (None, "-----"),
                ("match-email", _("Match only on email")),
                ("match-name", _("Match only on name")),
                ("match-email-name", _("Match on email and name")),
            ),
        },
    ],
}

CONSTANCE_CONFIG = {
    "ENABLE_LDAP_SYNC": (True, _("Enable ldap sync"), bool),
    "LDAP_SYNC_CREATE": (True, _("Match created persons to users"), bool),
    "LDAP_SYNC_ON_UPDATE": (True, _("Also sync if user updates"), bool),
    "LDAP_MATCHING_FIELDS": (
        None,
        _("LDAP sync matching fields"),
        "matching-fields-select",
    ),
    "LDAP_GROUP_SYNC_FIELD_SHORT_NAME": ("cn", _("Field for short name of group"), str),
    "LDAP_GROUP_SYNC_FIELD_NAME": ("cn", _("Field for name of group"), str),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "LDAP-Sync settings": (
        "ENABLE_LDAP_SYNC",
        "LDAP_SYNC_CREATE",
        "LDAP_SYNC_ON_UPDATE",
        "LDAP_MATCHING_FIELDS",
        "LDAP_GROUP_SYNC_FIELD_SHORT_NAME",
        "LDAP_GROUP_SYNC_FIELD_NAME",
    ),
}
