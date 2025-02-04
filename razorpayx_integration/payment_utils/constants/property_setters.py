PROPERTY_SETTERS = [
    ### Payment Entry ###
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_date",
        "property": "default",
        "property_type": "Data",
        "value": "Today",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_date",
        "property": "no_copy",
        "property_type": "Check",
        "value": 1,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_no",
        "property": "no_copy",
        "property_type": "Check",
        "value": 1,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_no",
        "property": "default",
        "property_type": "Data",
        "value": "-",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_email",
        "property": "depends_on",
        "property_type": "Data",
        "value": "eval: doc.contact_person || doc.party_type === 'Employee'",
    },
]

# PE mandatory fields on `make_bank_online_payment`
PE_MANDATORY_FIELDS_FOR_PAYMENT = ["bank_account"]

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

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

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


# TODO:? add bank account fields: is_default,disable permission level?? (Helpful in workflow)
