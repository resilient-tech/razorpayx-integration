# 🔔 Notifications

![Notification](https://github.com/user-attachments/assets/16efff38-56dd-4bb4-a146-36fdc08a6a23)

## 📩 Notification Types

Two custom notifications are provided:  

1. **Payout Failed/Reversed/Canceled**:  
   - Sent to the user who initiated the payout.  
   - Notifies them about the failure, reversal, or cancellation of the payout.  

2. **Payout Processed**:  
   - Sent to the **party** (Supplier/Employee etc.) if their contact email is available.  
   - Notifies them about the successful processing of the payout.  

## 🛠️ How to Enable Notifications

1. Go to **Notification** in ERPNext Site.  
2. Enable the relevant notifications for **Payout Failed/Reversed/Canceled** and **Payout Processed**.  

## 📌 Notes

- Ensure the **party's contact email** is correctly configured to receive **Payout Processed** notifications.
- Customize the notification templates to match your business needs.  
- Default `Outgoing EMail Account` is require to send notifications.
