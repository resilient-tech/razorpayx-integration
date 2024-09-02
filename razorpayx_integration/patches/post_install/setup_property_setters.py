import frappe

PROPERTY_SETTERS = [
    {
        "doctype_or_docfield": "DocField",
        "doctype": "Bank Transaction",
        "fieldname": "transaction_id",
        "property": "hidden",
        "value": 1,
        "property_type": "Check",
    },
    {
        "doctype_or_docfield": "DocField",
        "doctype": "Bank Transaction",
        "fieldname": "transaction_id",
        "property": "print_hide",
        "value": 1,
        "property_type": "Check",
    },
]


def execute():
    for property_setter in PROPERTY_SETTERS:
        frappe.make_property_setter(property_setter, validate_fields_for_doctype=False)
