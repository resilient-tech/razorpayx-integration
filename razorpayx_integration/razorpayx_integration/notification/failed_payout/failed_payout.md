<p>Dear {{ frappe.db.get_value("User", {"email": doc.payment_authorized_by},"first_name") }},</p>

<p>The payout has been <span style="color: red">{{ doc.razorpayx_payout_status }}!</span> for Payment Entry {{ doc.name }}.</p>

<p>For more details, visit your ERPNext site and check the details.</p>
