from aleksis.core.util.core_helpers import celery_optional

from .util.ldap_sync import mass_ldap_import


@celery_optional
def ldap_import():
    mass_ldap_import()
