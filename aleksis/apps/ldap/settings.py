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
    "LDAP_SYNC_ON_UPDATE": (True, _("Also sync if user updates"), bool),
    "LDAP_MATCHING_FIELDS": (
        None,
        _("LDAP sync matching fields"),
        "matching-fields-select",
    ),
    "LDAP_SYNC_FIELD_STREET": (None, _("Field for street"), str),
    "LDAP_SYNC_FIELD_HOUSENUMBER": (None, _("Field for house number"), str),
    "LDAP_SYNC_FIELD_POSTAL_CODE": (None, _("Field for postal code"), str),
    "LDAP_SYNC_FIELD_PLACE": (None, _("Field for place"), str),
    "LDAP_SYNC_FIELD_PHONE_NUMBER": (None, _("Field for phone number"), str),
    "LDAP_SYNC_FIELD_MOBILE_NUMBER": (None, _("Field for mobile number"), str),
    "LDAP_SYNC_FIELD_DATE_OF_BIRTH": (None, _("Field for date of birth"), str),
    "ENABLE_LDAP_GROUP_SYNC": (True, _("Enable ldap group sync"), bool),
    "LDAP_GROUP_SYNC_FIELD_SHORT_NAME": ("cn", _("Field for short name of group"), str),
    "LDAP_GROUP_SYNC_FIELD_NAME": ("cn", _("Field for name of group"), str),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "LDAP-Sync settings": (
        "ENABLE_LDAP_SYNC",
        "LDAP_SYNC_ON_UPDATE",
        "LDAP_MATCHING_FIELDS",
        "LDAP_SYNC_FIELD_STREET",
        "LDAP_SYNC_FIELD_HOUSENUMBER",
        "LDAP_SYNC_FIELD_POSTAL_CODE",
        "LDAP_SYNC_FIELD_PLACE",
        "LDAP_SYNC_FIELD_PHONE_NUMBER",
        "LDAP_SYNC_FIELD_MOBILE_NUMBER",
        "LDAP_SYNC_FIELD_DATE_OF_BIRTH",
        "ENABLE_LDAP_GROUP_SYNC",
        "LDAP_GROUP_SYNC_FIELD_SHORT_NAME",
        "LDAP_GROUP_SYNC_FIELD_NAME",
    ),
}
