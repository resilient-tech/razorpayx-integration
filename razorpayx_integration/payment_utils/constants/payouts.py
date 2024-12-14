from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class PAYOUT_MODE(BaseEnum):
    BANK = "NEFT/RTGS"  # NEFT/RTGS will be decided based on the amount at payout time
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "Link"
    CARD = "Card"
