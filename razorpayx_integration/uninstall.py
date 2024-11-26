from razorpayx_integration.setup import (
    delete_custom_fields,
    delete_property_setters,
    delete_role_and_permissions,
)


def before_uninstall():
    delete_custom_fields()
    delete_property_setters()
    delete_role_and_permissions()
