"""
Custom fields which are common for making/handling payments

Note:
    - Keep sequence like this:
        1. fieldname
        2. label
        3. fieldtype
        4. insert_after
        ...
"""

from razorpayx_integration.payment_utils.constants.payments import (
    BANK_METHODS,
    TRANSFER_METHOD,
)
from razorpayx_integration.payment_utils.constants.roles import PERMISSION_LEVEL

UPI_MODE_CONDITION = f"doc.make_bank_online_payment && doc.payment_transfer_method === '{TRANSFER_METHOD.UPI.value}'"
BANK_MODE_CONDITION = f"doc.make_bank_online_payment && {BANK_METHODS}.includes(doc.payment_transfer_method)"

CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "insert_after": "currency",
            "read_only": 1,
            "description": "As per the transaction response",
            "no_copy": 1,
        },
    ],
    "Bank Account": [  # For `UPI` payment mode
        {
            "fieldname": "upi_id",
            "label": "UPI ID",
            "fieldtype": "Data",
            "insert_after": "iban",
            "placeholder": "Eg. 9999999999@okicici",
            "depends_on": "",  # TODO: remove after split
            "no_copy": 1,
        },
    ],
    "Payment Entry": [
        {
            "fieldname": "contact_mobile",
            "label": "Mobile",
            "fieldtype": "Data",
            "insert_after": "party_name",
            "options": "Phone",
            "read_only": 1,
            "depends_on": "",  # TODO: remove after split
            "no_copy": 0,  # TODO: remove after split
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        ### ONLINE PAYMENT SECTION ###
        {
            "fieldname": "online_payment_section",
            "label": "Online Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "contact_email",
            "depends_on": "eval: doc.payment_type=='Pay' && doc.party && doc.party_type && doc.integration_doctype && doc.integration_docname",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "make_bank_online_payment",
            "label": "Make Online Payment",
            "fieldtype": "Check",
            "insert_after": "online_payment_section",
            "description": "Make online payment using <strong>Payment Integrations</strong>",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "payment_transfer_method",
            "label": "Payment Transfer Method",
            "fieldtype": "Select",
            "insert_after": "make_bank_online_payment",
            "options": TRANSFER_METHOD.values_as_string(),
            "default": TRANSFER_METHOD.LINK.value,
            "depends_on": "eval: doc.make_bank_online_payment",
            "mandatory_depends_on": "eval: doc.make_bank_online_payment",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "cb_online_payment_section",
            "fieldtype": "Column Break",
            "insert_after": "payment_transfer_method",
        },
        {
            "fieldname": "party_upi_id",
            "label": "Party UPI ID",
            "fieldtype": "Data",
            "insert_after": "cb_online_payment_section",
            "fetch_from": "party_bank_account.upi_id",
            "read_only": 1,
            "depends_on": f"eval: {UPI_MODE_CONDITION}",
            "mandatory_depends_on": f"eval: {UPI_MODE_CONDITION}",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "party_bank_account_no",
            "label": "Party Bank Account No",
            "fieldtype": "Data",
            "insert_after": "party_upi_id",
            "fetch_from": "party_bank_account.bank_account_no",
            "read_only": 1,
            "depends_on": f"eval: {BANK_MODE_CONDITION}",
            "mandatory_depends_on": f"eval: {BANK_MODE_CONDITION}",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "party_bank_ifsc",
            "label": "Party Bank IFSC Code",
            "fieldtype": "Data",
            "insert_after": "party_bank_account_no",
            "fetch_from": "party_bank_account.branch_code",
            "read_only": 1,
            "depends_on": f"eval: {BANK_MODE_CONDITION}",
            "mandatory_depends_on": f"eval: {BANK_MODE_CONDITION}",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        ### Read Only and Hidden Fields Section ###
        {
            "fieldname": "online_payment_meta_data_section",
            "label": "Online Payment Meta Data",
            "fieldtype": "Section Break",
            "insert_after": "party_bank_ifsc",
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "is_auto_generated",
            "label": "Is Auto Generated",
            "fieldtype": "Check",
            "insert_after": "online_payment_meta_data_section",
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "payment_authorized_by",
            "label": "Payment Authorized By",
            "fieldtype": "Data",
            "insert_after": "is_auto_generated",
            "options": "Email",
            "description": "User who made the payment",
            "hidden": 1,
            "print_hide": 1,
            "no_copy": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "cb_meta_data_section",
            "fieldtype": "Column Break",
            "insert_after": "payment_authorized_by",
        },
        {
            "fieldname": "integration_doctype",
            "label": "Integration DocType",
            "fieldtype": "Data",
            "insert_after": "cb_meta_data_section",
            "print_hide": 1,
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "integration_docname",
            "label": "Integration Docname",
            "fieldtype": "Data",
            "insert_after": "integration_doctype",
            "print_hide": 1,
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
    ],
}
