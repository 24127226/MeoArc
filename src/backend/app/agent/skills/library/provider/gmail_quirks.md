---
name: gmail-quirks
description: Use when the email provider is Gmail — for search syntax, label vs folder distinctions, and thread behaviour
---

# Gmail Quirks

## Overview
Gmail is not a traditional IMAP provider. Its label-and-archive model, conversation threading, and powerful search syntax behave differently from folder-based clients. Understanding these quirks is essential for correct read/write operations through the Gmail API.

## When to Use
- Provider is identified as Gmail
- Performing operations through the Gmail API
- Constructing search queries
- Explaining Gmail behaviour to the user (e.g. "why can't I find this email in the folder?")

## Key Concepts

### Labels vs Folders
| Aspect | Gmail (Labels) | Traditional (Folders) |
|--------|----------------|----------------------|
| An email can be in | Multiple labels | One folder |
| Deleting a label | Email stays in inbox/other labels | Moving from folder = moved |
| Archive | Removes inbox label | No concept of archive |
| `INBOX` | Just another label with special status | The root folder |

**Practical implications:**
- An email can be in `INBOX`, `URGENT`, and `PROJECT_X` simultaneously
- "Moving" to a folder in Gmail = adding a label + optionally removing `INBOX`
- Deleting a label ≠ deleting the email — unless you also trash it

### Conversation Threading

Gmail groups messages by subject line into threads (conversations).

| Behaviour | Detail |
|-----------|--------|
| Thread key | Messages with same subject + participants are grouped |
| Reply in thread | Gmail API: `threadId` in the response links them |
| Breaking a thread | Changing subject line creates a new thread |
| Thread metadata | Labels, read state, and star apply to the **entire thread**, not individual messages |

**API note:** When fetching messages, always check `threadId`. Operations on a thread affect all messages within it.

### Gmail Search Syntax

Use these in the Gmail API `q` parameter:

| Query | Finds |
|-------|-------|
| `from:alice@example.com` | Emails from a specific sender |
| `to:bob@example.com` | Emails to a specific recipient |
| `subject:meeting` | Emails with "meeting" in subject |
| `has:attachment` | Emails with any attachment |
| `is:unread` | Unread emails |
| `is:read` | Read emails |
| `in:inbox` | In inbox |
| `in:trash` | In trash |
| `in:spam` | In spam |
| `label:URGENT` | Has label "URGENT" |
| `after:2026/07/20` | After a date |
| `before:2026/07/27` | Before a date |
| `older_than:7d` | Older than 7 days |
| `newer_than:2d` | Within the last 2 days |
| `-has:userlabels` | In inbox only (no user labels) |
| `{from:alice from:bob}` | OR — matches either |
| `filename:pdf` | Has a PDF attachment |

**Composing queries:**
- Combine with space (AND): `from:alice is:unread`
- OR with `{}` or `OR`: `{from:alice from:bob}` or `from:alice OR from:bob`
- Negate with `-`: `from:alice -is:read`
- Exact phrase with `""`: `subject:"project update"`

### Gmail API Specifics

| Operation | Notes |
|-----------|-------|
| `users.messages.list` | Returns message IDs + thread IDs. Use `q` for filtering. |
| `users.messages.get` | Returns full message with payload. `format=metadata` to reduce payload. |
| `users.messages.modify` | `addLabelIds`, `removeLabelIds` — never replaces, always add/remove. |
| `users.messages.trash` | Moves to trash (not permanent delete). |
| `users.messages.delete` | **Permanent.** Use only after user confirmation. |
| `users.threads.modify` | Applies label changes to **all** messages in the thread. |

**Pagination:** Gmail API paginates at 100 results per page. Use `nextPageToken` to fetch more.

### Common User Confusions

| User says | What Gmail actually does |
|-----------|--------------------------|
| "I moved it to Project folder" | You applied the `PROJECT` label. It's still in inbox. |
| "I deleted it but it's still there" | You archived it (removed inbox label). Check All Mail. |
| "This email is in two places" | It can be — labels are not exclusive. |
| "I replied but it's a new thread" | Subject changed slightly — thread broke. |

Be ready to explain these when the user asks "where did my email go?"

## Complementary Skills
- **inbox_cleanup** — Gmail's label+archive model affects how cleanup (delete vs archive) behaves
- **outlook_quirks** — when the user switches between providers or has multiple accounts

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Treating labels as folders | Labels are tags. An email can have many. |
| Assuming thread operations affect one message | `threads.modify` affects every message in the thread |
| Not paginating | Always loop with `nextPageToken` |
| Using `delete` instead of `trash` | Default to `trash` unless user explicitly says permanent |
