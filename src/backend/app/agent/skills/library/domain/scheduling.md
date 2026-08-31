---
name: scheduling
description: Use when composing a meeting request, rescheduling an existing meeting, or sending calendar-related emails
---

# Scheduling Email

## Overview
Scheduling emails are short and information-dense: who, when, where, and why. The goal is to minimise back-and-forth by preempting questions (proposing specific times, providing the meeting link upfront, stating duration).

## When to Use
- Requesting a meeting with someone
- Rescheduling or cancelling an existing meeting
- Confirming a meeting time
- Sending a calendar invite via email (text-only)
- Coordinating availability with multiple people

**Do NOT use** for preparing meeting content (use meeting_prep) or composing non-scheduling emails.

## Templates

### Meeting Request (Internal / Peer)
```
Subject: Meeting: [Topic] — [Duration] min

Hi [Name],

I'd like to set up a [duration]-minute meeting to discuss [topic].

I'm available at:
• Mon 28 Jul — 10:00–11:00, 14:00–16:00
• Tue 29 Jul — 9:00–12:00
• Wed 30 Jul — 13:00–15:00

Does any slot work for you? Happy to propose others.

Thanks,
[Your Name]
```

### Meeting Request (External / Client)
```
Subject: Request: Meeting to discuss [Topic]

Dear [Name],

I'd like to schedule a [duration]-minute call to discuss [topic/purpose].

Proposed times ([timezone]):
• Option A: [date] at [time]
• Option B: [date] at [time]

If neither works, please suggest a few alternatives that suit your schedule.

The meeting link will be sent upon confirmation.

Best regards,
[Your Name]
```

### Reschedule
```
Subject: Reschedule: [Original meeting topic] — [Original date]

Hi [Name],

Unfortunately, I need to reschedule our meeting originally set for [date/time].

Could we move it to one of the following slots instead?
• [Option A]
• [Option B]

Apologies for the inconvenience.

Thanks,
[Your Name]
```

### Cancel
```
Subject: Cancelled: [Original meeting topic] — [Original date]

Hi [Name],

I'm cancelling our meeting on [date/time] regarding [topic].

Reason: [brief, optional — "The issue has been resolved" / "This is no longer a priority"]

I'll reach out if we need to reschedule. Thanks for the time.

Thanks,
[Your Name]
```

### Confirmation (replying to a meeting request)
```
Subject: Confirmed: [Original subject]

Hi [Name],

[Date/time] works for me. Confirming our meeting to discuss [topic].

See you then.

[Your Name]
```

## Quick Reference

| Scenario | Subject pattern | Key info to include |
|----------|----------------|---------------------|
| Request | `Meeting: <topic> — <duration>` | Multiple time options, purpose |
| Reschedule | `Reschedule: <topic> — <old date>` | Apology, new options |
| Cancel | `Cancelled: <topic> — <date>` | Reason (brief), no alternative needed |
| Propose to client | `Request: Meeting to discuss <topic>` | 2 specific options, timezone |

## Common Mistakes

| Mistake | Fix |
|---------|------|
| Proposing only one time | Always offer 2–3 options — one time forces back-and-forth if it doesn't work |
| No subject topic | "Meeting" as subject is useless — include the topic |
| Forgetting timezone | Always include timezone for cross-timezone meetings |
| Vague duration | State "30 min" or "1 hour" — not "quick chat" |
| No meeting link | If using a recurring link, include it in the first email — don't wait for confirmation |
