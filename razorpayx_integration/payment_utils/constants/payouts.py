from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class PAYOUT_MODE(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "Link"
    CARD = "Card"
