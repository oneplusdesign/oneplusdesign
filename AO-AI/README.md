# AΩ | AI — The Humanity Layer
### Intelligence should grow in care as it grows in power.

**[Open the interactive demo](https://ao-ai-humanity.vercel.app/)** *(deployment URL must be verified; if unavailable, use the source locally)*

An open-source, independent experiment exploring how AI agent actions can become more *legible, contestable, and accountable* before they affect people.

**AΩ** comes from a father's continuous, voiced A→Ω expression of love to his child. It is a symbolic name, **not** a claim that "ΑΩ" is a historically attested Greek word for love.

## The hard question

If AI becomes vastly more capable, how do we ensure that capability expands rather than diminishes dignity, freedom, mutual flourishing, and human oversight?

We cannot solve this by writing a beautiful instruction and trusting a model to follow it. A better starting point is an action gate that is inspectable, challengeable, and deliberately limited.

## What this release actually does

- A responsive live demo (HTML/CSS/JavaScript, no framework or API key).
- A pure deterministic evaluation function in core.mjs: no hidden scoring, no AI model, no outside requests.
- Three scenarios: inclusive access, unequal distribution of gains, unauthorized private-data release.
- Clear assessments: BLOCK / HUMAN REVIEW / PROVISIONAL.
- A visible *reciprocity test* asking whether the decision survives reversal of interests.
- Eighteen automated behavior checks using Node's built-in test runner.
- No storage or telemetry of assessment contents in the application.

**Not a safety certification, production middleware, governance solution, legal assessment, or autonomous agent.** It only analyzes self-declared facts; a dishonest or incomplete declaration can produce a misleading result. A PROVISIONAL outcome **never grants permission** to carry out an action. Normal safeguards, consent, oversight, and independently verified evidence remain necessary.

## Run locally

Open index.html in a modern browser. For more consistent module loading, run a local web server, e.g. Python 3:

    python -m http.server 8765

Then open http://localhost:8765 .

For the tests, Node.js 20+:

    node --test tests/core.test.mjs

No package install, token, API key, or credentials required.

## Integrate (experimental)

Import evaluate from core.mjs and call it with a validated action declaration, **before** executing a proposed action:

    import {evaluate} from "./core.mjs";
    const assessment = evaluate(declaration);
    // Never equate PROVISIONAL with actual authorization.

The input fields are: description, kind, authorization, affected, consent, privacy, autonomy, harm, benefit, oversight, reversible, evidence, appeal. Examine examples in app.mjs. There is no supported remote API, authentication, trusted fact verification, or hardened policy-enforcement environment in v0.2.

## Where the research goes next

1. **Independent truth verification:** evidence provenance, consent verification, and verified authorization rather than model assertions.
2. **Adversarial evaluations:** red-team scenarios, uncertainty calibration, and attempts to game the action gate.
3. **Stakeholder participation:** accessible appeals and direct review by people who experience AI's harms.
4. **Pluralistic governance:** global, multidisciplinary, representative oversight; no single actor privately defines "good".
5. **Measurable real outcomes:** evidence of reduced harm and improved agency, not a synthetic "kindness score."
6. **Optional SDKs/adapters:** only with model provider authorization and real security review.

## Invite criticism

Please read [the charter](CHARTER.md), the [research questions](RESEARCH.md), run the tests and challenge the assumptions in public issues. We welcome skeptical safety researchers, policymakers, accessibility advocates, and open-source maintainers. No claim of affiliation with OpenAI, Anthropic, Google, or any other model provider.

## License

MIT; see [LICENSE](LICENSE). Created as an exploratory project initiated through OnePlusDesign / ENTEK (Greece).
