"""
Custom fields which are helpful for payments via RazorPayX

Note:
    - Keep sequence like this:
        1. fieldname
        2. label
        3. fieldtype
        4. insert_after
        ...
"""

from razorpayx_integration.constants import RAZORPAYX_SETTING
from razorpayx_integration.payment_utils.constants.custom_fields import (
    BASE_CONDITION_TO_MAKE_ONLINE_PAYMENT,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYMENT_MODE_LIMIT,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)
from razorpayx_integration.razorpayx_integration.constants.roles import PERMISSION_LEVEL

CUSTOM_FIELDS = {
    "Payment Entry": [
        #### PAYOUT SECTION START ####
        {
            "fieldname": "razorpayx_payout_section",
            "label": "RazorPayX Payout Details",
            "fieldtype": "Section Break",
            "insert_after": "party_bank_ifsc",  ## Insert After `PARTY BANK IFSC` field (Payment Utils Custom Field)
            "depends_on": f"eval: {BASE_CONDITION_TO_MAKE_ONLINE_PAYMENT} && doc.make_bank_online_payment && doc.paid_from_account_currency === 'INR' && doc.integration_doctype === '{RAZORPAYX_SETTING}'",
            "collapsible": 1,
            "collapsible_depends_on": "eval: doc.docstatus === 0",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_payout_mode",
            "label": "RazorPayX Payout Mode",
            "fieldtype": "Select",
            "insert_after": "razorpayx_setting",
            "fetch_from": "party_bank_account.online_payment_mode",
            "options": USER_PAYOUT_MODE.values_as_string(),
            "default": USER_PAYOUT_MODE.LINK.value,
            "read_only": 1,
            "depends_on": "eval: doc.make_bank_online_payment",
            "mandatory_depends_on": "eval: doc.make_bank_online_payment",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_pay_instantaneously",
            "label": "Pay Instantaneously",
            "fieldtype": "Check",
            "insert_after": "razorpayx_payout_mode",
            "depends_on": f"eval: doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.BANK.value}' && doc.paid_amount <= {PAYMENT_MODE_LIMIT.IMPS.value}",
            "description": "Payment will be done with <strong>IMPS</strong> mode.",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_payout_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_pay_instantaneously",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_payout_desc",
            "label": "Payout Description",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_cb",
            "depends_on": "eval: doc.make_bank_online_payment",
            "mandatory_depends_on": f"eval:doc.make_bank_online_payment && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.LINK.value}'",
            "length": 30,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_payout_status",
            "label": "RazorPayX Payout Status",
            "fieldtype": "Select",
            "insert_after": "razorpayx_payout_desc",
            "options": PAYOUT_STATUS.title_case_values(as_string=True),
            "default": PAYOUT_STATUS.NOT_INITIATED.value.title(),
            "depends_on": "eval: doc.make_bank_online_payment && doc.creation",
            "read_only": 1,
            "allow_on_submit": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_id_sec",
            "label": "RazorPayX Payout ID Section",
            "fieldtype": "Section Break",
            "insert_after": "razorpayx_payout_status",
            "hidden": 1,
        },
        {
            "fieldname": "razorpayx_payout_id",
            "label": "RazorPayX Payout ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_id_sec",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_id_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_payout_id",
        },
        {
            "fieldname": "razorpayx_payout_link_id",
            "label": "RazorPayX Payout Link ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_id_cb",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        #### PAYMENT SECTION END ####
    ],
}
