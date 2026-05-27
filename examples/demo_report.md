# AI Research Brief

**Objective:** Find onboarding and research-repository friction for product managers

## Executive summary
Across 4 participants, the strongest signal is: Participants P01, P02, P04 want faster synthesis, but not at the cost of nuance or traceability. The main product implication is to reduce the gap between raw research data and trusted, source-backed product decisions.

## Themes

### Theme 1 — Analysis needs speed without flattening nuance
**Confidence:** high
**Participants:** P01, P02, P04

**Finding:** Participants P01, P02, P04 want faster synthesis, but not at the cost of nuance or traceability.

**Evidence:**
- "I would trust AI more if it showed quote clusters, outliers, and which segments the finding came from." — P02, 00:03:09 (`P02_researcher.md`)
- "A summary is helpful, but only if I can click into the source." — P01, 00:03:43 (`P01_product_manager.md`)
- "We had five calls about onboarding, and the researcher found that people were not confused by the setup itself." — P01, 00:00:19 (`P01_product_manager.md`)
- "I remember the loudest customer, not always the most representative one." — P04, 00:01:12 (`P04_founder.md`)

**Claims:**
- **Claim:** Teams want AI to accelerate the first synthesis pass while preserving nuance.
  - **Why it matters:** Researchers still need control, but a structured draft shortens time from calls to insight.
  - **Evidence:** "I would trust AI more if it showed quote clusters, outliers, and which segments the finding came from." — P02, 00:03:09 (`P02_researcher.md`)
  - **Evidence:** "A summary is helpful, but only if I can click into the source." — P01, 00:03:43 (`P01_product_manager.md`)
  - **Evidence:** "We had five calls about onboarding, and the researcher found that people were not confused by the setup itself." — P01, 00:00:19 (`P01_product_manager.md`)

**Product opportunity:** Generate editable thematic summaries with explicit quote clusters instead of opaque paragraphs.
**Risk if ignored:** Researchers reject summaries that feel fast but shallow.
**Next research question:** What level of summary compression still preserves the nuance researchers need?

### Theme 2 — Research handoff is too lossy
**Confidence:** medium
**Participants:** P02, P05

**Finding:** Participants P02, P05 need research outputs that are easy to reuse after the study ends.

**Evidence:**
- "The research tool should notice repeated customer language and suggest who to interview next." — P05, 00:01:26 (`P05_customer_success.md`)
- "If we learned something about onboarding last quarter, the repository should surface it when a PM starts a related study." — P02, 00:04:12 (`P02_researcher.md`)
- "Product, research, and customer success should look at the same evidence instead of translating it three different ways." — P05, 00:04:19 (`P05_customer_success.md`)

**Claims:**
- **Claim:** Research only stays valuable when teams can rediscover the decision and source evidence later.
  - **Why it matters:** A living evidence trail prevents old learning from disappearing into decks and docs.
  - **Evidence:** "The research tool should notice repeated customer language and suggest who to interview next." — P05, 00:01:26 (`P05_customer_success.md`)
  - **Evidence:** "If we learned something about onboarding last quarter, the repository should surface it when a PM starts a related study." — P02, 00:04:12 (`P02_researcher.md`)
  - **Evidence:** "Product, research, and customer success should look at the same evidence instead of translating it three different ways." — P05, 00:04:19 (`P05_customer_success.md`)

**Product opportunity:** Create durable insight cards that preserve source context and can be rediscovered later.
**Risk if ignored:** Insights disappear into old decks and are not reused in future decisions.
**Next research question:** When do teams search old research, and what metadata helps them trust what they find?

### Theme 3 — Insights must land inside product workflows
**Confidence:** medium
**Participants:** P02, P05

**Finding:** Participants P02, P05 want insights to connect directly to roadmap and product workflows.

**Evidence:**
- "One participant can love a workflow while another finds the same workflow risky." — P02, 00:01:20 (`P02_researcher.md`)
- "We hear patterns before product does, but our notes are scattered across tickets, calls, and Slack." — P05, 00:00:20 (`P05_customer_success.md`)

**Claims:**
- **Claim:** Insights need to travel into roadmap and planning workflows, not stop at a report.
  - **Why it matters:** A synthesis tool creates more value when it changes what the team builds next.
  - **Evidence:** "One participant can love a workflow while another finds the same workflow risky." — P02, 00:01:20 (`P02_researcher.md`)
  - **Evidence:** "We hear patterns before product does, but our notes are scattered across tickets, calls, and Slack." — P05, 00:00:20 (`P05_customer_success.md`)

**Product opportunity:** Push research-backed recommendations into planning rituals where product decisions happen.
**Risk if ignored:** Good research arrives too late or too disconnected to influence roadmap choices.
**Next research question:** Where should an insight appear so it changes a product decision instead of becoming documentation?

## Claim-to-evidence map

| Theme | Claim | Why it matters | Evidence |
|---|---|---|---|
| Analysis needs speed without flattening nuance | Teams want AI to accelerate the first synthesis pass while preserving nuance. | Researchers still need control, but a structured draft shortens time from calls to insight. | "I would trust AI more if it showed quote clusters, outliers, and which segments the finding came from." — P02, 00:03:09 (`P02_researcher.md`)<br>"A summary is helpful, but only if I can click into the source." — P01, 00:03:43 (`P01_product_manager.md`)<br>"We had five calls about onboarding, and the researcher found that people were not confused by the setup itself." — P01, 00:00:19 (`P01_product_manager.md`) |
| Research handoff is too lossy | Research only stays valuable when teams can rediscover the decision and source evidence later. | A living evidence trail prevents old learning from disappearing into decks and docs. | "The research tool should notice repeated customer language and suggest who to interview next." — P05, 00:01:26 (`P05_customer_success.md`)<br>"If we learned something about onboarding last quarter, the repository should surface it when a PM starts a related study." — P02, 00:04:12 (`P02_researcher.md`)<br>"Product, research, and customer success should look at the same evidence instead of translating it three different ways." — P05, 00:04:19 (`P05_customer_success.md`) |
| Insights must land inside product workflows | Insights need to travel into roadmap and planning workflows, not stop at a report. | A synthesis tool creates more value when it changes what the team builds next. | "One participant can love a workflow while another finds the same workflow risky." — P02, 00:01:20 (`P02_researcher.md`)<br>"We hear patterns before product does, but our notes are scattered across tickets, calls, and Slack." — P05, 00:00:20 (`P05_customer_success.md`) |

## Surprising quotes

- "A summary is helpful, but only if I can click into the source." — P01, 00:03:43 (`P01_product_manager.md`)
- "One participant can love a workflow while another finds the same workflow risky." — P02, 00:01:20 (`P02_researcher.md`)
- "Give me a concise insight card with confidence, quotes, and the recommended product bet." — P01, 00:04:27 (`P01_product_manager.md`)

## Recommended next steps

- Prototype insight cards that pair one-sentence findings with clickable quote evidence.
- Add a researcher review step so AI output is fast but still accountable.
- Expose confidence, source coverage, and quote diversity on each generated summary.
- Pilot integrations that push synthesized insights into planning docs or issue trackers.

## Automated eval checks

- **groundedness:** 1.0
- **source_coverage:** 0.8
- **theme_redundancy:** 0.044
- **claim_evidence_coverage:** 1.0
- **multi_source_theme_rate:** 1.0
