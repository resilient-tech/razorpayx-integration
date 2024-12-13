from razorpayx_integration.razorpayx_integration.constants.roles import (
    DEFAULT_PERM_LEVELS as BANK_ACC_PERM_LEVELS,
)

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

PROPERTY_SETTERS = []

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
