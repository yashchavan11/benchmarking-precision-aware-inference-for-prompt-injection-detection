# Session history

Chronological record of substantive implementation, investigation, experiments and analysis.
The latest resumable state is in [STATUS.md](STATUS.md); this file preserves how that state
was reached. No research sessions are recorded yet.

## Entry schema

Session IDs have the form `S-YYYYMMDD-NN`, unique across the team. The date/time field states
the actual timezone; the ID alone does not establish when work occurred. The following is
an unfilled schema, not a completed session.

### S-[date]-[sequence] — [short goal]

- **Date/time and timezone:** [actual start/end or date]
- **Contributor(s) / reviewer if any:** [actual names]
- **Phase:** [P1-A through P2-E, or F]
- **Starting context:** [prior session/phase closeout and relevant decision/evidence IDs]
- **Intended goal:** [bounded purpose]
- **Work actually performed:** [actions and project changes]
- **Changed files or artifacts:** [relative paths or durable locations; versions/hashes where relevant]
- **Observations:** [facts supported by linked run or validation records]
- **Interpretation and hypotheses:** [possible explanations, distinguished from observations]
- **Checks and outcomes:** [validation IDs, conditions and what the checks establish; a process exit status alone is not scientific validation]
- **Decisions made or proposed:** [decision IDs and accepted/proposed status]
- **Data exposure:** [splits, kind of inspection and DATA_REGISTRY exposure-entry reference]
- **Failed or abandoned attempts:** [what was tried, why it stopped and reusable lessons]
- **Effect on previous work:** [unaffected / potentially affected / invalidated, with record IDs]
- **Unresolved issues:** [question IDs and next investigation]
- **Ownership transition:** [who may proceed and concurrent work to preserve]
- **Next bounded action:** [task and required evidence, summarized in the current STATUS]
- **Records updated:** [affected canonical record IDs/paths]
- **Session outcome:** [complete / interrupted / blocked; incomplete work remains explicitly identified]

## History semantics

Entries reference the authoritative decision/run/result records rather than reproducing
their complete contents. Related actions can share one substantive entry; the history is
not a command transcript. A later correction references the earlier entry and explains
what changed, preserving failed attempts and their lessons. Typographical corrections may
be made in place when meaning is unchanged. Ending a session does not establish that its
task or research phase is complete.
