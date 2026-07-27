---
name: outlook-quirks
description: Use when the email provider is Outlook / Microsoft 365 — for category vs folder model, Focused Inbox, and Graph API nuances
---

# Outlook Quirks

## Overview
Outlook (Exchange / Microsoft 365) differs from Gmail in fundamental ways: folders are exclusive, categories are labels on a single item, and the Focused/Other split adds a second inbox layer. The Graph API has its own conventions and pagination model.

## When to Use
- Provider is identified as Outlook / Exchange / Microsoft 365
- Using Microsoft Graph API for email operations
- Explaining Focused Inbox or folder behaviour to the user
- Handling categories, rules, or auto-archiving

## Key Concepts

### Folders vs Categories

| Aspect | Outlook Folders | Outlook Categories |
|--------|----------------|-------------------|
| Model | Exclusive (one email, one folder) | Tags (non-exclusive, like Gmail labels) |
| Inheritance | Moving changes location permanently | Adding a category does not move anything |
| Deletion | Deleting folder = prompt to delete contents | Deleting category = removed from all items |
| API representation | `mailFolder` resource | `categories` collection, assigned via `singleValueExtendedProperties` |

**Practical implications:**
- An email lives in exactly **one** folder (plus optional archive/pst)
- "Moving" in Outlook = the email is no longer visible in the source folder
- Categories overlay on top of the folder structure — they don't replace it
- To replicate Gmail-like labels: use **categories** + keep the email in one folder

### Focused Inbox

Focused Inbox splits the inbox into two tabs: **Focused** (important) and **Other** (bulk, low priority).

| Behaviour | Detail |
|-----------|--------|
| API detection | Check `inferenceClassification` property on a message: `focused` or `other` |
| User override | User can manually move messages between tabs (trains the model) |
| Server-side learning | Classification improves with user feedback |
| Relevance | Focused = messages the model thinks matter. Not the same as "read" or "starred". |

**When querying:** If the user says "I can't find it in my inbox," check the `inferenceClassification` — it may be in Other. Offer to look up both tabs.

## Graph API Specifics

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| List messages | `GET /me/messages` | `$top` for page size (max 1000) |
| Get message | `GET /me/messages/{id}` | Use `$select` to reduce payload |
| Send | `POST /me/sendMail` | Body contains `message` + `saveToSentItems` |
| Move | `POST /me/messages/{id}/move` | Destination folder ID required |
| Create draft | `POST /me/messages` | Returns draft — then `POST /me/messages/{id}/send` |

### Pagination

```python
# Graph API uses @odata.nextLink (URL-based), not page tokens
# $top controls page size (default 10, max 1000)
# Always decode the nextLink URL to handle it

url = "https://graph.microsoft.com/v1.0/me/messages?$top=100&$select=id,subject"
while url:
    resp = await graph_client.get(url)
    data = resp.json()
    for msg in data["value"]:
        process(msg)
    url = data.get("@odata.nextLink")  # None = no more pages
```

### Search

| Capability | Detail |
|------------|--------|
| Basic search | `GET /me/messages?$search="keyword"` |
| Search syntax | Supports KQL (Keyword Query Language) |
| From query | `$search="from:alice@example.com"` |
| Date filter | Use `$filter` with `receivedDateTime` — not `$search` |
| Combined | `$search="meeting"&$filter=receivedDateTime ge 2026-07-20` |

**`$filter` vs `$search`:**
- `$filter` is faster and structured (date, from, hasAttachments)
- `$search` supports fuzzy and full-text but is slower
- Prefer `$filter` when criteria are structured; use `$search` for subject/body keywords

### Categories (via Extended Properties)

Categories are stored as `singleValueExtendedProperties`. To read them:

```
GET /me/messages/{id}?$expand=singleValueExtendedProperties($filter=id eq 'String {00062008-0000-0000-C000-000000000046} Names String 0x0000')
```

To assign a category, use `categories` property directly (array of strings):
```python
message["categories"] = ["URGENT", "Project X"]
```

## Common User Confusions

| User says | What Outlook actually does |
|-----------|---------------------------|
| "I filed it in multiple folders" | Not possible — move copies? Check for duplicates. |
| "It's not in my inbox" | Check Focused → Other tab, or it was auto-sorted by a rule |
| "I deleted the category and it disappeared" | Category removed, message still exists in its folder |
| "I moved it but now I can't find it" | Search across all folders, including archive/pst |

## Complementary Skills
- **inbox_cleanup** — Outlook's Focused Inbox and folder model affect cleanup workflows
- **gmail_quirks** — when the user switches between providers or has multiple accounts

## Common Mistakes

| Mistake | Fix |
|---------|------|
| Treating categories like Gmail labels | Categories are metadata. Folders still own the message. |
| Ignoring Focused/Other split | Always check `inferenceClassification` before saying "not found" |
| Using Gmail search syntax on Graph API | Graph uses KQL + `$filter`, not `q=` parameters |
| Not using `$select` | Graph responses are verbose — always limit fields |
| Expecting labels to work like Gmail | Outlook has folders (exclusive) + categories (tags). Different mental model. |
