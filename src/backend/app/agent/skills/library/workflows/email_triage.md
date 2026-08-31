---
name: email-triage
description: Use when the user has unread emails, asks what needs attention, or wants inbox prioritised
---

# Email Triage

## Overview
Not all unread emails matter equally. This workflow classifies unread messages, scores them by priority, produces a concise summary, and recommends a concrete next action per message — so the user acts on what counts and ignores the rest.

## When to Use
- User asks "what's new?" or "anything urgent?"
- User has been away and returns to an overflowing inbox
- User wants a ranked to-do list drawn from email
- Morning inbox scan or any context switch back to email

**Do NOT use** when the user explicitly wants a narrative summary, a full digest, or already knows what they're looking for.

## Core Workflow

```
                     ┌──────────────┐
                     │ Fetch unread │
                     │  (≤ 7 days)  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Classify    │
                     │ urgent/act-  │
                     │ ionable/FYI/ │
                     │ spam         │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Score 1-5    │
                     │ (sender +    │
                     │ urgency cue) │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Summarise +  │
                     │ suggest act- │
                     │ ion          │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Present rank-│
                     │ ed list by   │
                     │ class        │
                     └──────────────┘
```

### 1. Fetch unread
Get all inbox messages with `UNREAD` flag from the last 7 days. Respect Gmail's throttling — fetch in batches if needed.

### 2. Classify
Assign one category per message:
- **urgent** — deadline within 24 h, meeting today, boss or professor, "ASAP" / "urgent" in subject
- **actionable** — requires a reply, approval, or task but no time pressure
- **FYI** — informational, no response needed
- **spam** — promotional, auto-generated, newsletter, already handled elsewhere

### 3. Score priority (1–5)
Within each class, rank by:
- Sender relevance (frequent contacts, known names → higher)
- Explicit urgency markers (dates, "EOD", "today")
- Thread participants (Cc to manager? Higher.)
- Previous unread count (same sender with 5 unread = higher)

### 4. Summarise
One or two lines per email:
> From: Prof. Nguyen — Re: Project deadline moved to Friday (was Monday). Needs confirmation by end of tomorrow.

### 5. Suggest action
Every urgent/actionable email gets a concrete next step:
- *Reply confirming new deadline by 5pm tomorrow*
- *Add task: review draft, due Thursday*
- *Forward to team for discussion*

### 6. Present
Output format — grouped by class, sorted by score within group:

```
📥 Triage — 14 unread
├─ URGENT (3)
│  ⭐ Prof. Nguyen — deadline moved (score 5) → Reply confirm by 5pm
│  ⭐ Alice — server down (score 5) → Check + respond
│     Bob — budget approval (score 3) → Approve by Fri
├─ ACTIONABLE (5)
│  ...
├─ FYI (4)
└─ Spam (2) — hidden, 1-click bulk trash available
```

## Output Contract
**REQUIRED elements, in order:**
1. Total count + date range
2. URGENT group with ⭐ for score 4–5 items
3. Every urgent/actionable item has a concrete suggested action
4. Spam grouped and collapsible (never expanded inline)

## Complementary Skills
- **daily_digest** — for a grouped period overview instead of per-item ranking
- **inbox_cleanup** — after triage, to batch-process identified spam or old items
- **meeting_prep** — when a thread leads to a meeting that needs a brief

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing multi-paragraph summaries | Keep to 1–2 lines per email |
| No suggested action | Every urgent/actionable item must have one |
| Treating all senders equally | Score by sender history + urgency cues |
| Presenting flat list by date | Group by class, sort by score within group |
| Expanding spam inline | Collapse spam under a single line with bulk action |
