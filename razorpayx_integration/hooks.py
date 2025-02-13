app_name = "razorpayx_integration"
app_title = "RazorpayX Integration"
app_publisher = "Resilient Tech"
app_description = "Automat Payments By RazorpayX API For Frappe Apps"
app_email = "info@resilient.tech"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

after_install = "razorpayx_integration.install.after_install"
before_uninstall = "razorpayx_integration.uninstall.before_uninstall"

app_include_js = "razorpayx_integration.bundle.js"

export_python_type_annotations = True

doctype_js = {
    "Payment Entry": [
        "payment_utils/client_overrides/payment_entry.js",
        "razorpayx_integration/client_overrides/form/payment_entry.js",
    ],
    "Bank Account": "payment_utils/client_overrides/bank_account.js",
    "Bank Reconciliation Tool": "razorpayx_integration/client_overrides/form/bank_reconciliation_tool.js",
    "User": "payment_utils/client_overrides/user.js",
}

doctype_list_js = {
    "Payment Entry": "razorpayx_integration/client_overrides/list/payment_entry_list.js",
}

doc_events = {
    "Payment Entry": {
        "onload": [
            "razorpayx_integration.payment_utils.server_overrides.payment_entry.onload",
            "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.onload",
        ],
        "validate": [
            "razorpayx_integration.payment_utils.server_overrides.payment_entry.validate",
            "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.validate",
        ],
        "before_submit": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.before_submit",
        "on_submit": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.on_submit",
        "before_cancel": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.before_cancel",
    },
    "Bank Account": {
        "validate": "razorpayx_integration.payment_utils.server_overrides.bank_account.validate",
    },
}

scheduler_events = {
    "daily": [
        "razorpayx_integration.razorpayx_integration.utils.transaction.sync_transactions_periodically"
    ]
}

before_payment_authentication = (
    "razorpayx_integration.payment_utils.utils.permission.has_payout_permissions"
)
