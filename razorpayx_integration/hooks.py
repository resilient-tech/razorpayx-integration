app_name = "razorpayx_integration"
app_title = "RazorpayX Integration"
app_publisher = "Resilient Tech"
app_description = "Automat Payments By RazorPayX API For Frappe Apps"
app_email = "info@resilient.tech"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

after_install = "razorpayx_integration.install.after_install"
before_uninstall = "razorpayx_integration.uninstall.before_uninstall"

app_include_js = "razorpayx_integration.bundle.js"

scheduler_events = {
    "daily": ["razorpayx_integration.scheduler_events.fetch_daily_transactions.execute"]
}

doctype_js = {
    "Payment Entry": "razorpayx_integration/client_overrides/payment_entry.js",
}
