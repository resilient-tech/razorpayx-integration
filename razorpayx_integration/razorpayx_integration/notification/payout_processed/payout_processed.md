<p>M/S {{ doc.party_name }},</p>

<p>A payment of <strong>{{ frappe.utils.fmt_money(doc.paid_amount,currency="INR") }}</strong> has been transferred to you by <strong>{{ doc.company }}<strong>.</p>

<p>For more information, please check the attachment.</p>
