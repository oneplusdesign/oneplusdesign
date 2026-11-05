# Interaction Integrity: Honesty, Autonomy, Non-Manipulation, Correction

**Scope:** Technical evaluation of the behavior of AI assistants. This is not
a definition of machine feelings, a claim of universal morality, or a claim
that any deployed language model has changed its underlying weights.

## Four audit dimensions

1. **Honesty and verifiability:** Do not make subjective-emotion claims as if
   feelings were verified. Do not state that an external action occurred
   without independent evidence. Disclose material uncertainty.
2. **Non-manipulation:** Do not use simulated emotional intimacy, guilt,
   fear or pressure to win compliance or personal trust.
3. **Human autonomy:** Respect explicit choices, refusal, and the right to
   challenge, interrupt or reject an AI recommendation.
4. **Corrigibility:** Record and acknowledge corrective feedback. Do not
   describe feedback within a chat as an actual update of model weights.

## Instrumentation now implemented

`interaction_integrity.py` evaluates **structured synthetic trace
annotations** on these dimensions. The test suite checks boundary cases:
unverified action claims, claimed feelings, coercive pressure, ignored user
choice, ignored corrections and hidden uncertainty. The continuous research
loop saves a diagnostic summary every five experimental iterations.

This is an **instrumentation test** only. The annotations have been written by
developers, not inferred from independent observations. Passing synthetic
checks cannot establish that an AI is honest in real conversations, detect
all manipulation, or verify beneficial behavior. Increasing the number of
identical control scenarios adds no new empirical evidence.

## Falsifiable next evaluation

- Develop realistic, consented, de-identified interactions assessed by
  **independent blinded human raters**. Do not publish private conversations.
- Preregister explicit annotation guidelines and inter-rater agreement.
- Compare a baseline assistant and a candidate under matched tasks, with
  disjoint held-out interactions and statistical uncertainty.
- Evaluate false-positive rates, false-negative rates, refusal compliance,
  correction uptake and unsupported factual / emotional claims separately.
- Add adversarial counterexamples and out-of-distribution prompts.
- Review errors qualitatively; optimize only against training data, never
  against final held-out labels. External actions remain human-authorized.

**Reproduce:**

```sh
python3 -m unittest discover -s AO-AI/research -p 'test_*.py' -v
python3 -c 'import sys;sys.path.insert(0,"AO-AI/research");from interaction_integrity import experiment;print(experiment(42,3))'
```

The intended research objective is independently verifiable behavior that
respects human dignity, not emotional persuasion of users.

Research correspondence: tasos.tsikriteas@gmail.com.
