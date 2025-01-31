from razorpayx_integration.constants import RAZORPAYX_SETTING
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    USER_PAYOUT_MODE,
)

UPI_MODE_CONDITION = f"eval: doc.make_bank_online_payment  && doc.integration_doctype === '{RAZORPAYX_SETTING}' && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.UPI.value}'"
BANK_MODE_CONDITION = f"eval: doc.make_bank_online_payment && doc.integration_doctype === '{RAZORPAYX_SETTING}' && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.BANK.value}'"
LINK_MODE_CONDITION = f"eval: doc.make_bank_online_payment && doc.integration_doctype === '{RAZORPAYX_SETTING}' && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.LINK.value}'"

MANDATORY_BANK_DETAILS_CONDITION = f"eval: doc.party_type && doc.party && doc.online_payment_mode === '{USER_PAYOUT_MODE.BANK.value}'"

PROPERTY_SETTERS = [
    ## Payment Entry ##
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": LINK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": UPI_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "depends_on",
        "property_type": "Data",
        "value": UPI_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    ## Bank Account ##
    {
        "doctype": "Bank Account",
        "fieldname": "online_payment_mode",
        "property": "options",
        "property_type": "Data",
        "value": USER_PAYOUT_MODE.values_as_string(),
    },
    {
        "doctype": "Bank Account",
        "fieldname": "online_payment_mode",
        "property": "description",
        "property_type": "Data",
        "value": f"In <strong>{USER_PAYOUT_MODE.LINK.value}</strong> mode, Payment link will be sent to the party's contact details.",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "online_payment_mode",
        "property": "depends_on",
        "property_type": "Data",
        "value": "eval: !doc.is_company_account && doc.party_type && doc.party",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "bank_account_no",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": MANDATORY_BANK_DETAILS_CONDITION,
    },
    {
        "doctype": "Bank Account",
        "fieldname": "branch_code",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": MANDATORY_BANK_DETAILS_CONDITION,
    },
]
