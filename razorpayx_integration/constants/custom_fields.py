from razorpayx_integration.constants.payouts import RAZORPAYX_PAYOUT_MODE

CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "insert_after": "currency",
        },
    ],
    "Bank Account": [
        # For `Link` payment mode
        {
            "fieldname": "party_contact",
            "label": "Party Contact",
            "fieldtype": "Data",
            "insert_after": "party_type",
            "is_virtual": 1,
            "depends_on": "eval: !doc.is_company_account && doc.payment_mode === 'Link'",
            "read_only": 1,
        },
        {
            "fieldname": "party_email",
            "label": "Party Email",
            "fieldtype": "Data",
            "insert_after": "party",
            "is_virtual": 1,
            "depends_on": "eval: !doc.is_company_account && doc.payment_mode === 'Link'",
            "read_only": 1,
        },
        # Payment Mode Section
        {
            "fieldname": "payment_section",
            "label": "RazorpayX Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "party_email",
            "depends_on": "eval: !doc.is_company_account",
        },
        {
            "fieldname": "payment_mode",
            "label": "Payment Mode",
            "fieldtype": "Select",
            "insert_after": "payment_section",
            "options": "\n".join(RAZORPAYX_PAYOUT_MODE.values()),
            "default": RAZORPAYX_PAYOUT_MODE.Bank.value,
        },
        # For `UPI` payment mode
        {
            "fieldname": "upi_id",
            "label": "UPI ID",
            "fieldtype": "Data",
            "insert_after": "iban",
            "depends_on": "eval: !doc.is_company_account && doc.payment_mode === 'UPI'",
            "placeholder": "Eg. 90876543@okicici",
        },
    ],
}
