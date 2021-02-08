from aleksis.core.util.core_helpers import get_site_preferences


def ldap_change_password(request, user, **kwargs):
    enable_password_change = get_site_preferences()["ldap__enable_password_change"]
    admin_password_change = get_site_preferences()["ldap__admin_password_change"]
    admin_dn = get_site_preferences()["ldap__admin_dn"]
    admin_password = get_site_preferences()["ldap__admin_password"]

    if not enable_password_change:
        # Do nothing if password change in LDAP is disabled
        return

    # Get old and new password from submitted form
    # We rely on allauth already having validated the form before emitting the signal
    old = request.POST.get("oldpassword", None)
    new = request.POST["password1"]

    # Get low-level LDAP connection and update password
    conn = user.ldap_user._get_connection()
    if old and not admin_password_change:
        # If we are changing a password as user, use their credentials
        # except if the preference mandates always using admin credentials
        conn.bind_s(user.ldap_user.dn, old)
    elif admin_dn:
        # In all other cases, use admin credentials if available
        # If not available, try using the regular LDAP auth credentials
        conn.bind_s(admin_dn, admin_password)
    conn.passwd_s(user.ldap_user.dn, old, new)

    # Unbind so we do not leak connections with elevated privileges
    conn.unbind_s()
