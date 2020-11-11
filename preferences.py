from django.conf import settings
from django.forms import EmailField, ImageField, URLField
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.types import (
    StringPreference,
    IntegerPreference,
)

from .models import Person
from .registries import person_preferences_registry, site_preferences_registry
from .util.notifications import get_notification_choices_lazy

posix = Section("posix", verbose_name=_("POSIX"))


@site_preferences_registry.register
class DefaultShell(StringPreference):
    section = posix
    name = "shell"
    default = "/bin/bash"
    required = False
    verbose_name = _("Default login shell")


@site_preferences_registry.register
class DefaultPrimaryGid(IntegerPreference):
    section = posix
    name = "gid"
    default = 100
    required = False
    verbose_name = _("Default primary GID number")


@site_preferences_registry.register
class MinGidNumber(IntegerPreference):
    section = posix
    name = "min_gid"
    default = 1000
    required = False
    verbose_name = _("Minimal GID number")


@site_preferences_registry.register
class MinUidNumber(IntegerPreference):
    section = posix
    name = "min_uid"
    default = 1000
    required = False
    verbose_name = _("Minimum UID number")


@site_preferences_registry.register
class UIDRegex(StringPreference):
    section = posix
    name = "uid_regex"
    default = "^[A-Za-z0-9_.][A-Za-z0-9_.-]*$"
    required = False
    verbose_name = _("Regex match for usernames")


@site_preferences_registry.register
class DisallowedUids(LongStringPreference):
    section = posix
    name = "disallowed_uids"
    default = "bin,daemon,Debian-exim,freerad,games,gnats,irc,list,lp,mail,man,messagebus,news,nslcd,ntp,openldap,postfix,postgres,proxy,root,sshd,sssd,statd,sync,sys,systemd-bus-proxy,systemd-network,systemd-resolve,systemd-timesync,uucp,www-data,webmaster, hostmaster, postmaster"
    required = False
    verbose_name = _("Comma-seperated list of disallowed usernames")
