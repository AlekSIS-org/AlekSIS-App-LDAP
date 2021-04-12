from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

import sshpubkeys

from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Group, Person
from aleksis.core.util.core_helpers import get_site_preferences


def get_default_value_shell_preferences():
    return get_site_preferences()["posix__shell"]


def get_default_value_primary_gid_preferences():
    return get_site_preferences()["posix__gid"]


def validate_min_value_uid_preferences(value):
    if value < get_site_preferences()["posix__min_uid"]:
        raise ValidationError(_("Value smaller than minimum uid number!"))


def validate_min_value_gid_preferences(value):
    if value < get_site_preferences()["posix__min_gid"]:
        raise ValidationError(_("Value smaller than minimum gid number!"))


def validate_username_allowed(value):
    if value in get_site_preferences()["posix__disallowed_uids"].split(","):
        raise ValidationError(_("Username not allowed!"))


def validate_ssh_key(value):
    ssh_key = sshpubkeys.SSHKey(value)
    try:
        ssh_key.parse()
    except sshpubkeys.InvalidKeyError as e:
        raise ValidationError(_("Not a valid OpenSSH public key")) from e


class SSHKey(ExtensibleModel):
    """Model to store SSH keys uploaded by persons."""

    person = models.ForeignKey(
        Person, verbose_name=_("Person"), on_delete=models.CASCADE, related_name="ssh_keys",
    )

    key_data = models.TextField(verbose_name=_("SSH public key"), validators=[validate_ssh_key])

    @property
    def ssh_key(self):
        return sshpubkeys.SSHKey(self.key_data)

    def __str__(self) -> str:
        return self.ssh_key.comment

    class Meta:
        verbose_name = _("SSH key")
        verbose_name_plural = _("SSH keys")


class PersonPosixAttrs(ExtensibleModel):
    """Model to store POSIX attributs for POSIX users."""

    person = models.OneToOneField(
        Person,
        verbose_name=_("Related person"),
        related_name="posix_attrs",
        on_delete=models.CASCADE,
    )

    uid = models.PositiveIntegerField(
        verbose_name=_("UID Number"), unique=True, validators=[validate_min_value_uid_preferences],
    )
    home_directory = models.CharField(verbose_name=_("Home directory"), max_length=255)
    login_shell = models.CharField(
        verbose_name=_("Login shell"), default=get_default_value_shell_preferences, max_length=255
    )
    primary_gid = models.PositiveIntegerField(
        verbose_name=_("Primary GID Number"), default=get_default_value_primary_gid_preferences,
    )
    username = models.CharField(
        verbose_name=_("Username"),
        unique=True,
        validators=[validate_username_allowed,],
        max_length=32,
    )

    def clean_username(self) -> None:
        if not self.username and self.person.user:
            self.username = self.person.user.username
        RegexValidator(regex=r"^[A-Za-z0-9_.][A-Za-z0-9_.-]*$")(self.username)
        RegexValidator(regex=get_site_preferences()["posix__username_regex"])(self.username)

    def clean_uid(self) -> None:
        if not self.uid:
            self.uid = models.Max("uid") + 1

    class Meta:
        verbose_name = _("POSIX Attributes")


class GroupPosixAttrs(ExtensibleModel):
    """Model to store POSIX attributes for POSIX groups."""

    group = models.OneToOneField(
        Group,
        verbose_name=_("Related group"),
        related_name="posix_attrs",
        on_delete=models.CASCADE,
    )

    gid = models.IntegerField(
        verbose_name=_("GID Number"), unique=True, validators=[validate_min_value_gid_preferences]
    )

    def clean_gid(self) -> None:
        if not self.gid:
            self.gid = models.Max("gid") + 1

    class Meta:
        verbose_name = _("POSIX Attributes")
