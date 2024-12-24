from razorpayx_integration.razorpayx_integration.constants.payouts import (
    USER_PAYOUT_MODE,
)

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

# PE mandatory fields on `make_online_payment`
PE_MANDATORY_FIELDS_FOR_PAYMENT = [
    "bank_account",  # Company Bank Account
    "party_bank_account",
]

UPI_ID_CONDITION = f"eval: doc.make_online_payment && doc.razorpayx_account && doc.razorpayx_payment_mode === '{USER_PAYOUT_MODE.UPI.value}'"
BANK_ACCOUNT_CONDITION = f"eval: doc.make_online_payment && doc.razorpayx_account && doc.razorpayx_payment_mode === '{USER_PAYOUT_MODE.BANK.value}'"

PROPERTY_SETTERS = [
    ## Payment Entry ##
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": f"eval: doc.make_online_payment && doc.razorpayx_account && doc.razorpayx_payment_mode === '{USER_PAYOUT_MODE.LINK.value}'",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "fetch_from",
        "property_type": "Data",
        "value": "party_bank_account.contact_to_pay",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "fetch_if_empty",
        "property_type": "Check",
        "value": 1,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": UPI_ID_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "depends_on",
        "property_type": "Data",
        "value": UPI_ID_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_ACCOUNT_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "depends_on",
        "property_type": "Data",
        "value": BANK_ACCOUNT_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_ACCOUNT_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "depends_on",
        "property_type": "Data",
        "value": BANK_ACCOUNT_CONDITION,
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
        "property": "default",
        "property_type": "Data",
        "value": USER_PAYOUT_MODE.BANK.value,
    },
    {
        "doctype": "Bank Account",
        "fieldname": "upi_id",
        "property": "depends_on",
        "property_type": "Data",
        "value": f"eval: doc.online_payment_mode === '{USER_PAYOUT_MODE.UPI.value}'",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "contact_to_pay",
        "property": "depends_on",
        "property_type": "Data",
        "value": f"eval: doc.online_payment_mode === '{USER_PAYOUT_MODE.LINK.value}'",
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
            "value": "eval: doc.make_online_payment",
        }
    )
