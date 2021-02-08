from aleksis.core.util.core_helpers import get_site_preferences


def ldap_change_password(request, user, **kwargs):
    if not get_site_preferences()["ldap__enable_password_change"]:
        # Do nothing if password change in LDAP is disabled
        return

    # Get old and new password from submitted form
    # We rely on allauth already having validated the form before emitting the signal
    old = request.POST["oldpassword"]
    new = request.POST["password1"]

    # Get low-level LDAP connection and update password
    conn = user.ldap_user._get_connection()
    conn.bind_s(user.ldap_user.dn, old)
    conn.passwd_s(user.ldap_user.dn, old, new)
