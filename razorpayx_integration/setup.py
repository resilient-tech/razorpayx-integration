import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from razorpayx_integration.constants import CUSTOM_FIELDS, PROPERTY_SETTERS
from razorpayx_integration.hooks import app_title as APP_NAME


def make_custom_fields():
    click.secho(f"Creating Custom Fields for {APP_NAME}...", fg="blue")
    # todo: make more custom fields
    create_custom_fields(CUSTOM_FIELDS)

    click.secho("\n Custom fields created successfully!", fg="green")


def make_property_setters():
    click.secho(f"Creating Property Setters for {APP_NAME}...", fg="blue")
    # todo: make more property setters
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)

    click.secho("\n Property setters created successfully!", fg="green")


def make_role_and_permissions():
    # todo: make role and permissions
    pass


def delete_custom_fields():
    click.secho(f"\n Deleting custom fields of {APP_NAME}...", fg="blue")

    for doctype, fields in CUSTOM_FIELDS.items():
        frappe.db.delete(
            "Custom Field",
            {
                "fieldname": ("in", [field["fieldname"] for field in fields]),
                "dt": doctype,
            },
        )

        frappe.clear_cache(doctype=doctype)

    click.secho("\n Custom fields deleted successfully!", fg="green")


def delete_property_setters():
    click.secho(f"Deleting property setters off {APP_NAME}...", fg="blue")

    field_map = {
        "doctype": "doc_type",
        "fieldname": "field_name",
    }

    for property_setter in PROPERTY_SETTERS:
        for key, fieldname in field_map.items():
            if key in property_setter:
                property_setter[fieldname] = property_setter.pop(key)

        frappe.db.delete("Property Setter", property_setter)

    click.secho("\n Property setters deleted successfully!", fg="green")


def delete_role_and_permissions():
    # todo: delete role and permissions
    pass
