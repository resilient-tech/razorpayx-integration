# Copyright (c) 2025, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    return get_columns(), get_data(filters)


def get_data(filters: dict | None = None) -> list[dict]:
    pass


def get_columns() -> list[dict]:
    return [
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
        },
        {
            "label": _("RazorpayX Configuration"),
            "fieldname": "razorpayx_config",
            "fieldtype": "Link",
            "options": "RazorpayX Configuration",
        },
        {
            "label": _("Docstatus"),
            "fieldname": "docstatus",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout Mode"),
            "fieldname": "payout_mode",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout ID"),
            "fieldname": "payout_id",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout Link ID"),
            "fieldname": "payout_link_id",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout Status"),
            "fieldname": "payout_status",
            "fieldtype": "Data",
        },
        {
            "label": _("Paid Amount"),
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "options": "INR",
        },
        {
            "label": _("UTR"),
            "fieldname": "utr",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout Made By"),
            "fieldname": "payout_made_by",
            "fieldtype": "Link",
            "options": "User",
        },
        # TODO: add column for payout which are initiated in the original PE for amended PEs?
    ]
