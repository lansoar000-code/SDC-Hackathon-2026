# Competition readiness and remaining work
Audit date: 2026-10-24 (UTC+8). This is a requirements/status tracker, not a completed competition proposal.

## Authoritative sources
1. [Domain 2 problem statement and preliminary rubric](https://drive.google.com/file/d/11wqbeO-HYep-DJPQ-LPZnrZfQvCgr5BU/view), especially What to Build, Must-Have Features, Rules and Boundaries, Support and Data, and Marking Rubric.
2. [Official Handbook](https://drive.google.com/file/d/1vDGxSLufFrE9h6T8-KY1ltxmAgQln23k/view), especially sections 7.4 and 8.
3. [Phase 1 preliminary proposal template](https://drive.google.com/file/d/1jNjuMJfhMYjo3qQw_PmmeGM-INEwuleo/view).
4. [Organizer-linked GitHub submission sample](https://github.com/michaelzhngg/SDC_Hackathon_Submission_Template), including its README checklist and submission examples.
5. [Official participant resources](https://drive.google.com/drive/folders/1xw7c2aN8N-at8hPEULzkcU76e_FFb0Ef).

The proposal template states **25 October 2026** as the preliminary submission deadline. An exact submission time/timezone and any later Discord/portal updates have not been verified. Check those channels before relying on a cutoff time. Do not infer an extension from an outage or a failed deployment.

## What the preliminary round requires
The Domain 2 brief requires a rough working version of the most important feature, shown live and backed by an accessible GitHub repository. The proposal must explain the complete final journey and all six must-have features. The brief describes trigger -> connected data -> decision logic -> human approval -> visible outcome with an activity record; identity, profiles and RBAC may be simulated. Live Orbyte access is not required.

The Handbook also requires a working technical prototype, a functional UI and a live presentation/pitch. The official sample lists a pitch-deck link, demo-video link, preliminary PDF, technology declaration, Replit proof and RunPod proof. Its Replit and RunPod sections are explicitly marked required. The proof PDFs themselves are **EXAMPLE ONLY**, not evidence of this team's use. Confirm any permitted sponsor-use exception with organizers; the domain brief's freedom to choose an MVP does not by itself waive the submission sample's sponsor checklist.

Do not copy the sample's GPU architecture into the submission as an implemented PrepWise capability. The current project runs CPU forecasting and has no verified RunPod integration.

## Requirements-to-evidence matrix
| Requirement | Verified current status | Remaining work |
| --- | --- | --- |
| One specific SME burden | Prep quantities for small restaurants; functioning forecasting workflow | Explain the Malaysian SME user and recurring planning task in the proposal |
| Trigger and connected data | Manual request plus validated CSV/XLSX sales history | Describe the Orbyte event/API assumptions; a scheduled trigger is optional |
| Rules/AI decision logic | Baseline/Ridge/XGBoost selection and operator-set buffer | Load and demonstrate a matching synthetic dataset/model on the live site |
| Accuracy and ease of learning | Validation and per-dish method labels; earlier regression evidence | Record a short new-user workflow and measure time/steps under a stated protocol |
| Human control | Operator can choose inputs and buffer | Implement or explicitly simulate who can approve a consequential final plan, and demonstrate it |
| Permissions and activity record | Saved prediction snapshots, no roles or approval state | Add simulated role boundaries plus actor, action, timestamp and approval/outcome records; history alone is not enough |
| Orbyte fit and multi-SME reuse | Architecture can be explained as a reusable forecasting service | Document hub integration, ownership/permission boundary and how multiple SMEs would be separated; label proposed parts |
| Business benefit and SDG | SDG 8.2/8.3 are appropriate primary targets; waste benefit is a hypothesis | State numeric baseline, measurable KPI and realistic Phase 2 target with sources/assumptions |
| Synthetic-only data | Generator, labelled IDs/names and isolated local artifacts exist | Seed the live demo with reviewed team-created synthetic data only; no real personal/customer/company records |
| Working UI and public demo | English redesign at the Replit public URL; health responded successfully | Rehearse the selected use case, confirm mobile access and have a video fallback |
| Matching repository | Repo private; frontend PR #1 remains open | Merge/reconcile the final app and production startup configuration, identify a tested revision, and grant judges access |
| Major-resource/AI declaration | Resource inventory now documented | Complete official signed technology declaration with team-confirmed details |
| Required submission materials | Team confirmed on 2026-10-24 that these are not finished | Complete PDFs and provide deck/video links; no placeholder counts as a final submission |
| Deployment continuity | Replit publication confirmed | Check free-plan expiry and durable data/model storage across restart/republish; this is not yet verified |
| Team understanding and prior work | Earlier related work is mentioned in project history | Review every major component, confirm contribution details, and declare pre-hackathon materials/approval status accurately |

## Prioritized work
### P0 - before preliminary submission
- Complete the official preliminary proposal and technology declaration, including all team fields, citations, permitted word counts, signatures and dates. The documentation in this repository does not replace them.
- Prepare truthful Replit and RunPod proof of use. Replit hosting is evidenced; RunPod execution is not. A voucher receipt is not an endpoint or completed workload. Implement an appropriate genuine use or obtain an explicit organizer-approved alternative; do not invent it.
- Make the submitted code match the demo. Frontend PR #1 is unmerged, and the production startup fix was made in Replit; its synchronization back to GitHub is unverified. Do not merge outdated deployment configuration blindly.
- Grant judges repository access or explicitly review a public release. Current private status is a submission access risk, not a reason to publish personal information or secrets.
- Prepare a representative labelled synthetic dataset on the live site and verify model mode. Health showed 0 sales / 0 dates / training not ready; model status showed untrained at this audit.
- Demonstrate an understandable approval/role/activity-record path, at least simulated. Clearly separate implemented functions from final-stage plans.
- Finish the pitch deck and demo video links; rehearse the primary journey and failure fallback.
- Confirm the exact deadline/time, submission portal, current organizer announcements and required workshop completion.

### P1 - reliability and evidence
- Persist the dataset and model on appropriate durable storage; test recovery and republishing without touching the only copy of a submission dataset.
- Measure planning time/steps and forecast error against a stated baseline. A waste-reduction target is not an achieved impact.
- Capture screenshots of the actual application, deployment and sponsor workload; remove keys, tokens and account/private details from proof.
- Close gaps in data/PDPA principles, role permissions, multi-SME reuse and exception handoff. This is a synthetic prototype, not a claim of legal compliance.

### P2 - optional improvements
Owner/staff usability feedback, automatic schedules, richer explanations and a business model can strengthen the pitch. A real-data accuracy study, production identity platform, live Orbyte account and broad inventory system are not prerequisites imposed by this brief. Keep the demo focused on one complete SME task.

## Proposal format and word limits
The official preliminary template requires a single PDF named `SDC2026_TeamName_Preliminary.pdf`, replacing TeamName consistently:
- Team/project overview.
- Problem context: maximum 250 words.
- Proposed AI solution: maximum 300 words.
- Conceptual technology stack and a simple block diagram; disclose actual sponsor use.
- Design-thinking/deployment strategy: maximum 200 words.
- Exact SDG sub-target, numeric problem baseline, core measurable KPI and percentage-based Phase 2 impact target; cite sources or clearly identify estimates.
- Readiness/workshop checklist; prior-owned work, third-party resources and employment-IP declarations; leader signature/date.

The technology declaration has separate limits, including architecture 200 words, AI-output review 100, sponsor replaceability 100, data/privacy 150 and limitations 150. Use the official forms and complete non-applicable fields as No/None.

## Preliminary scoring priorities
| Criterion | Weight |
| --- | ---: |
| Innovation and Creativity | 30% |
| Problem-Solution Fit | 25% |
| Feasibility of Build | 25% |
| Clarity of Proposal | 20% |

Source: Domain 2 preliminary rubric. Final-round scoring is different and has not been supplied here.

## Audit boundaries
No repository visibility was changed, no production data was written, no approval workflow was implemented, no sponsor account was configured and no official form was signed or submitted by this cleanup. Team membership, workshop attendance, prior-work approval, private IP matters and definitive licensing/rights attestations require team confirmation. The audit reports evidence and gaps rather than declaring eligibility.
