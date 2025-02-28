# 🔄 Sync Bank Transactions via RazorpayX API for Bank Reconciliation

## 🛠️ How to Sync Transactions

1. **Ensure Bank Account is Associated with RazorpayX Configuration**:
   - The bank account must be linked to a `RazorpayX Configuration` to enable transaction syncing.

2. **Sync Transactions**:
   - During reconciliation, you can manually sync transactions up to the current time by selecting the associated bank account.


## 📸 Example

https://github.com/user-attachments/assets/4ec650ac-b305-4377-a386-d76703ae49c0

## 💡 Key Notes

- **Automatic Sync**: Bank transactions are synced daily via a cron job.
- **Manual Sync**: Use the manual sync option during reconciliation to fetch the latest transactions up to the current time.
- **Integration Requirement**: Ensure the bank account is associated with a `RazorpayX Configuration` for syncing to work.
