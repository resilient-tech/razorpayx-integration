# 💡 Payout Tips and Notes

## 🌐 Payout Link

- To pay via **Payout Link**, choose the payment transfer method as **Link**.  

- Payouts created via **Payout Link** are managed as payouts, not as payout links.  
  - **Example**:  
    - Only **Payout** statuses are maintained as `RazorpayX Payout Status`.  
    - The status will show as `Not Initiated` or `Queued` until the payout is created.  
    - The payout is created when the party provides bank details via the link.  
    - Once the payout is initiated, the status updates based on webhook events.  
    - If the payout is canceled or fails, the payout link will also be canceled.  

- **Party's Contact Details**:  
  - To create a Payout Link, the party's contact details (email or mobile) are mandatory.  
  - For **Employees**: The preferred email or mobile number must be set.  
  - For others: Select the **Contact** details.  

## 📝 General Notes

- **Make Online Payment Checkbox**:  
  - This checkbox appears after saving the Payment Entry (PE) for the first time if the integration is found via the Company's Bank Account and User have permissions.

- **Reconfiguring RazorpayX**:  
  - If RazorpayX is configured after creating the PE, reselect the **Company Bank Account** and save the PE to set up the integration.  

- **Amended Payment Entries**:  
  - If an **Amended Payment Entry** has its original PE marked for `Make Online Payment`, you cannot make a payout with the amended PE.  
  - Payment details cannot be changed in such cases.  
  - In future updates, if the original PE's payout is **Failed/Reversed/Canceled**, the amended PE will allow creating a payout.  

- **Payout or Payout Link Canceled/Failed**:  
  - If a **Payout** or **Payout Link** is Canceled/Failed and the webhook event is captured, the Payment Entry will also be canceled.  

- **Payout Reversed**:  
  - If a **Payout** is Reversed, only the payout status is updated, and the PE is not canceled.  
  - Reversal Journal Entries (JE) for the Payment Entry and Fees Reversal JE will be created if configured.  
  - For more details on Reversal Accounting, read [here](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/accounting/2_payout_reversal.md).  

- **Payout Description**:  
  - Maximum length: 30 characters.  
  - Allowed characters: `a-z`, `A-Z`, `0-9`, and spaces.  

- **UTR in Payment Entry**:  
  - The **UTR** will be set after the payout is **Processed**.  
  - Until then, the default placeholder will be:

    ```bash
    *** UTR WILL BE SET AUTOMATICALLY ***
    ```
