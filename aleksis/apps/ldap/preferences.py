from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.types import BooleanPreference, ChoicePreference, StringPreference

from aleksis.core.registries import site_preferences_registry

ldap = Section("ldap")


@site_preferences_registry.register
class EnableLDAPSync(BooleanPreference):
    section = ldap
    name = "enable_sync"
    default = True
    required = False
    verbose_name = _("Enable LDAP sync")


@site_preferences_registry.register
class LDAPSyncOnUpdate(BooleanPreference):
    section = ldap
    name = "sync_on_update"
    default = True
    required = False
    verbose_name = _("Also sync LDAP if user updates")


@site_preferences_registry.register
class LDAPSyncCreateMissingPersons(BooleanPreference):
    section = ldap
    name = "create_missing_persons"
    default = True
    required = False
    verbose_name = _("Create missing persons for LDAP users")


@site_preferences_registry.register
class LDAPMatchingFields(ChoicePreference):
    section = ldap
    name = "matching_fields"
    default = ""
    required = False
    verbose_name = _("LDAP sync matching fields")
    choices = [
        ("", "-----"),
        ("match-email", _("Match only on email")),
        ("match-name", _("Match only on name")),
        ("match-email-name", _("Match on email and name")),
    ]


@site_preferences_registry.register
class EnableLDAPGroupSync(BooleanPreference):
    section = ldap
    name = "enable_group_sync"
    default = True
    required = False
    verbose_name = _("Enable ldap group sync")


@site_preferences_registry.register
class LDAPGroupSyncFieldShortName(StringPreference):
    section = ldap
    name = "group_sync_field_short_name"
    default = "cn"
    required = False
    verbose_name = _("Field for short name of group")


@site_preferences_registry.register
class LDAPGroupSyncFieldShortNameRE(StringPreference):
    section = ldap
    name = "group_sync_field_short_name_re"
    default = ""
    required = False
    verbose_name = _(
        "Regular expression to match LDAP value for group short name against,"
        "e.g. class_(?P<class>.*); separate multiple patterns by |"
    )


@site_preferences_registry.register
class LDAPGroupSyncFieldShortNameReplace(StringPreference):
    section = ldap
    name = "group_sync_field_short_name_replace"
    default = ""
    required = False
    verbose_name = _(
        "Replacement template to apply to group short name,"
        "e.g. \\g<class>; separate multiple templates by |"
    )


@site_preferences_registry.register
class LDAPGroupSyncFieldName(StringPreference):
    section = ldap
    name = "group_sync_field_name"
    default = "cn"
    required = False
    verbose_name = _("Field for name of group")


@site_preferences_registry.register
class LDAPGroupSyncFieldNameRE(StringPreference):
    section = ldap
    name = "group_sync_field_name_re"
    default = ""
    required = False
    verbose_name = _(
        "Regular expression to match LDAP value for group name against,"
        "e.g. class_(?P<class>.*); separate multiple patterns by |"
    )


@site_preferences_registry.register
class LDAPGroupSyncFieldNameReplace(StringPreference):
    section = ldap
    name = "group_sync_field_name_replace"
    default = ""
    required = False
    verbose_name = _(
        "Replacement template to apply to group name,"
        "e.g. \\g<class>; separate multiple templates by |"
    )


@site_preferences_registry.register
class LDAPGroupSyncOwnerAttr(StringPreference):
    section = ldap
    name = "group_sync_owner_attr"
    default = ""
    required = False
    verbose_name = _("LDAP field with dn of group owner")


@site_preferences_registry.register
class LDAPGroupSyncOwnerAttrType(ChoicePreference):
    section = ldap
    name = "group_sync_owner_attr_type"
    default = "dn"
    required = False
    verbose_name = _("LDAP sync matching fields")
    choices = [
        ("dn", _("Distinguished Name")),
        ("uid", _("UID")),
    ]


@site_preferences_registry.register
class LDAPPersonSyncOnLogin(BooleanPreference):
    section = ldap
    name = "person_sync_on_login"
    default = True
    required = False
    verbose_name = _("Sync LDAP user with person on login")
