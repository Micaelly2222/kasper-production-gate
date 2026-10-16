# Option C — Squad health design

**Approach.** Produce weekly squad summaries for founders and private individual reports for each person’s Squad Lead for Sep 14–Oct 11. Every flag includes evidence, its calculation and a proposed follow-up. These are support signals, not rankings or burnout diagnoses.

**Calculations.** Count each task once in the UTC Monday–Sunday week of its first `Sent to Client`. It is late if that UTC date exceeds `due_date`. On-time rate is on-time tasks/all first sends; no deliveries means N/A. Adjust capacity by weekdays, employment dates, inclusive PTO and ramp-up: Mello 7 points/week, Nathalia 50% from Sep 21 for four weeks, Lucas’s vacation and Dora’s sick day. Exclude null lead capacities from utilization. Delivered points are throughput; queue snapshots lack incoming/queued points, so exact demand and hiring requirements need more data.

**Attribution.** Use the assignee at first send for delivered points and flag transfers. Attribute activity to the event actor in their local timezone. Provisionally use weekdays 09:00–18:00 until schedules are confirmed; count activity days, not inferred hours. Separate unattended rendering, client direction changes and internal errors. Avoid double-counting revisions from two records.

| Job | Tool | Why |
|---|---|---|
| Events, calendars and metrics | Scheduled code/Supabase | Exact, reproducible calculations. |
| Evidence and report text | Code templates | Explain every flag without model calls. |
| Approved follow-up tasks | Native ClickUp | Existing team workflow. |
| Ambiguous signals/check-ins | Squad Lead review | Context requires human judgment. |
| Frontier model/Grok Bot | Not selected | Routine scans do not justify agent costs. |

**Access and decisions.** Enforce private delivery and authenticated access; founders see aggregates. Proposed check-in triggers: >110% adjusted capacity for two weeks, outside-hours activity on ≥3 days/week, or ≥2 internal-error tasks affecting ≥20% of deliveries. Squad escalation: three consecutive queue increases with oldest age >3 days. These thresholds need validation. Squad B’s queue grows 5→9→13→18 and age 1→3→4→6: discuss coverage with Bea before an exact hiring recommendation. Danilo’s message supports a check-in; Gabi’s overnight render alone does not prove overnight labour. Localize Mello’s Lisbon activity; client changes are not Ana’s quality failures.

**Cost and first build.** Shared weekly code/model cost is approximately $0; six leads reuse results. Assume 12 approved actions/week × 4.33 = ~52 native actions/month. Subscriptions/human review excluded. Optional Grok: $0.43–$2.17 shared or $2.60–$12.99 for six weekly leads; not selected. First build the event reducer and capacity calendar; test first sends, UTC boundaries, PTO/ramp, transfers and timezones. Monitor missing data and permission failures.
