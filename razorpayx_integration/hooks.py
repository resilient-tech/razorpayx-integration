app_name = "razorpayx_integration"
app_title = "RazorpayX Integration"
app_publisher = "Resilient Tech"
app_description = "Automat Payments By RazorpayX API For Frappe Apps"
app_email = "info@resilient.tech"
app_license = "GNU General Public License (v3)"
required_apps = ["frappe/erpnext", "resilient-tech/payment_integration_utils"]

after_install = "razorpayx_integration.install.after_install"
before_uninstall = "razorpayx_integration.uninstall.before_uninstall"

after_app_install = "razorpayx_integration.install.after_app_install"
before_app_uninstall = "razorpayx_integration.uninstall.before_app_uninstall"

app_include_js = "razorpayx_integration.bundle.js"

export_python_type_annotations = True

doctype_js = {
    "Payment Entry": "razorpayx_integration/client_overrides/form/payment_entry.js",
    "Bank Reconciliation Tool": "razorpayx_integration/client_overrides/form/bank_reconciliation_tool.js",
}


doc_events = {
    "Payment Entry": {
        "onload": "razorpayx_integration.razorpayx_integration.server_overrides.doctype.payment_entry.onload",
        "validate": "razorpayx_integration.razorpayx_integration.server_overrides.doctype.payment_entry.validate",
        "before_submit": "razorpayx_integration.razorpayx_integration.server_overrides.doctype.payment_entry.before_submit",
        "on_submit": "razorpayx_integration.razorpayx_integration.server_overrides.doctype.payment_entry.on_submit",
        "before_cancel": "razorpayx_integration.razorpayx_integration.server_overrides.doctype.payment_entry.before_cancel",
    },
}

scheduler_events = {
    "daily": [
        "razorpayx_integration.razorpayx_integration.utils.bank_transaction.sync_transactions_periodically"
    ]
}

payment_integration_fields = [
    "razorpayx_payout_desc",
    "razorpayx_payout_status",
    "razorpayx_payout_id",
    "razorpayx_payout_link_id",
]
