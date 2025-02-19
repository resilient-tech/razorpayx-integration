# Make RazorpayX Payout with Payment Entry

## Requirements

1. At least one `RazorpayX Integration Setting` available
2. `Company Bank Account must` be set and associated with RazorpayX Setting
3. User must have
   1. `Online Payment Authorizer` Role
   2. Permission to submit `Payment Entry`
4. `Make Online Payment` should be checked
   - If not check you can make payout after submit if Integration Setting is set.

## Notes

- Here `Payout` and `Payout Link` consider one entity.
  - If you want to pay via `Payout Link` choose transfer mode `Link`
  - Then `Payout` created via `Payout Link` will be managed not `Payout Link`
    - Example:
      - Only `Payout` status are maintain as `RazorpayX Payout Status`
      - Status of RazorpayX will be `Not Initiated` or `Queued` until `Payout` created for this.
      - If `Payout` is cancelled or failed `Payout Link` will also cancelled

- `Make Online Payment` checkbox appear after saving PE first time if Integration Found.

- If RazorpayX configure after the PE creation, reselect `Company Bank Account` and save.

- If `Amended` Payment Entry's original PE is already mark for `Make Online Payment` then Amended PE will not make payout.
  - Also Payment Details are not allowed to change.

- If `Payout` or `Payout Link` cancelled/failed and webhook event captured then Payment Entry will also cancelled!

- If `Payout` is revered only status will updated and PE will not be cancelled!

## Method 1: Create Payout with simple workflow

<!-- Video|Gif for simple workflow -->

- If there is any frappe workflow is active for PE than `Pay and Submit` will not be visible and on submit `Make Online Payment` is unchecked if checked.


## Method 2: Create Payout with `Make Payout` custom button

- After submit if `Make Online Payment` is unchecked and Integration Setting are set than it is visible.

<!-- Video|Gif for Make Payout workflow -->

## Method 3: Bulk Pay and Submit

- Bulk `Pay and Submit` with list view bulk action

- Ask confirmation for those PE which have Integration Setting set but `Make Online Payment` is unchecked.

<!-- Video|Gif for bulk workflow -->

<!-- Details tag for different type of dialogs -->

### Notifications

- 2 exmaple notification is given.
  - When Payout Failed/Reversed/Cancelled 
  - When Payout Processed

- To use enable the notification

<!-- Image : Notification -->