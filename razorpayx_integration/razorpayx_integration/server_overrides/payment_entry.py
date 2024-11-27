# TODO: Validations
# Workflow => Payment Entry => Choose Mode of Payment => Choose Party => Bank Account, Party Bank Account and Credit Account (Account Paid From) is autoset.
# 1. Validation should start from Company Bank account. Check RazorPayX Settings.
# 2. Does Mode of Payment Match? Does Credit Account Match? If not, Validate and Show Message.
# 3. Don't automatically show the Paying via RazorPayX description.
# 4. On submit => Pay => Update Refernce No => Update Remarks

import frappe
