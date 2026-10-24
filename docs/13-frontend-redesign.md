# PrepWise frontend redesign

Source: lansoar000-code/SDC-Hackathon-2026, main commit 6d7f48fe1d775844c5306b37498cd019fea5eb71.

The reference layout is implemented as a forest-green sidebar, warm cream dashboard, food hero, serving summaries, dish prep grid and a demand chart. All fixed interface copy is English. Existing user-entered names remain native data; a small display-only mapping covers the dishes named in the reference. Backend-owned messages are translated for display without modifying their payloads.

The existing API paths, HTTP methods, forecast parameters, training rules, model selection and CSV contents are preserved. The duplicate pasted chart module in main's script.js and duplicated inline sample chart are removed so the page can initialize. The demand chart aggregates only the matched comparisons returned by /api/reports/metrics. Empty data is shown as empty; simulated and synthetic results remain labelled.

The third summary displays extra prep servings, derived from the existing forecast response. The reference's inventory shortage count cannot be derived from this branch's API. No stock count or procurement workflow is fabricated; existing sales feedback remains accessible in the sidebar.

Validation:
- 25 existing repository regression tests passed against an isolated copy of the same GitHub backend.
- Node syntax checks passed for all six frontend JavaScript modules.
- Browser: simulated forecast, CSV import (126 synthetic rows / 42 dates), model training, historical forecast with prep buffer, sales feedback, history detail, CSV download, empty-history error handling and demand chart.
- Browser console: no errors observed during these flows.
- Desktop and 390px responsive checks: no document horizontal overflow.
- Visible page text in the checked synthetic-data scenario contained no Chinese characters.
- Test data exists only in the local .preview database. It is not included in the GitHub change.

External presentation assets: Google Fonts (DM Sans, Libre Caslon Display) and a rice photograph served by Unsplash at https://images.unsplash.com/photo-1512058564366-18510be2db19 . System fonts and the cream background remain as fallbacks if external assets cannot load.

Replit has not been edited or synchronized by this work. Import or pull the resulting GitHub branch into the existing Replit project, retain its existing runtime/environment configuration, and run it to verify that environment before publishing.
