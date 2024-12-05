STANDARD_FIELDS_TO_HIDE = {
    "Employee": ["bank_name", "bank_ac_no", "iban"],  # ? Correct
}

# TODO: Do not allow Bank Account user to edit the disabled and is_default fields
# TODO: Permissions (permlevel)
PROPERTY_SETTERS = [
    {
        "doctype": "Bank Account",
        "fieldname": "disabled",
        "property": "default",
        "property_type": "Data",
        "value": 1,
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
