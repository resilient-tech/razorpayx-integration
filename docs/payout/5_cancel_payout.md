# 🚫 Workflow to Cancel Payout

## 🛠️ Cancellation Conditions

- A **Payout** can only be canceled in the following states:

  1. **Not Initiated** (A custom state defined in RazorpayX Integration)
  2. **Queued**

## 📝 Steps to Cancel a Payout

1. **Cancel the Payment Entry**:  
   - To cancel a payout, cancel the **Payment Entry** from which the payout was made.  

2. **Confirmation Dialog**:  
   - If the payout is in a cancellable state, a confirmation dialog will appear to confirm the cancellation.  

https://github.com/user-attachments/assets/0ea12c0f-6a5e-40c2-bbf5-eb829ba9ea76

## 📌 Notes

- If **Auto Cancellation** is enabled in the `RazorpayX Configuration`, the dialog box will not be shown, and the payout will be **canceled automatically**.
- You can cancel a `Payment Entry` regardless of the  `RazorpayX Payout Status`.
