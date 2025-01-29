<p>Payment of <strong>Rs. {{ frappe.utils.fmt_money(doc.paid_amount) }}</strong> has been transferred to your Bank Account.</p>

<hr>

<p><strong>URT:</strong> {{ doc.reference_no }}</p>

<p><strong>Description:</strong> {{ doc.razorpayx_payout_desc }}</p>

<hr>

<p>This payment done after you provided your payment details to <strong>RazorPayX Link</strong></p>
