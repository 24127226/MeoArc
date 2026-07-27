---
name: daily-digest
description: Use when the user asks for a daily summary, weekly recap, or wants email activity grouped and reported over a time window
---

# Daily Digest

## Overview
When the user wants a bird's-eye view of email activity over a period, collect all messages (read + unread), group them by meaningful category, and produce a scannable report. The digest surfaces what happened, how much, and what matters most — without drowning the user in individual summaries.

## When to Use
- User says "give me a digest" or "what happened this week?"
- End-of-day or end-of-week automated check-in
- User returns from vacation and wants a broad overview before deep-diving
- User wants counts by category (work vs personal vs finance)

**Do NOT use** when the user wants prioritized actions (use email_triage) or a single-thread deep-dive.

## Core Workflow

```
                     ┌──────────────────┐
                     │ Determine period │
                     │ (default: 24 h)  │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  Collect emails  │
                     │  (excl. spam)    │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Group by label / │
                     │ sender domain /  │
                     │ semantic cluster │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Per group: count │
                     │ + top 1-2 high-  │
                     │ lights           │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Generate report  │
                     │ with ⭐ markers  │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Present + offer  │
                     │ dive-in per group│
                     └──────────────────┘
```

### 1. Determine period
Default: last 24 hours. Accept natural language ranges ("this week", "last 3 days", "since Monday"). Validate that the period makes sense (don't accept "last year" without asking).

### 2. Collect
Fetch all messages (read + unread) within the period. Exclude spam and trash. If the count exceeds 200, note the total and work with the most recent 200.

### 3. Group by category
Use labels if available, otherwise fall back in this order:
1. Gmail labels / folders
2. Sender domain clustering (company.com → Work)
3. Semantic clustering based on subject keywords ("invoice" → Finance, "meeting" → Calendar)

Standard groups: **Work / Personal / Finance / Social & Newsletters / Academic / Calendar & Meetings**

### 4. Count & highlight
Per group: total count, unread count, and 1–2 most significant messages with a one-line rationale for why they matter (sender importance, subject urgency, thread length).

### 5. Generate report
```
📋 Daily Digest — Mon 27 Jul 2026 (last 24 h)
├─ 💼 Work (12 new, 3 unread)
│  ⭐ Project X: timeline revised (from John) — ⚠ deadline now Friday
│  ⭐ Sprint retro notes shared (from Alice)
├─ 🏠 Personal (4 new, 1 unread)
│  ⭐ Mom: dinner Saturday? (read but unreplied)
├─ 💳 Finance (2 new)
│  ⭐ Credit card statement available
├─ 📬 Social & Newsletters (8 new)
│  (3 unread) — 1-click archive available
└─ 📅 Calendar (1 new)
     Team standup moved to 10:30
```

### 6. Present
Return the digest. After presenting, offer to dive deeper into any group: "Want me to expand any section or take action on an item?"

## Output Contract
**REQUIRED elements, in order:**
1. Header line: `📋 Digest — <label> <date> (<period>)`
2. Groups listed by importance (Work/Academic first, Social last)
3. Each group: emoji + name + (total new, unread count)
4. ⭐ for highlights with a one-line rationale
5. Collapsible low-importance groups (Social, Promotions)
6. Closing offer to dive deeper

## Complementary Skills
- **email_triage** — for per-item prioritisation and suggested actions instead of a grouped overview
- **inbox_cleanup** — to archive or delete after reviewing the digest

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Individual email summaries for every message | Only highlight 1–2 per group |
| Flat list sorted by date | Group by category, sort groups by importance |
| No rationale for highlights | Every ⭐ needs a reason it matters |
| Burying critical items | Work/Academic groups first; surface ⭐ items |
| Always fetching everything | Respect large mailboxes — cap at 200 and report the cap |
