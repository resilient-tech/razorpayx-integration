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

from razorpayx_integration.payment_utils.constants.payouts import PAYOUT_MODE
from razorpayx_integration.payment_utils.constants.roles import PERMISSION_LEVEL

# TODO: permission level are left to add
BLOCK_AUTO_PAYMENT = {
    "fieldname": "block_auto_payment",
    "label": "Block Auto Payment",
    "fieldtype": "Check",
    "description": "Automatic payment entries will not be created for this party",
    "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
}


CUSTOM_FIELDS = {
    # NOTE: update bank account custom fields in particular integration if required
    "Bank Account": [
        {
            "fieldname": "online_payment_section",
            "label": "Online Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "party",
            "depends_on": "eval: !doc.is_company_account && doc.party_type && doc.party",
        },
        {
            "fieldname": "online_payment_mode",
            "label": "Online Payment Mode",
            "fieldtype": "Select",
            "insert_after": "online_payment_section",
            "options": PAYOUT_MODE.values_as_string(),
            "default": PAYOUT_MODE.BANK.value,
        },
        {
            "fieldname": "online_payment_cb",
            "fieldtype": "Column Break",
            "insert_after": "online_payment_mode",
        },
        # For `UPI` payment mode
        {
            "fieldname": "upi_id",
            "label": "UPI ID",
            "fieldtype": "Data",
            "insert_after": "iban",
            "placeholder": "Eg. 9999999999@okicici",
            "depends_on": f"eval: doc.online_payment_mode === '{PAYOUT_MODE.UPI.value}'",
            "mandatory_depends_on": f"eval: doc.online_payment_mode === '{PAYOUT_MODE.UPI.value}'",
            "no_copy": 1,
        },
    ],
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
    "Payment Entry": [
        {
            "fieldname": "contact_mobile",
            "label": "Mobile",
            "fieldtype": "Data",
            "insert_after": "party_name",
            "options": "Phone",
            "depends_on": "eval: doc.contact_person",
            "read_only": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "online_payment_section",
            "label": "Online Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "contact_email",
            "depends_on": "eval: doc.payment_type=='Pay' && doc.mode_of_payment!='Cash' && doc.party && doc.party_type && doc.paid_to_account_currency === 'INR'",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "make_bank_online_payment",
            "label": "Make Online Payment",
            "fieldtype": "Check",
            "insert_after": "online_payment_section",
            "description": "Make online payment using <strong>Payments Integration</strong>",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "cb_online_payment_section",
            "fieldtype": "Column Break",
            "insert_after": "make_bank_online_payment",
        },
        {
            "fieldname": "party_upi_id",
            "label": "Party UPI ID",
            "fieldtype": "Data",
            "insert_after": "cb_online_payment_section",
            "fetch_from": "party_bank_account.upi_id",  # Note: update at integration level if required
            "read_only": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "party_bank_account_no",
            "label": "Party Bank Account No",
            "fieldtype": "Data",
            "insert_after": "party_upi_id",
            "fetch_from": "party_bank_account.bank_account_no",  # Note: update at integration level if required
            "read_only": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "party_bank_ifsc",
            "label": "Party Bank IFSC Code",
            "fieldtype": "Data",
            "insert_after": "party_bank_account_no",
            "fetch_from": "party_bank_account.branch_code",  # Note: update at integration level if required
            "read_only": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
    ],
    "Customer": [
        {**BLOCK_AUTO_PAYMENT, "insert_after": "payment_terms"},
    ],
    "Supplier": [
        {**BLOCK_AUTO_PAYMENT, "insert_after": "payment_terms"},
    ],
    "Employee": [
        {**BLOCK_AUTO_PAYMENT, "insert_after": "bank_name"},
    ],
}

# TODO: Add `no copy` for all custom fields which are not required to copy
