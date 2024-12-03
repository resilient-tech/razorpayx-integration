import frappe


# TODO: Proper way to fetch contact details of a party ?
def get_party_contact_details(party_type: str, party: str) -> dict:
    """
    Returns the `Mobile No` and `Email` of the `Party`.
    """
    pass

    # field_map = {
    #     "Customer": ["email_id", "mobile_no"],
    #     "Supplier": ["email_id", "mobile_no"],
    #     "Employee": [
    #         ["prefered_email", "personal_email", "company_email"],
    #         "cell_number",
    #     ],
    # }


"""
Customer: email_id, mobile_no
Supplier: email_id, mobile_no
Employee: [prefered_email,company_email,personal_email], [cell_number,emergency_phone_number]
Shareholder: Don't have email_id, mobile_no ??
"""
