<p>Dear {{ doc.party_name }},</p>

<p>A payment of Rs. {{ frappe.utils.fmt_money(doc.paid_amount) }} has been transferred to you as per the bank details provided by {{ doc.company }}.</p>

<p>For more information, please check the attachment.</p>
