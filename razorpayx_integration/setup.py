import click

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from razorpayx_integration.hooks import app_title as APP_NAME

#### Setup Constants ####
CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "insert_after": "currency",
        },
    ],
}

STANDARD_FIELDS_TO_HIDE = {
    "Bank Transaction": ["transaction_id"],
    "Employee": ["bank_name", "bank_ac_no", "iban"],
}

PROPERTY_SETTERS = []

for doctype, fields in STANDARD_FIELDS_TO_HIDE.items():
    for field in fields:
        PROPERTY_SETTERS.append(
            {
                "doctype": doctype,
                "fieldname": field,
                "property": "hidden",
                "property_type": "Check",
                "value": 1,
            }
        )


#### Setup Functions ####
def make_custom_fields():
    click.secho(f"Creating Custom Fields for {APP_NAME}...", fg="blue")
    # todo: make more custom fields
    create_custom_fields(CUSTOM_FIELDS)


def make_property_setters():
    click.secho(f"Creating Property Setters for {APP_NAME}...", fg="blue")
    # todo: make more property setters
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


def make_role_and_permissions():
    # todo: make role and permissions
    pass
