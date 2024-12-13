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

from razorpayx_integration.payment_utils.constants import INTEGRATION_DOCTYPE
from razorpayx_integration.payment_utils.constants.roles import (
    DEFAULT_PERM_LEVELS as PERM_LEVELS,
)

# TODO: permission level are left to add
BLOCK_AUTO_PAYMENT = {
    "fieldname": "block_auto_payment",
    "label": "Block Auto Payment",
    "fieldtype": "Check",
    "description": "Auto payment will be blocked for this party",
}


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
    "Payment Entry": [
        {
            "fieldname": "online_payment_section",
            "label": "Online Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "contact_email",
            "depends_on": "eval: doc.payment_type=='Pay' && doc.mode_of_payment!='Cash'",
            "permlevel": PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "make_online_payment",
            "label": "Make Online Payment",
            "fieldtype": "Check",
            "insert_after": "online_payment_section",
            "description": "Make online payment using <strong>Payments Integration</strong>",
            "permlevel": PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "online_payment_cb",
            "fieldtype": "Column Break",
            "insert_after": "make_online_payment",
            "permlevel": PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "bank_payment_integration",
            "label": "Bank Payment Integration",
            "fieldtype": "Link",
            "insert_after": "online_payment_cb",
            "options": INTEGRATION_DOCTYPE,
            "depends_on": "eval: doc.make_online_payment",
            "mandatory_depends_on": "eval: doc.make_online_payment",
            "permlevel": PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        },
    ],
}
