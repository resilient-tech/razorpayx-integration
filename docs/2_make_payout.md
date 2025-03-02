# 💳 Make RazorpayX Payout with Payment Entry

## ✅ Requirements

1. **RazorpayX Configuration**: At least one configuration must be available.
2. **Company Bank Account**: Must be set and associated with the RazorpayX Configuartion.
3. **Payment Type**: `Pay`
4. **Paid from Account Currency**: `INR`
5. **User Permissions**:
   - Role: `Online Payment Authorizer`.
   - Permission to submit `Payment Entry`.
6. **Make Online Payment**: Ensure this checkbox is checked.
   - If unchecked, you can still make a payout after submission if the integration setting is configured.

## 📌 Notes

- Here **Payout and Payout Link** are considered one entity.
  - To pay via **Payout Link**, choose the transfer mode as `Link`.
  - Payouts created via **Payout Link** will be managed as payouts, not as payout links.
    - Example:
      - Only **Payout** statuses are maintained as `RazorpayX Payout Status`.
      - The status will show as `Not Initiated` or `Queued` until the payout is created.
      - Once the payout is initiated via the payout link, the status will update based on webhook events.
      - If the payout is canceled or fails, the payout link will also be canceled.

- The **Make Online Payment** checkbox appears after saving the Payment Entry (PE) for the first time if the integration is found.

- If RazorpayX is configured after creating the PE, reselect the **Company Bank Account** and save the PE to set integartion.

- If an **Amended Payment Entry** has its original PE marked for `Make Online Payment`, the amended PE will not create a payout.
  - Payment details cannot be changed in such cases.

- If a **Payout** or **Payout Link** is canceled/failed and the webhook event is captured, the Payment Entry will also be canceled.

- If a **Payout** is reversed, only the status will be updated, and the PE will not be canceled.

- **Payment Authentication Method**: OTP App (See `System Settings` Login tab)
  
  ![image](https://github.com/user-attachments/assets/b9daa82a-e7dd-469f-8008-f84aa7a79305)


## 🛠️ Methods to Create Payouts

### Method 1: Create Payout with Simple Workflow

https://github.com/user-attachments/assets/528a76bf-6c5f-49ab-9b13-e28499eb107d

- If a Frappe workflow is active for the PE, the `Pay and Submit` button will not be visible and on submission, `Make Online Payment` will be unchecked if previously checked.

### Method 2: Create Payout with `Make Payout` Custom Button

- After submission, if `Make Online Payment` is unchecked and the integration settings are configured, the `Make Payout` button will be visible.

https://github.com/user-attachments/assets/57064570-26cf-48d1-8ac9-35d9918016a2


### Method 3: Bulk Pay and Submit

- Use the **Bulk Pay and Submit** option in the list view for bulk actions.
- A confirmation dialog will appear for PEs with integration settings configured but `Make Online Payment` unchecked.
- If `Party Bank Account` is selected payout will be made with `NEFT` by default otherwise made with `Link`.
- It is recommeded to select valid  `Company Bank Account` and `Party Bank Account` and `Make Bank Online Payment` check to bulk pay.

https://github.com/user-attachments/assets/1fac304e-1de5-4e00-9d80-0fc4cf6c4ce8

<details>
<summary>📂 View Other Dialog Messages</summary>

1. **All Eligible to Pay**:  
   ![All Eligible](https://github.com/user-attachments/assets/6acc905a-5857-41c6-95b3-e7551bb6bb18)

2. **Some Eligible and Some Not Eligible**:  
   ![Some Eligible](https://github.com/user-attachments/assets/46aee276-4044-410e-9e43-603c054e6772)

3. **Only Unmarked**:  
   ![Only Unmarked](https://github.com/user-attachments/assets/532ba1a3-1108-4459-9b46-ea38fad71fe6)

4. **Invalid Selection**:  
   ![Invalid Selection](https://github.com/user-attachments/assets/f1f55dd3-5194-4f4f-9214-d98edc00e9ec)

</details>

## 🔔 Notifications

- Two example notifications are provided:
  1. When a payout is **Failed/Reversed/Canceled**.
  2. When a payout is **Processed**.

- Enable these notifications to use them.

![Notification](https://github.com/user-attachments/assets/39ec860b-0307-4c4c-b034-336b15b6f981)

## ❌ Cancellation Workflow

- A **Payout** can only be canceled in the `Not Initiated` or `Queued` state.

https://github.com/user-attachments/assets/ec56e347-b37b-49ef-ba84-d16819e93449

- **Note**: If **Auto Cancellation** is enabled, the dialog box will not be shown.
