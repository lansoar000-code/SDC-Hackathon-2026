# Plan approval prototype

The existing prep result gains one Approve plan button and a short status. There are no name fields, role selectors or new dashboard panels. Once approved, the existing CSV link downloads the final approved quantities. Reopening a saved forecast restores its approval state.

Approval uses a simulated owner identity for one demo restaurant. The actor header and role switch API are not authentication, and do not provide tenant isolation. Use synthetic data only. Orbyte integration remains a proposed connection, not a live integration.

The server saves a separate final plan, revision, approval timestamp and append-only application events in SQLite. Original predictions and existing prediction APIs are unchanged. Pending plans cannot export a final CSV. Approved plans cannot be edited or approved again. Historical suggestion exports remain available through the existing API and are not approval records.

The new routes expose status, review creation/detail/list, version-checked draft edits, owner approval and final CSV export. Draft editing and demo actors are API capabilities only; this minimal UI has no adjustment or identity fields.

For an existing deployment, add the router module and initialization to the current app without replacing unrelated routes, database schema, UI files, model artifacts or data. Republish only after verifying the resulting integration and preserving durable data.

Validation: 8 approval regression cases; 33 tests against the GitHub-compatible backend; 39 tests against the local backend including inventory. Browser checks cover demo generation, approval, locked state, reload and reopening history. Role enforcement applies only to the declared simulated identities, not to authenticated users.
