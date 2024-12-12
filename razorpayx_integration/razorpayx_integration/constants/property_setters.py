from razorpayx_integration.razorpayx_integration.constants.roles import (
    DEFAULT_PERM_LEVELS as BANK_ACC_PERM_LEVELS,
)

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
        "value": BANK_ACC_PERM_LEVELS.BANK_ACC_MANAGER.value,
    },
    {
        "doctype": "Bank Account",
        "fieldname": "is_default",
        "property": "permlevel",
        "property_type": "Int",
        "value": BANK_ACC_PERM_LEVELS.BANK_ACC_MANAGER.value,
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
