<p>Payment of <strong>Rs. {{ frappe.utils.fmt_money(doc.paid_amount) }}</strong> has been transferred via RazorPayX</p>

<hr>

<p><strong>URT:</strong> {{ doc.reference_no }}</p>

{% if doc.razorpayx_payout_desc %}
<p><strong>Description:</strong> {{ doc.razorpayx_payout_desc }}</p>
{% endif %}

{% if doc.razorpayx_payout_mode == "NEFT/RTGS" %}
<p><strong>Bank Account No:</strong> {{ doc.party_bank_account_no }}</p>
<p><strong>Bank IFSC:</strong> {{ doc.party_bank_ifsc }}</p>
{% elif doc.razorpayx_payout_mode == "UPI" %}
<p><strong>UPI ID:</strong> {{ doc.party_upi_id }}</p>
{% else %}
<p>This payment was done after you provided your payment details to <strong>RazorPayX Link</strong></p>
{% endif %}