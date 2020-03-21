from django.utils.translation import gettext_lazy as _

CONSTANCE_ADDITIONAL_FIELDS = {
    "strategy-select": ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((None, "-----"),
                    ("match-only", _("Only match persons to users")),
                    ("match-create", _("Match and create persons")),
                    )
    }],
    "matching-fields-select": ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((None, "-----"),
                    ("match-email", _("Match only on email")),
                    ("match-name", _("Match only on name")),
                    ("match-email-name", _("Match on email and name")),
                    )
    }],
}

CONSTANCE_CONFIG = {
    "ENABLE_LDAP_SYNC": (True, _("Enable ldap sync"), bool),
    "LDAP_SYNC_CREATE": (True, _("Match created persons to users"), bool),
    "LDAP_MATCHING_FIELDS": (None, _("LDAP sync matching fields"), "matching-fields-select"),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "LDAP-Sync settings": ("ENABLE_LDAP_SYNC", "LDAP_SYNC_CREATE", "LDAP_MATCHING_FIELDS"),
}
