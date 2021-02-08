def ldap_change_password(request, user, **kwargs):
    # Get old and new password from submitted form
    # We rely on allauth already having validated the form before emitting the signal
    old = request.POST["oldpassword"]
    new = request.POST["password1"]

    # Get low-level LDAP connection and update password
    conn = user.ldap_user._get_connection()
    conn.passwd_s(user.ldap_user.dn, old, new)
