---
name: meeting-prep
description: Use when the user has a meeting coming up, needs a brief, or wants action items and decisions extracted from an email thread
---

# Meeting Preparation

## Overview
A meeting is only as good as the preparation behind it. This workflow takes an email thread (or a set of messages about an upcoming meeting) and produces a structured brief covering agenda, past decisions, action items with owners, and blockers — so the user walks in informed and doesn't waste time rehashing.

## When to Use
- User is about to attend a meeting and wants context
- User asks "what's the status of X?" before a sync
- User forwards a thread and says "prep me for this"
- User wants action items extracted from a long thread
- User says "what did we decide about Y?"

**Do NOT use** when the user just needs a quick reply or the thread is a single message with no decisions to extract.

## Core Workflow

```
                     ┌──────────────────────┐
                     │ Locate thread (ID /  │
                     │ URL / search query)  │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Read full thread in  │
                     │ chronological order  │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Extract: when, where,│
                     │ who, agenda purpose  │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Extract decisions    │
                     │ already made         │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Extract action items │
                     │ (owner + task + due) │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Flag risks / blockers│
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Generate structured  │
                     │ brief                │
                     └──────────────────────┘
```

### 1. Locate the thread
Accept: message ID, email URL, a search query, or a forwarded email. If the user provides a query, search inbox + sent + important folders. If nothing matches, say so — don't fabricate.

### 2. Read full thread
Parse all messages oldest-first. Note the cast (who wrote, who was Cc'd, who joined late), the tone (aligned? tense? silent stakeholders?), and timestamps.

### 3. Extract meeting details
- **Time / date / duration** (stated or inferred from calendar link)
- **Location or meeting link** (Zoom, Google Meet, room)
- **Attendees** (To + Cc, plus explicit delegates)
- **Agenda** (the stated purpose, plus any agenda items mentioned in the thread)

### 4. Extract decisions already made
List every closed decision from the thread. The goal is to prevent rehashing. Format:

| Decision | Made by | When | Status |
|----------|---------|------|--------|
| Use Python 3.13 for backend | John | 22 Jul | Confirmed |
| Skip Redis for MVP | Team | 23 Jul | Confirmed |

### 5. Extract action items
Every explicit ("Alice will draft the spec by Friday") or implicit ("we still need the spec") to-do. Format:

| Owner | Task | Deadline | Status |
|-------|------|----------|--------|
| Alice | Draft spec | Fri 25 Jul | ⏳ Pending |
| Bob | Review infra costs | Mon 28 Jul | ❌ Overdue |

**Never omit the owner.** If no owner is stated, flag it as unassigned.

### 6. Flag risks / blockers
Things that could stall the meeting or the project: missing inputs, pending approvals, unresponsive stakeholders, conflicting deadlines.

### 7. Generate brief
```
📝 Meeting Brief — Sprint Planning
├─ 📅 When & Where
│  Wed 30 Jul · 10:00–11:00 · Google Meet
├─ 👥 Attendees
│  John, Alice, Bob (+ Nam, invited)
├─ 📋 Agenda
│  1. Sprint goal review
│  2. Task assignment
│  3. Risk discussion
├─ ✅ Past decisions
│  • Python 3.13 confirmed
│  • Redis not needed for MVP
├─ 📌 Action items
│  • Alice → Draft spec (Fri 25) ⏳
│  • Bob → Review infra (Mon 28) ❌ OVERDUE
│  • Nam → Confirm API design (unassigned)
└─ ⚠ Risks
     Bob's infra review overdue — may block sprint start
```

If any action item is overdue, call it out prominently at the top of the brief.

## Output Contract
**REQUIRED sections, in order:**
1. Header: meeting topic
2. When & Where
3. Attendees
4. Agenda
5. Past decisions (table)
6. Action items (table with owners)
7. Risks / blockers

**Fail conditions:** Omitting any section above, or presenting action items without owners.

## Complementary Skills
- **email_structure** — to compose meeting confirmation, reschedule, or follow-up emails after prep
- **email_triage** — if the meeting thread is buried among unread messages
- **reply_etiquette** — when responding to participants after the meeting

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| No owner on action items | Never omit. Tag as "unassigned" if unclear. |
| Decisions and action items mixed in one list | Separate them — they serve different purposes |
| Chronological retelling of the thread | Synthesise into sections, don't narrate |
| Forgetting to flag overdue items | Scan deadlines against today's date |
| Fabricating thread content | If the thread lacks info, say so |
