# External resources and AI-use inventory
This is a factual preparation note for the official technology declaration. It is not a signed declaration and does not establish licensing compliance or organizer approval.

## Application and development resources
| Resource | Observed use | Declaration action |
| --- | --- | --- |
| Python 3.12 | Application/runtime language | Record runtime and Python Software Foundation license |
| FastAPI 0.159.1 / Pydantic 2.14.1 | API and validation | MIT licenses; confirm final deployed versions |
| Uvicorn 0.54.0 / Starlette 1.9.0 | Server / web framework | BSD-3-Clause; confirm final deployed versions |
| python-multipart 0.0.32 | Upload parsing | Apache-2.0 |
| openpyxl 3.1.5 | XLSX reading | MIT |
| NumPy 2.5.4 | Numerical computing and custom Ridge | Preserve bundled license notices; observed metadata lists BSD-3-Clause, 0BSD, MIT, Zlib and CC0-1.0 |
| XGBoost 3.4.1 | CPU forecasting trained on team synthetic data | Apache-2.0; self-trained model, not a GenAI service |
| SQLite | Local data persistence | SQLite public-domain dedication; cloud durability remains open |
| Replit | Development environment and public hosting | Record actual plan, region, deployment URL and proof; free-plan expiry must be checked |
| GitHub | Source control and review | Repo private; arrange judge access |
| OpenAI ChatGPT/Codex | Code, debugging, documentation and design assistance | Disclose substantial assistance; exact model/version per contribution not fully recorded, do not guess |
| OpenAI image generation | Earlier interface concept/reference artwork | Identify any generated images actually used; current food hero is an external photograph |
| Replit Agent | Setup and attempted frontend/deployment assistance | Record actual outcomes; quota exhaustion caused incomplete tasks; requests alone are not completed work |
| Cloudflare Quick Tunnel | Earlier temporary synthetic preview only | Not production hosting; not needed for the Replit public site |
| Ruff / unittest / HTTPX and other dependency tools | Quality checks and testing | Include material tools in the final inventory; requirements/lockfiles are the version source |

Licenses above were checked against the available local package metadata during this audit. They are not a guarantee that the final cloud environment has identical transitive versions. Reconcile `backend/requirements.txt`, `requirements.lock.txt`, `pyproject.toml` and `uv.lock` before final declaration; do not modify them merely to match prose.

## Models and datasets
The application uses a team-implemented historical baseline, a custom Ridge estimator and XGBoost models trained on fictional cafeteria records. No runtime LLM/GenAI, remote inference endpoint or pretrained foundation model is present in the audited main implementation.

Declare the synthetic dataset, generator, seed, date span, feature assumptions, model-selection procedure and evaluation limitations. The historical comparison reused a previously inspected period. Do not call the final full-data model independently tested, WAPE an accuracy rate, or simulated savings actual business impact.

The local dataset and reports are generated artifacts, not a reason to upload a SQLite database or a multi-megabyte model to GitHub. Provide reproducible generation and, if useful, a small clearly labelled synthetic demo file after review.

## External visual/reference material
The English UI redesign uses:
- DM Sans and Libre Caslon Display from Google Fonts. Check and retain their applicable font-license notices for the final distributed assets.
- An Unsplash food photograph served from `https://images.unsplash.com/photo-1512058564366-18510be2db19`. Record the original photo/creator and applicable use terms before final submission; the image CDN address alone is incomplete attribution.
- METMalaysia's climate explanation as qualitative simulator background, not a weather-data feed.

Earlier AI-created concepts influenced design. Do not state that the food photograph was created by the team or that generated reference concepts are implemented screenshots. Identify any additional libraries/CDNs/assets used in the final release.

## Sponsor resources
The organizer-linked [submission sample](https://github.com/michaelzhngg/SDC_Hackathon_Submission_Template) marks Replit and RunPod use sections as required. Replit hosting is verified. A RunPod voucher email exists, but no RunPod endpoint, authenticated workload or integration was found in the audited code or public API. Do not disclose voucher codes, keys, billing records or credential screenshots.

Before submission, complete genuine documented RunPod use suited to the project or confirm an explicit exception with organizers. Do not add a fake endpoint or an unnecessary GenAI call merely to imitate example text. No live Orbyte platform, sandbox or customer data was provided or is claimed.

## Privacy and people
Use synthetic-only business records in the public demo. The current app has no login or role enforcement, so do not describe it as protecting real restaurant data. Document intended least-privilege access, human approval, retention/deletion and tenant separation as future controls unless implemented.

Team leaders must confirm member details, workshop participation, individual contributions, prior-owned work, any pre-event approval, IP restrictions and signatures. Never infer approval from silence. The Handbook requires declaration of pre-hackathon materials; it treats AI-generated material created during the hacking period under AI-use rules instead of automatically classifying it as prior work.

## Team review needed
The team should review and explain the code, data leakage controls, baseline/model choice, prep rounding, errors, storage and deployment. Mark all AI assistance accurately, specify the extent of use, and state what the team actually tested or adapted. Do not sign an assertion that every AI output was reviewed unless that review has happened.

Sources: [Official Handbook, section 8](https://drive.google.com/file/d/1vDGxSLufFrE9h6T8-KY1ltxmAgQln23k/view), [official template resources](https://drive.google.com/drive/folders/1xw7c2aN8N-at8hPEULzkcU76e_FFb0Ef), [Domain 2 brief](https://drive.google.com/file/d/11wqbeO-HYep-DJPQ-LPZnrZfQvCgr5BU/view).
