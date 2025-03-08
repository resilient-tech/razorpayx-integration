# Setup Test and Live Mode for RazorpayX Integration

## Live Mode (Production Mode) in RazorpayX Dashboard

- **Purpose**: In Live Mode, actual money will be debited from your bank account.  
- **Use Case**: Use this mode only for real transactions in a production environment.  
- **Important**:  
  - Do **not** share API keys and secrets generated in this mode.  
  - Ensure proper security measures are in place to protect sensitive credentials.  

## Test Mode in RazorpayX Dashboard

- **Purpose**: In Test Mode, you can simulate transactions without debiting real money from your bank account.  
- **Test Balance**: Add test balance [here](https://x.razorpay.com/).  
  ![Test Balance](https://github.com/user-attachments/assets/bb83b7bb-6feb-4a91-b710-24b5a1b4795e)  

- **How to Enable Test Mode**:  
  1. Go to [Developer Controls](https://x.razorpay.com/settings/developer-controls).  
  2. Enable **Test Mode**.  
    ![Enable Test Mode](https://github.com/user-attachments/assets/0804ffdb-613b-4766-b7e0-592b90d780be)  

- **Test Mode Dashboard**:  
  After enabling Test Mode, your dashboard will look like this:  
  ![Test Mode Dashboard](https://github.com/user-attachments/assets/2308cd31-f587-4b7a-b83e-d7c9a355b8e7)  

- **Manually Change Payout Status in Test Mode**:  
  - In Test Mode, payout statuses need to be changed manually.  
  - You can only change the status if it is not in a final state.  
  - Go to [Payouts](https://x.razorpay.com/payouts).  
  - Hover over any payout and click on **Change Status**.  
    ![Change Payout Status](https://github.com/user-attachments/assets/33aca0d8-aec2-49b8-9fd7-6fbb7411c68e)  

## Setup Key ID and Key Secret

- **For Both Modes**:  
  The process to generate **Key ID** and **Key Secret** is the same for both Test and Live modes.  
  - **Important**: Never share Live Mode API credentials.  

## Setup Webhook

- **For Both Modes**:  
  The process to set up webhooks is the same for both Test and Live modes.  

  - **Test Mode Specific**:  
    When saving the webhook in Test Mode, use the fixed OTP:

    ```bash
    754081
    ```

## Setup Test and Live Mode in ERPNext Site

1. **Add Credentials**:  
   - For each mode (Test or Live), add the corresponding **Key ID** and **Key Secret** in the ERPNext RazorpayX Configuration.  

2. **Setup Webhook**:  
   - Configure the webhook URL for each mode separately.  

## Local Testing

- **Use Test Mode Credentials**:  
  - For local testing, always use Test Mode credentials to avoid real transactions.  

- **Live Webhook URL for Local Testing**:  
  To test live webhooks locally, use a tool like **Ngrok**. Replace the URL in the webhook configuration as follows:  

  Follow this [Guide](https://discuss.frappe.io/t/guide-for-using-ngrok-for-webhook-testing/141902) to get the Ngrok URL.  

  ```bash
  NGROK_URL/api/method/razorpayx_integration.razorpayx_integration.utils.webhook.webhook_listener
  ```  

  Replace `NGROK_URL` with the URL generated via Ngrok.  
