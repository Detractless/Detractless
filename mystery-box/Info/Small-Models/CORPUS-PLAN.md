# Corpus collection plan — exporting Gmail / Proton / Outlook (drafted 2026-07-15)

Goal: grow the fine-tuning corpus (FINETUNE-PLAN.md) from 434 emails to thousands of
REAL consumer-inbox emails across three providers. Division of labor: **you do the
sign-ins and exports** (I never handle account credentials), **I process everything
from local files onward**.

## Recommended route per provider

### Gmail — Google Takeout (no code, most reliable)
1. You: go to takeout.google.com → deselect all → select only Mail → choose
   specific labels if desired (Inbox, Promotions, Updates are the valuable ones)
   → export as .mbox → download the zip.
2. Me: parse the .mbox (Python stdlib `mailbox` module), extract HTML bodies,
   normalize into the corpus DB.
- Alternative if Takeout is too coarse: IMAP via app password — requires 2FA
  enabled on the Google account; you generate the app password and place it in a
  local file I read. Takeout is simpler and complete; start there.

### Proton — the app we already have
- mail.db already syncs Proton (`protonweb:` accounts via the hidden WebView2
  session; BridgeCore gRPC also available). The 434 rows are just the recent
  window. Two options, preferred first:
  1. Extend the existing UnifiedCommunication sync to pull deeper history
     (the scraper currently stops at recent mail — needs a look at its paging).
  2. Proton's official Export Tool / Bridge (needs a paid plan) → local files.
- You: confirm whether the Proton account is paid (determines option 2) and how
  far back the web session can page.

### Outlook / Hotmail — Thunderbird sync (OAuth handled by the client)
- Microsoft removed simple IMAP passwords for personal accounts (OAuth2 only), so
  scripts can't log in directly. Cleanest path:
  1. You: install Thunderbird, add the Outlook account (it does the OAuth dance in
     a browser window), let it download all mail, then close it.
  2. Me: read Thunderbird's local mbox files directly from its profile folder.
- Thunderbird can also host the Gmail account if Takeout proves annoying — one
  tool for both.

## Processing pipeline (my side, all local)

1. **Ingest**: parse mbox/EML → one SQLite corpus DB (schema mirrors mail.db:
   subject, from, date, body_html, provider, account).
2. **Normalize**: run the existing `extract.py` cleaning (same code path the
   pipeline uses — training data must look exactly like inference data).
3. **Dedupe**: hash on (from, subject, body prefix); newsletters repeat.
4. **Decontaminate**: drop the 32 eval emails (10 train + 22 validation) by
   subject match — non-negotiable, keeps our benchmark honest.
5. **Privacy pass**: drop emails from human correspondents by default (personal
   conversations are not needed — the pipeline targets automated/marketing mail);
   configurable allowlist/blocklist of senders and folders you specify.
6. **Stratify + report**: category counts (marketing / notification / transactional
   / personal / spam) so we can see class balance before annotation begins.

## Key details I need from you before starting

1. Which accounts exactly (how many Gmail / Outlook addresses)? Rough total volume?
2. Folders in scope: Inbox only? Include Promotions/Updates tabs? Include Spam
   (useful for the marketing class) or exclude? Sent mail is NOT needed.
3. Date range: everything, or last N years?
4. Exclusions: any senders/folders/topics to keep out of the corpus entirely
   (e.g. medical, legal, work)? The privacy pass will honor these.
5. Is the Proton account paid (Bridge/Export eligibility)?
6. Disk: exports can be GBs. C: has ~2.5GB free — is there another drive, or
   should I add a cleanup step (extract text, discard raw exports) as we go?

## Found-data sources (added 2026-07-15 after research)

Tiered by provenance ethics; use tier A and C, skip B:

- **A. Officially released archives:**
  - Epstein files via jmail.world — 1M+ emails from real personal Gmail/Yahoo
    accounts, congressional release (EFTA), has a Data API (jmail.world/docs).
    Best real personal-inbox source found; sample via API before committing.
  - Clinton FOIA emails (~30k, work-mail genre), Enron (already planned).
- **B. Leaked/hacked (Podesta, Sony, Hacking Team) — SKIP:** stolen private mail,
  no legal release process, and tier A already exceeds annotation capacity.
- **C. Public-by-design disposable inboxes (Mailinator, Guerrilla Mail,
  maildrop.cc):** publicly readable throwaway inboxes full of signup
  confirmations / verification codes / password resets — the transactional genre
  no archive has. Ephemeral: passive collection over days, modest volume, check
  ToS. Would shrink the synthetic share of the transactional class.
- Marketing archives (Milled ~38M, ReallyGoodEmails ~19k categorized) per earlier
  research — modest rate-limited sampling only.

## Explicitly out of scope

- I never enter or store account passwords/credentials; all sign-ins are yours.
- Training data never includes the eval emails.
- Nothing leaves this machine except the final anonymized-enough training JSONL
  you upload to Colab yourself (and we review a sample together first).

Status: PLANNED — waiting on the key details above.
