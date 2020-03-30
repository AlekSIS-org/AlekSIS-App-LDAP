from django.apps import apps
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
    "owner-attr-type": [
        "django.forms.fields.ChoiceField",
        {
            "widget": "django.forms.Select",
            "choices": (
                ("dn", _("Distinguished Name")),
                ("uid", _("UID")),
            ),
        },
    ],
}

CONSTANCE_CONFIG = {
    "ENABLE_LDAP_SYNC": (True, _("Enable ldap sync"), bool),
    "LDAP_SYNC_ON_UPDATE": (True, _("Also sync if user updates"), bool),
    "LDAP_SYNC_CREATE_MISSING_PERSONS": (True, _("Create missing persons for LDAP users"), bool),
    "LDAP_MATCHING_FIELDS": (
        None,
        _("LDAP sync matching fields"),
        "matching-fields-select",
    ),
    "ENABLE_LDAP_GROUP_SYNC": (True, _("Enable ldap group sync"), bool),
    "LDAP_GROUP_SYNC_FIELD_SHORT_NAME": ("cn", _("Field for short name of group"), str),
    "LDAP_GROUP_SYNC_FIELD_SHORT_NAME_RE": ("", _("Regular expression to match LDAP value for group short name against, e.g. class_(?P<class>.*); separate multiple patterns by |"), str),
    "LDAP_GROUP_SYNC_FIELD_SHORT_NAME_REPLACE": ("", _("Replacement template to apply to group short name, e.g. \\g<class>; separate multiple templates by |"), str),
    "LDAP_GROUP_SYNC_FIELD_NAME": ("cn", _("Field for name of group"), str),
    "LDAP_GROUP_SYNC_FIELD_NAME_RE": ("", _("Regular expression to match LDAP value for group name against, e.g. class_(?P<class>.*); separate multiple patterns by |"), str),
    "LDAP_GROUP_SYNC_FIELD_NAME_REPLACE": ("", _("Replacement template to apply to group name, e.g. \\g<class>; separate multiple templates by |"), str),
    "LDAP_GROUP_SYNC_OWNER_ATTR": ("", _("LDAP field with dn of group owner"), str),
    "LDAP_GROUP_SYNC_OWNER_ATTR_TYPE": ("dn", _("Type of data in the ldap_field. Either DN or UID"), "owner-attr-type"),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "LDAP-Sync settings": (
        "ENABLE_LDAP_SYNC",
        "LDAP_SYNC_ON_UPDATE",
        "LDAP_SYNC_CREATE_MISSING_PERSONS",
        "LDAP_MATCHING_FIELDS",
        "ENABLE_LDAP_GROUP_SYNC",
        "LDAP_GROUP_SYNC_OWNER_ATTR",
        "LDAP_GROUP_SYNC_OWNER_ATTR_TYPE",
        "LDAP_GROUP_SYNC_FIELD_SHORT_NAME",
        "LDAP_GROUP_SYNC_FIELD_SHORT_NAME_RE",
        "LDAP_GROUP_SYNC_FIELD_SHORT_NAME_REPLACE",
        "LDAP_GROUP_SYNC_FIELD_NAME",
        "LDAP_GROUP_SYNC_FIELD_NAME_RE",
        "LDAP_GROUP_SYNC_FIELD_NAME_REPLACE",
    ),
}
