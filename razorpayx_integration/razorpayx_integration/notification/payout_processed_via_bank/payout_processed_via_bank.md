<p>Payment of <strong>Rs. {{ frappe.utils.fmt_money(doc.paid_amount) }}</strong> has been transferred to your account.</p>

<hr>

<p><strong>URT:</strong> {{ doc.reference_no }}</p>

<p><strong>Description:</strong> {{ doc.razorpayx_payout_desc }}</p>

<p><strong>Bank Account No:</strong> {{ doc.party_bank_account_no }}</p>

<p><strong>Bank IFSC:</strong> {{ doc.party_bank_ifsc }}</p>