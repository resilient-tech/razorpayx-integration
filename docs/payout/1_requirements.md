# 📋 Requirements Before Making Payout

## 🔐 Roles and Permissions

1. **Online Payments Authorizer Role**:  
   - The user must have the `Online Payments Authorizer` role to initiate payouts.  

2. **Submit Permission for Payment Entry**:  
   - The user must have permission to **submit** the **Payment Entry**.  

3. **Read Permission for RazorpayX Configuration**:  
   - The user must have at least **read** permission for the **RazorpayX Configuration** document.  

## 🔒 Authentication Setup

- For detailed steps on setting up authentication, refer to the [Authentication Guide](URL).  

## 💳 Payment Entry Requirements

1. **Payment Type**:  
   - Set the payment type to **Pay**.  

2. **Company Bank Account**:  
   - Ensure the selected **Company Bank Account** is linked to the RazorpayX Configuration.  

3. **Paid from Account Currency**:  
   - The currency must be set to **INR** (Indian Rupees).  

4. **Make Online Payment**:  
   - If **Checked**:  
     - The payout will be initiated automatically when the Payment Entry is submitted (via `Pay and Submit`).  
   - If **Unchecked**:  
     - The payout can be initiated manually after submission, provided the RazorpayX Configuration (via `Company bank Account`) is available.  
