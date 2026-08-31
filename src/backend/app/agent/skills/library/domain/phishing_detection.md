---
name: phishing-detection
description: Use when the user asks whether an email is suspicious, a scam, or safe to open
---

# Phishing Detection

## Overview
Phishing emails are the most common security threat to any email account. This skill lists the red flags to check, what to verify before clicking anything, and what actions to take when an email is confirmed suspicious.

## When to Use
- User forwards or pastes an email asking "is this a scam?"
- User says "I got a strange email from [bank/shipping/unknown]"
- User asks "should I click this link?"
- User reports an email asking for password or payment information
- Suspicious attachment or unsolicited download request

**Do NOT use** when the user is composing an email (use the other domain skills instead).

## Red Flags — Quick Scan

Check these in order. If ANY is suspicious, treat the email as unverified:

| Red Flag | What to look for |
|----------|------------------|
| **Sender address mismatch** | Display name says "PayPal" but the actual email is `paypa1-support@random.ru` |
| **Generic greeting** | "Dear Customer" / "Dear User" instead of your actual name |
| **Urgency / fear** | "Account suspended — act now!" / "Unauthorised login detected" |
| **Suspicious link** | Hover shows a different domain than the display text claims |
| **Unexpected attachment** | Invoice, receipt, or PDF you weren't expecting |
| **Spelling / grammar errors** | Official emails are proofread. Broken English is a warning. |
| **Asking for credentials** | No legitimate service emails you asking for your password or OTP |
| **Threat of consequences** | "Legal action", "account deletion", "police report" |

## Detailed Checks

### Check the sender
1. **Full email address** — not just the display name. Scammers spoof display names.
2. **Domain** — `@paypal.com` vs `@paypa1.com` vs `@paypal-security.com`
3. **Previous emails** — does this sender have a history? If first contact, be suspicious.

### Check the link (without clicking)
Hover over every link (or inspect the raw HTML):

```
Display text: "Click here to verify your account"
Actual link:   http://evil.com/steal-credentials
```

If the domain in the link does not match the claimed sender's official domain, it's phishing.

### Check the attachment
- Unexpected attachments from unknown senders = do not open
- Attachments with `.exe`, `.zip`, `.scr`, `.vbs`, `.docm` extensions are high-risk
- Even PDFs and Office docs can contain malicious macros

## What to Do

| Situation | Action |
|-----------|--------|
| Confirmed phishing | **Do not click anything.** Mark as spam / report phishing in Gmail/Outlook. Delete. |
| Unsure | Do not reply. Do not click. Check the official website by typing the URL manually (not from the email). |
| Already clicked a link | Change your password immediately. Enable 2FA. Check account activity. |
| Already entered credentials | Change password. Contact the real support team of the impersonated service. |

## Common Mistakes

| Mistake | Fix |
|---------|------|
| Trusting the display name | Always check the raw email address, not the display name |
| Clicking "unsubscribe" on suspicious emails | Legitimate unsubscribe is safe, but scammers use it to verify active emails — better to mark as spam |
| Believing urgency | Scammers create fake deadlines to bypass your caution. Pause and verify. |
| Forwarding suspicious emails to others | Don't spread potential threats. Report/delete instead. |
| Assuming Gmail/Outlook catches everything | No filter is perfect — always use your own judgment |
