# Copyright (c) 2025, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Date
from frappe.utils.data import get_timespan_date_range

from razorpayx_integration.constants import RAZORPAYX_CONFIG


def execute(filters=None):
    return get_columns(), get_data(filters)


def get_data(filters: dict | None = None) -> list[dict]:
    from_date, to_date = parse_date_range(filters)

    PE = frappe.qb.DocType("Payment Entry")

    base_query = (
        frappe.qb.from_(PE)
        .select(
            PE.name.as_("payment_entry"),
            PE.posting_date,
            PE.company,
            PE.party_type,
            PE.party,
            PE.paid_amount,
            PE.razorpayx_payout_status.as_("payout_status"),
            PE.payment_transfer_method.as_("payout_mode"),
            PE.razorpayx_payout_desc.as_("payout_description"),
            PE.status.as_("docstatus"),
            PE.payment_authorized_by.as_("payout_made_by"),
            PE.integration_docname.as_("razorpayx_config"),
            PE.reference_no.as_("utr"),
            PE.razorpayx_payout_id.as_("payout_id"),
            PE.razorpayx_payout_link_id.as_("payout_link_id"),
        )
        .where(PE.company == filters.company)
        .where(PE.posting_date >= Date(from_date))
        .where(PE.posting_date <= Date(to_date))
        .where(PE.integration_doctype == RAZORPAYX_CONFIG)
        .where(PE.make_bank_online_payment == 1)
        .orderby(PE.posting_date, order=frappe.qb.desc)
    )

    # update the query based on filters
    if filters.party_type:
        base_query = base_query.where(PE.party_type == filters.party_type)

    if filters.party:
        base_query = base_query.where(PE.party == filters.party)

    if filters.docstatus:
        base_query = base_query.where(PE.status.isin(filters.docstatus))

    if filters.payout_status:
        base_query = base_query.where(
            PE.razorpayx_payout_status.isin(filters.payout_status)
        )

    if filters.payout_mode:
        base_query = base_query.where(
            PE.payment_transfer_method.isin(filters.payout_mode)
        )

    if filters.razorpayx_config:
        base_query = base_query.where(
            PE.integration_docname == filters.razorpayx_config
        )

    if filters.payout_made_by:
        base_query = base_query.where(
            PE.payment_authorized_by == filters.payout_made_by
        )

    return base_query.run(as_dict=True)


def parse_date_range(filters: dict) -> tuple[str, str]:
    if filters.date_time_span == "Select Date Range":
        return filters.date_range

    return get_timespan_date_range(filters.date_time_span.lower())


def get_columns() -> list[dict]:
    return [
        {
            "label": _("Payment Entry"),
            "fieldname": "payment_entry",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 200,
        },
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 180,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Link",
            "options": "Party Type",
            "width": 120,
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            "width": 180,
        },
        {
            "label": _("Paid Amount"),
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "options": "INR",
            "width": 150,
        },
        {
            "label": _("Payout Status"),
            "fieldname": "payout_status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Payout Mode"),
            "fieldname": "payout_mode",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Payout Description"),
            "fieldname": "payout_description",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Docstatus"),
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Payout Made By"),
            "fieldname": "payout_made_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 200,
        },
        {
            "label": _("RazorpayX Configuration"),
            "fieldname": "razorpayx_config",
            "fieldtype": "Link",
            "options": "RazorpayX Configuration",
            "width": 150,
        },
        {
            "label": _("UTR"),
            "fieldname": "utr",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Payout ID"),
            "fieldname": "payout_id",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Payout Link ID"),
            "fieldname": "payout_link_id",
            "fieldtype": "Data",
            "width": 180,
        },
    ]
