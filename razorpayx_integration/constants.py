from razorpayx_integration.payment_utils.constants.enums import BaseEnum

BUG_REPORT_URL = "https://github.com/resilient-tech/razorpayx_integration/issues/new"

### Constants for RazorpayX Integration ###
RAZORPAYX = "RazorPayX"
RAZORPAYX_SETTING_DOCTYPE = "RazorPayX Integration Setting"


### Constants for APIs ###
class SUPPORTED_HTTP_METHOD(BaseEnum):
    GET = "GET"
    DELETE = "DELETE"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"


RAZORPAYX_BASE_API_URL = "https://api.razorpay.com/v1/"
SECONDS_IN_A_DAY = 86400  # use for to get day's end epoch time
