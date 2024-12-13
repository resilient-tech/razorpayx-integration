from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_MODE,
)

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

# PE mandatory fields on `make_online_payment`
PE_MANDATORY_FIELDS_ON_RAZORPAYX = [
    "party_type",
    "party",
    "bank_account",
    "party_bank_account",
]

PROPERTY_SETTERS = [
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": f"eval: doc.make_online_payment && doc.razorpayx_payment_mode === '{RAZORPAYX_PAYOUT_MODE.LINK.value}'",
    }
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

for field in PE_MANDATORY_FIELDS_ON_RAZORPAYX:
    PROPERTY_SETTERS.append(
        {
            "doctype": "Payment Entry",
            "fieldname": field,
            "property": "mandatory_depends_on",
            "property_type": "Data",
            "value": "eval: doc.make_online_payment",
        }
    )
