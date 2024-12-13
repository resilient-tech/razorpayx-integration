# Copyright (c) 2024, Resilient Tech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OnlineBankPaymentIntegration(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        integration_name: DF.Data
        website_url: DF.Data | None
    # end: auto-generated types
    pass
