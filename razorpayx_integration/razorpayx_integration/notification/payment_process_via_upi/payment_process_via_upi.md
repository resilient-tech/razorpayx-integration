<p>Payment of <strong>Rs. {{ frappe.utils.fmt_money(doc.paid_amount) }}</strong> has been transferred to your UPI ID.</p>

<hr>

<p><strong>URT:</strong> {{ doc.reference_no }}</p>

<p><strong>Description:</strong> {{ doc.razorpayx_payout_desc }}</p>

<p><strong>UPI ID:</strong> {{ doc.party_upi_id }}</p>
