from razorpayx_integration.payment_utils.constants.roles import ROLE_PROFILES

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

PROPERTY_SETTERS = [
    # BANK ACCOUNT
    {
        "doctype": "Bank Account",
        "fieldname": "disabled",
        "property": "default",
        "property_type": "Data",
        "value": 1,
    },
    {
        "doctype": "Bank Account",
        "fieldname": "disabled",
        "property": "permlevel",
        "property_type": "Int",
        "value": ROLE_PROFILES["Bank Acc Manager"]["permlevel"],
    },
    {
        "doctype": "Bank Account",
        "fieldname": "is_default",
        "property": "permlevel",
        "property_type": "Int",
        "value": ROLE_PROFILES["Bank Acc Manager"]["permlevel"],
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
