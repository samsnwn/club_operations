# Blue Velvet Club Operations

Shared language for the club's operations platform. Only the invoice-ingestion
quick win (PLAN.md §Phase 0.5) is defined so far.

## Invoice ingestion

**Invoice folder**:
The shared Google Drive folder the owner uploads invoices to; the only
production source. Files stay there as the owner's archive.
_Avoid_: Inbox, Drive, upload folder

**Local inbox**:
A folder on the service's own machine used for development, tests and
offline demos. Never the owner's channel.
_Avoid_: Drop folder (in user-facing text), inbox

**Ingestion channel**:
Either the invoice folder or the local inbox.
_Avoid_: Source (in user-facing text), connector

**Capture**:
One file taken in from an ingestion channel, before anyone knows whether it is
a new invoice.
_Avoid_: Upload, attachment, document

**Invoice**:
A capture that is unique by content and is being tracked through review.
_Avoid_: Record, item, row

**Extraction**:
Reading an invoice's text and proposing field values from it.
_Avoid_: Parsing, classification, OCR (OCR is only one way of getting the text)

**Suggestion**:
A field value proposed by extraction. It is never a fact until a reviewer
confirms it.
_Avoid_: Guess, prediction, extracted value

**Classification**:
Deciding whether a capture is an invoice at all, and which known supplier sent
it. Not built yet; today the supplier is only a suggestion.
_Avoid_: Using it for extraction

**Required fields**:
Supplier, invoice date and gross amount: the minimum an invoice needs before it
can be confirmed.
_Avoid_: Mandatory fields, key fields

**Needs attention**:
An open invoice where extraction did not suggest every required field, so the
reviewer has to enter them by hand.
_Avoid_: Low confidence, unrecognised, failed

**Open**:
An invoice still waiting for a review decision: pending review or needs
attention.
_Avoid_: Pending (that is only one of the two open states), unreviewed

**Confirm**:
A reviewer's decision that an invoice's final values are correct. Only
confirmed invoices may ever reach the accounting sheet.
_Avoid_: Approve, accept

**Reject**:
A reviewer's decision that a capture should never be exported. Final; the
original is kept on file.
_Avoid_: Delete, discard
