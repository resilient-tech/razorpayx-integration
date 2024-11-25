import click

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import (
    add_permission,
    setup_custom_perms,
    update_permission_property,
)

from razorpayx_integration.constants import BUG_REPORT_URL, RAZORPAYX_SETTING_DOCTYPE

INTEGRATION_MANAGER_PERMISSION_LEVEL = 7


CUSTOM_BANK_SECTION = {
    "fieldname": "bank_details_section",
    "label": "Bank Details",
    "fieldtype": "Section Break",
    "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
}

CUSTOM_PARTY_FIELDS = [
    {
        "fieldname": "bank_account",
        "label": "Bank Account",
        "fieldtype": "Link",
        "options": "Bank Account",
        "insert_after": "bank_details_section",
        "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
    },
]

CUSTOM_FIELDS = {
    "Employee": CUSTOM_PARTY_FIELDS,
    "Supplier": [
        {
            **CUSTOM_BANK_SECTION,
            "insert_after": "accounts",
        }
    ]
    + CUSTOM_PARTY_FIELDS,
    "Customer": [
        {
            **CUSTOM_BANK_SECTION,
            "insert_after": "payment_terms",
        },
        {
            "fieldname": "end_bank_section",
            "fieldtype": "Section Break",
            "insert_after": "bank_account",
        },
    ]
    + CUSTOM_PARTY_FIELDS,
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "insert_after": "currency",
        },
    ],
    "Payment Entry": [
        {
            "fieldname": "razorpayx_payment_section",
            "label": "RazorpayX Payment",
            "fieldtype": "Section Break",
            "depends_on": "eval:(doc.payment_type=='Pay' && doc.mode_of_payment!='Cash' && doc.paid_from && doc.party)",
            "insert_after": "contact_email",
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "pay_now",
            "label": "Make Payment Now",
            "fieldtype": "Check",
            "depends_on": "eval:(doc.payment_type=='Pay' && doc.mode_of_payment!='Cash' && doc.paid_from && doc.party)",
            "insert_after": "razorpayx_payment_section",
            "print_hide": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "party_bank_acc",
            "label": "Party's Bank Account",
            "fieldtype": "Link",
            "options": "Bank Account",
            "depends_on": "eval:doc.pay_now",
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "pay_now",
            "print_hide": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "party_bank_ac_no",
            "label": "Party's Bank Account No",
            "fieldtype": "Data",
            "depends_on": "eval:doc.pay_now",
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "party_bank_acc",
            "read_only": 1,
            "print_hide": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "payment_desc",
            "label": "Payment Description",
            "fieldtype": "Data",
            "depends_on": "eval:doc.pay_now",
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "party_bank_ac_no",
            "print_hide": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "bank_payment_cb",
            "fieldtype": "Column Break",
            "insert_after": "payment_desc",
        },
        {
            "fieldname": "pay_on_submit",
            "label": "Make Payment On Submit",
            "fieldtype": "Check",
            "depends_on": "eval:doc.pay_now",
            "insert_after": "bank_payment_cb",
            "print_hide": 1,
            "read_only": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "razorpayx_account",
            "label": "RazorpayX Integration Account",
            "fieldtype": "Link",
            "options": RAZORPAYX_SETTING_DOCTYPE,
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "pay_on_submit",
            "print_hide": 1,
            "read_only": 1,
            "hidden": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "razorpayx_payment_status",
            "label": "Payment Status",
            "fieldtype": "Select",
            "options": "Not Initiated\nProcessing\nProcessed\nCancelled\nReversed\nFailed",
            "default": "Not Initiated",
            "depends_on": "eval:(doc.pay_now && doc.creation)",
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "razorpayx_account",
            "print_hide": 1,
            "read_only": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "party_bank",
            "label": "Party's Bank",
            "fieldtype": "Link",
            "options": "Bank",
            "depends_on": "eval:doc.pay_now",
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "razorpayx_payment_status",
            "print_hide": 1,
            "read_only": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "party_bank_branch_code",
            "label": "Party's Bank Branch Code",
            "fieldtype": "Data",
            "depends_on": "eval:doc.pay_now",
            "mandatory_depends_on": "eval:doc.pay_now",
            "insert_after": "party_bank",
            "read_only": 1,
            "print_hide": 1,
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
        {
            "fieldname": "payment_mode",
            "label": "Payment Mode",
            "fieldtype": "Select",
            "options": "\nNEFT\nRTGS",
            "depends_on": "eval:doc.pay_now",
            "insert_after": "party_bank_branch_code",
            "print_hide": 1,
            "mandatory_depends_on": "eval:doc.pay_now",
            "permlevel": INTEGRATION_MANAGER_PERMISSION_LEVEL,
        },
    ],
}


COMMON_CHECK_PROPERTY_SETTINGS = {
    "value": 1,
    "property_type": "Check",
}

STANDARD_FIELDS_TO_HIDE = {
    "Bank Transaction": ["transaction_id"],
    "Employee": ["bank_name", "bank_ac_no", "iban"],
}

PROPERTY_SETTERS = [
    {
        "doctype": "Bank Transaction",
        "fieldname": "transaction_id",
        "property": "hidden",
        **COMMON_CHECK_PROPERTY_SETTINGS,
    },
    {
        "doctype": "Bank Transaction",
        "fieldname": "transaction_id",
        "property": "print_hide",
        **COMMON_CHECK_PROPERTY_SETTINGS,
    },
]

for doctype, fields in STANDARD_FIELDS_TO_HIDE.items():
    for field in fields:
        PROPERTY_SETTERS.append(
            {
                "doctype": doctype,
                "fieldname": field,
                "property": "hidden",
                **COMMON_CHECK_PROPERTY_SETTINGS,
            }
        )


def after_install():
    try:
        click.secho("Patching...", fg="blue")
        make_custom_fields()
        make_property_setters()
        make_role_and_permissions()

    except Exception as e:
        click.secho(
            (
                "Installation for RazorPayX Integration failed due to an error."
                "Please try re-installing the app or "
                f"report the issue on {BUG_REPORT_URL} if not resolved."
            ),
            fg="bright_red",
        )
        raise e

    click.secho("Thank you for installing RazorPayX Integration!", fg="green")


def make_custom_fields():
    create_custom_fields(CUSTOM_FIELDS)


def make_property_setters():
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter)


def make_role_and_permissions():
    role_name = "RazorPayX Integration Manager"

    try:
        role = frappe.new_doc("Role")
        role.update(
            {
                "role_name": role_name,
                "desk_access": 1,
            }
        )
        role.save()
    except frappe.DuplicateEntryError:
        pass

    frappe.reload_doc(
        "razorpayx_integration", "doctype", "razorpayx_integration_setting"
    )
    setup_custom_perms(RAZORPAYX_SETTING_DOCTYPE)

    for doctype in ("Employee", "Customer", "Supplier", "Payment Entry"):
        add_permission(doctype, role_name, INTEGRATION_MANAGER_PERMISSION_LEVEL)
        update_permission_property(
            doctype, role_name, INTEGRATION_MANAGER_PERMISSION_LEVEL, "write", 1
        )
