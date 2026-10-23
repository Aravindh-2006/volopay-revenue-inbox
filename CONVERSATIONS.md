# Conversations Inventory

This document provides a complete inventory of the 44 records in the Revenue Intelligence Inbox Revenue Intelligence dataset across the initial batch (`data/01_initial.json`) and update batch (`data/02_update.json`).

---

## 1. Summary Statistics

- **Total Unique Records**: 44
  - **Calls**: 24 (`B01`–`B20`, `C01`–`C04`)
  - **Meetings**: 20 (`M01`–`M20`)
- **Usable Transcripts**:
  - Initial Batch (`01_initial.json`): 22 records with transcripts (50.0% coverage)
  - After Update Batch (`02_update.json`): 23 records with transcripts (52.3% coverage; adds M07)
- **Active Reps**: `U101`, `U102`, `U103`, `U104`, `U105`

---

## 2. Calls Breakdown (24 Records)

### Campaign Calls: B01 to B20
- **Source**: Outbound automated dialer campaign run by rep `U101`.
- **Connects vs Voicemails**:
  - Connected with real conversation: `B03`, `B07`, `B12`, `B18` (4 calls). Transcripts captured.
  - Voicemail / No Answer: 16 calls (80%). Duration < 30s. No transcript.
- **Routing**: Connected calls are classified into `Follow-Up / Nurture` or `New Prospect Outreach`. Unanswered calls route to `No Conversation`.

### Ad-hoc Direct Calls: C01 to C04
- **C01**: Inbound call from partner lead. Usable transcript present.
- **C02**: Outbound check-in with existing client. Usable transcript present.
- **C03**: Follow-up call regarding pilot deployment. Usable transcript present.
- **C04**: Brief missed call / voicemail. No transcript.

---

## 3. Meetings Breakdown (20 Records)

| ID | Title | Host | Transcript Status | Key Discussion Topic |
|----|-------|------|-------------------|----------------------|
| **M01** | Harborpath Advisory Sync | U101 | Available | Referral fee structure, 15% revenue share, advisory co-selling. |
| **M02** | Weekly Sales Standup | U102 | Available | Internal pipeline review, quota attainment. |
| **M03** | Product Demo - FinPeak | U103 | Available | Enterprise card management, multi-entity approval demo. |
| **M04** | Cedarwave Account Review | U104 | Available | **Churn Risk**: Frustration over physical card migration delays. |
| **M05** | Tech Vendor Evaluation | U105 | Available | Revenue Intelligence Inbox evaluating a new compliance & KYC provider. |
| **M06** | Discovery Call - Apex Corp | U101 | Available | Discovery on expense reporting pain points. |
| **M07** | **Executive Intro - Crestline** | **U102** | **Initial: Pending / Missing<br>Update: Available (Rev 2)** | Strategic enterprise overview and multi-currency billing. |
| **M08** | Customer Success Handoff | U103 | Available | Handoff of newly closed account to CS rep. |
| **M09** | Quarterly Business Review | U104 | Available | Spend review with Tier-1 enterprise account. |
| **M10** | Partner Enablement | U101 | Available | Training accounting partner on portal features. |
| **M11** | Cold Prospect Connect | U102 | Unavailable (`recording_disabled`) | Scheduled discovery call; recording was disabled by client. |
| **M12** | Contract Negotiation | U103 | Available | Discussion on annual payment discounts and SLA terms. |
| **M13** | Supplier Demo - TravelDesk | U105 | Available | Evaluating TravelDesk corporate travel integration. |
| **M14** | Architecture Review | U102 | Unavailable (`processing_pending`) | Technical integration call. |
| **M15** | Renewal Discussion | U104 | Available | Contract renewal and seat expansion. |
| **M16** | Mid-Market Intro Call | U101 | Available | First introductory call with CFO. |
| **M17** | Pricing Discussion | U103 | Available | Custom interchange pricing and volume tiers. |
| **M18** | Churn Prevention Call | U104 | Available | Addressing customer concerns regarding UI responsiveness. |
| **M19** | Candidate Interview | U102 | Unavailable (`confidential`) | Sales engineer interview (confidential HR policy). |
| **M20** | Wrap-up & Next Steps | U101 | Available | Closing next steps after POC completion. |

---

## 4. Notable Findings & Strategic Insights

1. **Harborpath Partnership (M01)**: Concrete partnership negotiation with exact quotes on revenue sharing.
2. **Cedarwave Churn Threat (M04)**: Urgent account issue requiring immediate intervention by leadership.
3. **Outbound Campaign Efficiency (B01–B20)**: Low connect rate (20%) highlighting need for cadence adjustments.
4. **M07 Update Dynamics**: M07 demonstrates the full lifecycle: ingestion without transcript $\rightarrow$ analysis $\rightarrow$ late transcript arrival $\rightarrow$ revision update $\rightarrow$ freshness recalculation.
