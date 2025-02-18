# Connect ERPNext with RazorpayX

### Step 1: Create a Company's Bank Account with `RazorpayX` account details

- Mandatory
  - `Is Company Account`
  - `Bank Account No.`

<!-- Image-1 Bank Account -->

- For Test Mode:

  - `Bank Account No.` will be Customer Identifier, [Get it from here](https://x.razorpay.com/settings/banking)
  - <!-- Image-2 Customer Identifier -->

- For Live Mode:
  - `Bank Account No.` will be your Current Account number or Customer Identifier
    - <!-- Image-3 Bank Account No type -->

### Step 2: Create a `RazorpayX Integration Setting`

<!-- Image-4 RPX Setting -->

- Get `API Key` and `API Secret` if not available from [Here](https://x.razorpay.com/settings/developer-controls)
  - <!-- Image-5 API KEY and Secret -->
  
- Get `Account ID` from  (It is `Business ID`)
  - <!-- Image-6 Account ID -->
  - 

#### Setup WebHook

- Get webhook URL by clicking `Copy webhook URL`

- Add to RazorpayX dashboard. ([Add here](https://x.razorpay.com/settings/developer-controls))
  - <!-- Image-7 webhook -->
  - For test mode webhook testing refer [this](https://discuss.frappe.io/t/guide-for-using-ngrok-for-webhook-testing/141902)

- Add webhook secret otherwise updates will not be received