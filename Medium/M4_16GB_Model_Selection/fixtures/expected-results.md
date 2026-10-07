# Fixture acceptance checks — not model outputs

These are original fictional inputs with human-specified checks. No result below is represented as a completed model inference.

**Chat:** three requested sections; no invented measurements.

**Meeting summary:** budget EUR 2,400; Leena owner; Marco certificate renewal with deadline not specified; Sam onboarding draft, not publication approval; Priya notifies beta testers only after schedule approval; production date not approved; retry_budget is 2; no software purchase approval. Additional nuance must remain faithful to the transcript.

**RAG:** approved Aurora budget/owner are EUR 2,400/Leena; no approved production launch date. Do not substitute obsolete EUR 3,000, a suggested Friday, or Beacon's EUR 8,000/Omar. Inspect the actual retrieved excerpts and cite the relevant note.

**Translation:** preserve the amount, negation, conditional publishing approval, unresolved date and exact identifier `retry_budget`. Fluency requires a competent reviewer; no universal gold wording is asserted.

**Vision/OCR:** Coffee quantity2 ×3.60 =7.20; Notebook1 ×8.50 =8.50; Pencils3 ×1.20 =3.60; total EUR19.30. Receipt TEST-1005, 5 October 2026. A hallucinated item or decimal is a failure.

**ASR:** compare the recording with recording-script.txt; named people, amount and negative launch-date statement matter. Reading deviations by the person making the recording belong in the ground truth, not automatically in the model's error count.

**Image:** recognizable small desktop, notebook, plant; specified composition; no requested text. This is a subjective acceptance rubric, not a reference pixel image.

**TTS:** decodable nonempty audio; intelligible text; inspect names/numbers; record pronunciation errors and speech duration. Voice-clone similarity is evaluated separately with the speaker's permission.

**Coding:** fixture tests fail before repair, and all9 tests should pass after a correct repair. Tests are not modified. Review the code before executing it. Passing the fixture does not establish broad coding ability.
