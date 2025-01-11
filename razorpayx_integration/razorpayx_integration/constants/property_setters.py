from razorpayx_integration.payment_utils.constants.custom_fields import (
    BASE_CONDITION_TO_MAKE_ONLINE_PAYMENT,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    USER_PAYOUT_MODE,
)

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

# PE mandatory fields on `make_bank_online_payment`
PE_MANDATORY_FIELDS_FOR_PAYMENT = [
    "bank_account",  # Company Bank Account
]

UPI_MODE_CONDITION = f"eval: doc.make_bank_online_payment && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.UPI.value}'"
BANK_MODE_CONDITION = f"eval: doc.make_bank_online_payment && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.BANK.value}'"
LINK_MODE_CONDITION = f"eval: doc.make_bank_online_payment && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.LINK.value}'"

MANDATORY_BANK_DETAILS_CONDITION = (
    f"eval: doc.party_type && doc.party && doc.online_payment_mode === '{USER_PAYOUT_MODE.BANK.value}'",
)

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
    {
        "doctype": "Payment Entry",
        "fieldname": "online_payment_section",
        "property": "depends_on",
        "property_type": "Data",
        "value": f"eval: {BASE_CONDITION_TO_MAKE_ONLINE_PAYMENT} && doc.razorpayx_account",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "make_bank_online_payment",
        "property": "depends_on",
        "property_type": "Data",
        "value": f"eval: {BASE_CONDITION_TO_MAKE_ONLINE_PAYMENT} && doc.razorpayx_account",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "bank_account",
        "property": "description",
        "property_type": "Data",
        "value": "Reselect the <strong>Company Bank Account</strong> if payment options are not visible.",
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

for field in PE_MANDATORY_FIELDS_FOR_PAYMENT:
    PROPERTY_SETTERS.append(
        {
            "doctype": "Payment Entry",
            "fieldname": field,
            "property": "mandatory_depends_on",
            "property_type": "Data",
            "value": "eval: doc.make_bank_online_payment",
        }
    )
