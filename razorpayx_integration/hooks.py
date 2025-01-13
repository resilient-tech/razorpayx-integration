app_name = "razorpayx_integration"
app_title = "RazorPayX Integration"
app_publisher = "Resilient Tech"
app_description = "Automat Payments By RazorPayX API For Frappe Apps"
app_email = "info@resilient.tech"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

after_install = "razorpayx_integration.install.after_install"
before_uninstall = "razorpayx_integration.uninstall.before_uninstall"

app_include_js = "razorpayx_integration.bundle.js"

export_python_type_annotations = True

doctype_js = {
    "Payment Entry": "razorpayx_integration/client_overrides/payment_entry.js",
}

doc_events = {
    "Bank Account": {
        "validate": "razorpayx_integration.payment_utils.server_overrides.bank_account.validate"
    },
    "Payment Entry": {
        "onload": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.onload",
        "validate": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.validate",
        "before_submit": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.before_submit",
        "on_submit": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.on_submit",
        "before_cancel": "razorpayx_integration.razorpayx_integration.server_overrides.payment_entry.before_cancel",
    },
}
