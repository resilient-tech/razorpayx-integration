import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import (
    add_permission,
)
from frappe.permissions import (
    setup_custom_perms as update_custom_perms,
)
from frappe.permissions import (
    update_permission_property as update_permission,
)

from razorpayx_integration.constants import (
    CUSTOM_FIELDS,
    CUSTOM_PERMISSIONS,
    PROPERTY_SETTERS,
    ROLES,
)
from razorpayx_integration.hooks import app_title as APP_NAME


def make_custom_fields():
    click.secho(f"\nCreating Custom Fields for {APP_NAME}...", fg="blue")
    # todo: make more custom fields
    create_custom_fields(CUSTOM_FIELDS)


def make_property_setters():
    click.secho(f"\nCreating Property Setters for {APP_NAME}...", fg="blue")
    # todo: make more property setters
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


def make_role_and_permissions():
    # todo: make role and permissions
    click.secho(f"\nCreating Role and Permissions for {APP_NAME}...", fg="blue")

    # creating a roles
    for role in ROLES:
        try:
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role["role_name"],
                    "desk_access": 1,
                },
            ).save()

        except frappe.DuplicateEntryError:
            pass

    # setting up custom permissions
    setup_custom_permissions()

    # setting up roles and permissions
    update_roles_and_permissions()


def setup_custom_permissions():
    for custom_permission in CUSTOM_PERMISSIONS:
        frappe.reload_doc(
            module=custom_permission["module"],
            dt=custom_permission["dt"],
            dn=custom_permission["dn"],
        )

        update_custom_perms(custom_permission["doctype"])


def update_roles_and_permissions():
    for role in ROLES:
        doctypes, role_name, permlevel, permissions = role.values()

        for doctype in doctypes:
            add_permission(doctype, role_name, permlevel)

            for permission in permissions:
                update_permission(doctype, role_name, permlevel, permission, 1)


def delete_custom_fields():
    click.secho(f"\nDeleting custom fields of {APP_NAME}...", fg="blue")

    for doctype, fields in CUSTOM_FIELDS.items():
        frappe.db.delete(
            "Custom Field",
            {
                "fieldname": ("in", [field["fieldname"] for field in fields]),
                "dt": doctype,
            },
        )

        frappe.clear_cache(doctype=doctype)


def delete_property_setters():
    click.secho(f"\nDeleting property setters off {APP_NAME}...", fg="blue")

    field_map = {
        "doctype": "doc_type",
        "fieldname": "field_name",
    }

    for property_setter in PROPERTY_SETTERS:
        for key, fieldname in field_map.items():
            if key in property_setter:
                property_setter[fieldname] = property_setter.pop(key)

        frappe.db.delete("Property Setter", property_setter)


def delete_role_and_permissions():
    # todo: delete role and permissions
    pass
