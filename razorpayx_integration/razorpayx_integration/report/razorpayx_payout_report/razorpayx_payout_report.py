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
            PE.company,
            PE.posting_date,
            PE.integration_docname.as_("razorpayx_config"),
            PE.status.as_("docstatus"),
            PE.payment_transfer_method.as_("payout_mode"),
            PE.razorpayx_payout_id.as_("payout_id"),
            PE.razorpayx_payout_link_id.as_("payout_link_id"),
            PE.razorpayx_payout_desc.as_("payout_description"),
            PE.razorpayx_payout_status.as_("payout_status"),
            PE.paid_amount,
            PE.reference_no.as_("utr"),
            PE.payment_authorized_by.as_("payout_made_by"),
        )
        .where(PE.company == filters.company)
        .where(PE.posting_date >= Date(from_date))
        .where(PE.posting_date <= Date(to_date))
        .where(PE.integration_doctype == RAZORPAYX_CONFIG)
        .where(PE.make_bank_online_payment == 1)
    )

    # update the query based on filters
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

    if filters.ignore_amended:
        base_query = base_query.where(PE.amended_from.isnull())

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
        },
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
            "label": _("Paid Amount"),
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "options": "INR",
        },
        {
            "label": _("Payout Status"),
            "fieldname": "payout_status",
            "fieldtype": "Data",
        },
        {
            "label": _("UTR"),
            "fieldname": "utr",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout Mode"),
            "fieldname": "payout_mode",
            "fieldtype": "Data",
        },
        {
            "label": _("Payout Description"),
            "fieldname": "payout_description",
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
            "label": _("RazorpayX Configuration"),
            "fieldname": "razorpayx_config",
            "fieldtype": "Link",
            "options": "RazorpayX Configuration",
        },
        {
            "label": _("Payout Made By"),
            "fieldname": "payout_made_by",
            "fieldtype": "Link",
            "options": "User",
        },
        {
            "label": _("Docstatus"),
            "fieldname": "docstatus",
            "fieldtype": "Data",
        },
        # TODO: add column for payout which are initiated in the original PE for amended PEs?
    ]
