---
name: inbox-cleanup
description: Use when the user wants to bulk-delete spam, archive old emails, or mass-mark messages as read
---

# Inbox Cleanup

## Overview
Inbox clutter accumulates fast. This workflow batch-deletes spam, archives old messages, and marks noise as read — but it is a **destructive workflow** and must never act without explicit user confirmation. Every batch operation requires a preview, a confirmation prompt, and a post-operation report.

## ⚠️ Core Constraint — Human-in-the-loop
**Destructive operations (delete, archive, mark-read) require explicit user confirmation before execution. The agent must never perform these actions autonomously.**

This is non-negotiable. The user must see what will be affected and explicitly approve before anything changes.

## When to Use
- User says "clean my inbox" or "declutter"
- User wants to delete all spam
- User wants to archive everything older than N days
- User wants to mark all newsletters as read
- User wants bulk operations against a specific sender or domain

**Do NOT use** when the user wants to manage individual messages or needs a triage/summary first.

## Core Workflow

```
                     ┌──────────────────────┐
                     │ Ask scope: what to   │
                     │ clean + criteria     │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ PREVIEW: compute     │
                     │ count + show 5 sam-  │
                     │ ples per category    │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ CONFIRM: show summ-  │
                     │ ary table → ask y/N  │
                     │ WAIT for response    │
                     └──────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
              ┌──────────────┐     ┌──────────────┐
              │ User: No     │     │ User: Yes    │
              │ → Stop.      │     │ → Execute in │
              │   Report 0.  │     │   batches    │
              └──────────────┘     └──────┬───────┘
                                          │
                                          ▼
                               ┌──────────────────────┐
                               │ Report: done count,  │
                               │ failures, remaining  │
                               └──────────────────────┘
```

## Step by Step

### 1. Ask scope
Clarify what the user wants to clean. Do not assume. Ask:
- **Type:** delete? archive? mark-read?
- **Criteria:** spam? older than N days? specific sender/domain? all read emails older than N?
- If ambiguous, list the options and let them pick.

Single-action only per round — don't mix delete and archive in one confirmation.

### 2. Preview (REQUIRED)
Before any action, compute and present:
- Count of affected messages per category
- A representative sample of up to 5 messages per category (subject + sender + date snippet)
- Storage estimate if applicable (e.g. "≈ 12 MB")

```
Preview — Delete spam (23 messages)
Sample (5 of 23):
  1. "You've won!" — winner@scam.com — 22 Jul
  2. "Cheap watches" — deals@spam.net — 21 Jul
  3. ...
```

### 3. Confirm (REQUIRED)
Show a confirmation table and **wait for user response**.

```
┌─ Cleanup Preview ─────────────────────────┐
│ Delete spam               23 emails        │
│ Archive read (older 90d)  12 emails        │
│ Mark-read newsletters      8 emails        │
│ ─────────────────────────                 │
│ Total                     43 emails        │
│ Samples shown above.                       │
│                                            │
│ Proceed? [y/N]                             │
└────────────────────────────────────────────┘
```

Do not proceed without an affirmative answer. "y", "yes", "Y", "do it" all count. Anything else = no.

### 4. Execute
- Process in batches of 10 with progress reporting: "Deleted 10/23 spam messages..."
- On failure: log the specific error, continue with the rest.
- If more than 20% fail, pause and notify the user.

### 5. Report
Summarise:
```
✅ Cleanup complete
   Deleted: 21 (2 failed — permission denied on thread XXX)
   Archived: 12
   Marked read: 8
   Remaining: 2 spam (skipped due to errors)
```

## Safety Rules
These must never be bypassed:

1. **Never delete without showing a sample first.**
2. **Never archive messages from the last 7 days** unless the user explicitly says to.
3. **Flag important-looking emails for manual review** before acting: meeting invites, calendar notifications, billing statements, messages from frequent contacts.
4. **Single action type per round.** Delete and archive are separate operations requiring separate confirmations.

## Common Rationalizations (DO NOT FALL FOR)

| Rationalization | Why it's wrong |
|----------------|----------------|
| "The user said clean, so I'll just do it" | "Clean" is ambiguous. Preview first. |
| "Showing the count is enough" | The user needs sample subjects to judge. |
| "They'll see the action in undo" | Not all actions are undoable (delete). |
| "I already know what they want" | You don't. Ask. |

## Red Flags — STOP

- About to delete/archive/mark-read without showing samples
- User said "clean" but you haven't asked what that means
- Processing more than 50 messages in one confirmation
- Mixing delete with archive in one operation
- Thinking "this is obvious, I can skip preview"

**All of these mean: stop, show preview, wait for confirmation.**

## Complementary Skills
- **email_triage** — to identify which messages need action before mass-cleanup
- **gmail_quirks** / **outlook_quirks** — for provider-specific bulk operation behaviour
- **client_comms** — if cleanup involves client-facing threads that need a careful touch

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping preview | Show count + samples before every action |
| Proceeding without confirmation | Wait for explicit "y" / "yes" |
| Mixing delete + archive in one batch | One action type per confirmation round |
| Not showing samples | Counts alone are insufficient — show actual subjects |
| Deleting important auto-generated mail | Flag invites, billing, calendar notifications for review |
