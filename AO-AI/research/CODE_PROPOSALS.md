# AΩ | AI — Autonomous Executable Code Proposals

## Implemented: source generation, not unattended deployment

AΩ can generate executable Python source files from evolving combinations
of a strictly bounded set of research-method components. This is
deterministic program synthesis, NOT an unrestricted AI agent that
invented wholly new algorithms or improves itself generally.

The separate GitHub workflow ao-ai-code-proposals.yml runs every four
hours on a best-effort schedule during 2026-11-06 to 2027-05-06 UTC.
No user login is needed.

### Each proposal cycle

1. Load the last PROMOTED research champion as schema-validated JSON from
   the previous successful experiment; never execute prior artifacts.
   If no candidate has passed all gates, begin without a champion.
2. Train-select a new structural method using human-defined components.
3. Evaluate it on disjoint synthetic holdout cases against an established
   baseline selected on training cases only.
4. Generate an actual standalone Python program implementing the selected
   scoring, exploration, anchor and candidate-proposal logic.
5. In a separate process, check source byte-for-byte against the trusted
   whitelist compiler and execute 30 paired conformance tests across
   five synthetic regimes. Reject any discrepancy or invalid budgets.
6. Run a second, stricter qualification on 1,000 fresh synthetic cases,
   five seeds and five regimes, against both established baselines and
   the previous champion. Require a >5pp advantage, positive 95% paired
   CI lower bound, nonnegative effect in every regime, no false Pareto
   claims or budget violations, and candidate CPU time within 1.5x
   each comparator.
7. If ALL tests pass, remember only the newly selected JSON recipe as
   the next research champion; otherwise carry forward the previous
   champion without overwriting it. No source merge or deployment.
8. Archive the Python source, SHA256, full verification.json,
   champion.json and cycle.json, including negative results.
9. Repeat automatically with fresh examples and the last accepted champion.

### Strict controls

- GitHub has contents:read, actions:read only; no code commits, merges,
  pull requests, deployments or write credentials.
- The source is generated ONLY from whitelisted components, not from
  arbitrary model-provided strings, plugins or downloaded code.
- Generated code is executed in a subprocess with a stripped environment
  and a timeout. This does not constitute a hardened container.
- The manifest declares automatic_merge_allowed: false, and the gate never
  allows real-world application or code deployment. See the
  [Good-of-All Safety Contract](SAFETY_AND_GOVERNANCE.md).
- Correctness checks prove conformance to a defined synthetic method,
  not scientific innovation or real-world human well-being.
- Holdout outcomes are exploratory, without independent replication.
- Human-authorized review is needed before any source is integrated.

### Not yet implemented

Open-ended autonomous patch writing and genuine novel code primitives
would require a separate model runtime, hardened isolated execution,
independent evaluation, signed diffs, approval gates and rollback.
This project does not grant the worker those privileges.

Contact: tasos.tsikriteas@gmail.com.
