"""
Custom fields which are helpful for payments via RazorpayX

Note:
    - Keep sequence like this:
        1. fieldname
        2. label
        3. fieldtype
        4. insert_after
        ...
"""

from razorpayx_integration.constants import RAZORPAYX_SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.roles import (
    DEFAULT_PERM_LEVELS as PAYMENT_PERM_LEVELS,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_MODE,
    RAZORPAYX_PAYOUT_STATUS,
)

CUSTOM_FIELDS = {
    "Bank Account": [
        {
            "fieldname": "razorpayx_payment_section",
            "label": "RazorpayX Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "bank_account_no",
            "depends_on": "eval: !doc.is_company_account && doc.party_type && doc.party",
        },
        {
            "fieldname": "razorpayx_payment_mode",
            "label": "RazorpayX Payment Mode",
            "fieldtype": "Select",
            "insert_after": "razorpayx_payment_section",
            "options": RAZORPAYX_PAYOUT_MODE.values_as_string(),
            "default": RAZORPAYX_PAYOUT_MODE.BANK.value,
        },
        {
            "fieldname": "payment_id_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_payment_mode",
        },
        # For `UPI` payment mode
        {
            "fieldname": "upi_id",
            "label": "UPI ID",
            "fieldtype": "Data",
            "insert_after": "payment_id_cb",
            "placeholder": "Eg. 90876543@okicici",
            "depends_on": f"eval: doc.razorpayx_payment_mode === '{RAZORPAYX_PAYOUT_MODE.UPI.value}'",
        },
        # For `Link` payment mode
        {
            "fieldname": "contact_to_pay",
            "label": "Contact to Pay",
            "fieldtype": "Link",
            "insert_after": "upi_id",
            "options": "Contact",
            "depends_on": f"eval: doc.razorpayx_payment_mode === '{RAZORPAYX_PAYOUT_MODE.LINK.value}'",
            "description": "Contact to whom the payment link will be sent.",
        },
    ],
    "Payment Entry": [
        {
            "fieldname": "contact_mobile",
            "label": "Contact Mobile",
            "fieldtype": "Data",
            "insert_after": "contact_email",
            "options": "Phone",
            "depends_on": "eval: doc.contact_person",
            "read_only": 1,
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payment_section",
            "label": "RazorpayX Payment",
            "fieldtype": "Section Break",
            "insert_after": "contact_mobile",
            "depends_on": "eval: doc.make_online_payment",
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_account",
            "label": "RazorpayX Integration Account",
            "fieldtype": "Link",
            "insert_after": "razorpayx_payment_section",
            "options": RAZORPAYX_SETTING_DOCTYPE,
            "print_hide": 1,
            "read_only": 1,
            "hidden": 1,
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payment_mode",
            "label": "RazorpayX Payment Mode",
            "fieldtype": "Data",
            "insert_after": "razorpayx_account",
            "fetch_from": "party_bank_account.razorpayx_payment_mode",
            "depends_on": "eval: doc.razorpayx_account && doc.party_bank_account",
            "mandatory_depends_on": "eval:doc.razorpayx_account && doc.party_bank_account",
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "pay_instantaneous",
            "label": "Pay Instantaneously",
            "fieldtype": "Check",
            "insert_after": "razorpayx_payment_mode",
            "fetch_from": "party_bank_account.razorpayx_payment_mode",
            "depends_on": f"eval: doc.razorpayx_account && doc.razorpayx_payment_mode === '{RAZORPAYX_PAYOUT_MODE.BANK.value}'",
            "description": "Payment will be done with <strong>IMPS</strong> mode.",
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payment_cb",
            "fieldtype": "Column Break",
            "insert_after": "pay_instantaneous",
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "payment_desc",
            "label": "Payment Description",
            "fieldtype": "Small Text",
            "insert_after": "razorpayx_payment_cb",
            "depends_on": "eval: doc.razorpayx_account",
            "mandatory_depends_on": "eval: doc.razorpayx_account",
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payment_status",
            "label": "Payment Status",
            "fieldtype": "Select",
            "insert_after": "payment_desc",
            "options": RAZORPAYX_PAYOUT_STATUS.values_as_string(),
            "default": RAZORPAYX_PAYOUT_STATUS.NOT_INITIATED.value,
            "depends_on": "eval: doc.razorpayx_account && doc.creation",
            "read_only": 1,
            "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
    ],
}
