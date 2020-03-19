from django.utils.translation import gettext_lazy as _

CONSTANCE_ADDITIONAL_FIELDS = {
    "strategy-select": ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((None, "-----"),
                    ("match-only", _("Only match persons to users")),
                    ("match-create", _("Match and create persons")),
                    )
    }],
}

CONSTANCE_CONFIG = {
    "ENABLE_LDAP_SYNC": ("yes", _("Enable ldap sync"), "bool"),
    "LDAP_SYNC_STRATEGY": ("None", _("Strategy for ldap sync"), "strategy-select"),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "LDAP-Sync settings": ("ENABLE_LDAP_SYNC", "LDAP_SYNC_STRATEGY"),
}
