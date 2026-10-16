# Implementation notes

## 1. Approach

I chose a standard-library Python batch gate: explicit rules for structured data, reviewed text patterns for the supplied brand policies, and English clarification templates. It checks all 30 briefs with 19 passes and 11 blocks. The 22 tests cover those outcomes, altered inputs and command execution. Each result records reasons, owner, product matches, approvals and usage before/after.

## 2. Tool per job

| Job | Tool | Reason |
|---|---|---|
| Dates, counts, status and quota | Code | Exact calculations; cheapest reliable level. |
| Products and approvals | Code | Exact catalog matches and explicit authority checks. |
| Supplied brand rules | Code | Small reviewed policy set; unknown rule strings block for review. |
| Clarification messages | Templates | Consistent wording tied to detected issues. |
| Assignment and status changes | Native ClickUp, proposed | Existing workflow actions avoid custom delivery code. |
| Ambiguous language | Creative Lead review | Patterns cannot interpret arbitrary wording; no model fallback implemented. |
| Frontier model or Grok Bot | Not selected | No justified multi-tool judgment task remains in this implementation. |

## 3. LLM usage and monthly cost

**No runtime LLM; model cost is $0.** Using the exercise’s estimates, 400 briefs/month cost approximately $0 incremental compute on the existing stack. Two proposed native actions per brief mean about 800 actions before retries, subject to the remaining shared 10,000 allowance. Subscriptions, development and human review are excluded.

| Comparison only | 400 shared checks | Six duplicated checks per brief |
|---|---:|---:|
| Current code | ~$0 | ~$0 compute |
| Cheap model at $0.001/call | $0.40 | $2.40 |
| Frontier at $0.02–$0.10/call | $8–$40 | $48–$240 |
| Grok at $0.10–$0.50/run | $40–$200 | $240–$1,200 |

Run one shared gate; lead bots read its result. These comparisons assume one call per check, without retries. If broader semantics are needed, evaluate a small model on ambiguous wording; keep arithmetic and authority in code.

## 4. Where it should live

The delivered tool runs locally. Proposed deployment: an authenticated Vercel function checks intake before `Queued`; Supabase stores versioned decisions and quota reservations; native ClickUp actions apply validated changes. Studio changes or generation are unnecessary.

A live system needs a transaction/lock per client-month, unique brief/version keys, atomic reservation replacement on recheck, and retry-safe action delivery. The local batch restarts from the supplied snapshot; it does not persist reservations. Historical passes should not be displaced by backdated requests.

The Squad Lead reviews clarification drafts within the two-hour reply SLA and seeks same-day clarification. The Creative Lead resolves brand ambiguity; finance controls reactivation. Recheck updates before production. Monitor overturned blocks, missed claims, stale usage, duplicate events, unknown policies and delivery lag.

## 5. Assumptions

- Fixed UTC check time: Oct 13, 2026, 09:00. Monday–Friday, no holidays, today is day zero. Static earliest date: Oct 16; any video: Oct 20. Rush cannot fix a past date.
- Valid input shapes are required. Malformed configuration/identities abort; missing business information blocks. Fixture author names are trusted; production needs authenticated user IDs.
- Counts are totals, not multiplied by platform/format; nonnegative integers with a nonzero total. Static/video quotas are separate, and exact limits pass. No extra TikTok restriction is assumed.
- Usage belongs to the check month and excludes this batch. Only passes reserve quota. Overage applies to that brief and increases usage, not the plan; zero new units of an already-over-limit type do not block.
- Approval comments must be between creation and evaluation, from the configured lead, with explicit leading approval wording. Questions/conditions do not approve. Latest recognized decision wins, including revoked or reduced scope. Explicit quantities must cover the request; arbitrary contract wording is unsupported.
- Products match normalized SKU/name/alias, optionally removing a leading English article; no fuzzy guesses. Unknown, ambiguous or inactive products block. `brand` permits brand-only work.
- Assets require an HTTPS Drive reference or a positive Studio catalog instruction/flag. Conflicting negative instructions do not grant permission. Images, access and availability are not checked.
- Formats use positive ratios and optional integer seconds. Every video-only format needs duration; mixed briefs may combine plain static ratios and timed video ratios without per-deliverable mapping.
- Title, copy direction and notes are creative content; comments are approval evidence. Word boundaries avoid matching `cure` inside `curated`; supplied Portuguese claims are checked. General negation/paraphrase understanding is not claimed.
- Northpeak’s packaging rule is a standing instruction; explicit cup-led BR-03 needs clarification. BR-29’s superlative requires evidence/replacement. Unknown Brain strings block for review.
- Numeric percentages count as discounts only with explicit discount wording. Material percentages are excluded; spelled-out or stacked offers need interpretation.
- No release/substantiation registry is supplied. Child imagery triggers review under that policy. Account and claims restrictions cannot be waived by rush/overage approval.

No live integrations, automatic client messaging or UI were added. Before rollout, validate real language cases, identity, concurrent reservations and atomic report/action delivery.
