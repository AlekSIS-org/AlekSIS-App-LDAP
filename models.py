from django.db import models
from django.utils.translation import gettext_lazy as _

from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Group, Person
from aleksis.core.util.core_helpers import get_site_preferences


def get_default_value_shell_preferences():
    return get_site_preferences()["posix__shell"]


def get_default_value_gid_preferences():
    return get_site_preferences()["posix__gid_number"]


def validate_min_value_uid_number_preferences(value):
    if value < get_site_preferences()["posix__min_uid_number"]:
        raise ValidationError(_("Value smaller than minimum uid number!"))


def get_next_free_uid_number():
    return PersonPosixAttrs.objects.order_by("-uid_number")[0].uid_number + 1


def validate_uid_number(value):
    if PersonPosixAttrs.objects.get(uid_number=value).exists():
        raise ValidationError(_("Account with this UID number already exists!"))


def validate_free_username(value):
        disallowed_uids = get_site_preferences()["posix__disallowed_uids"].split(",")
        if value in disallowed_uids:
            raise ValidationError(_("Username not allowed"))


class SSHKey(ExtensibleModel):
    """Model to store SSH keys uploaded by persons."""

    name = models.CharField(
        verbose_name=_("Name of this Key"), max_length=255, default=_("SSH Public key")
    )
    public_key = models.TextField(verbose_name=_("SSH public key"))
    person = models.ForeignKey(
        Person,
        verbose_name=_("Person"),
        on_delete=models.CASCADE,
        related_name="ssh_keys",
    )

    def __str__(self) -> str:
        return self.name

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

    uid_number = models.PositiveIntegerField(
        verbose_name=_("UID Number"),
        validators=[validate_min_value_uid_number_preferences],
    )
    home_directory = models.CharField(verbose_name=_("Home directory"))
    login_shell = models.CharField(
        verbose_name=_("Login shell"), default=get_default_value_shell_preferences
    )
    gid_number = models.PositiveIntegerField(
        verbose_name=_("Primary GID Number"),
        default=get_default_value_gid_preferences,
    )
    uid = models.CharField(
        verbose_name=_("UID"),
        unique=True,
        default=get_next_free_uid_number,
        validators=[
            RegexValidator(regex=get_site_preferences()["posix__uid_regex"]),
            RegexValidator(regex=r"^[A-Za-z0-9_.][A-Za-z0-9_.-]*$"),
            validate_uid_number,
            validate_free_username,
        ],
    )

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

    gidNumber = models.IntegerField(verbose_name=_("GID Number"))

    class Meta:
        verbose_name = _("POSIX Attributes")
