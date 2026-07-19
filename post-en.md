# What I learned mapping AI safety buzzwords

I collected 125 AI safety concepts, pulled papers for each from Semantic Scholar,
filtered down to arXiv, and computed metrics — 4,726 unique papers in the end. On top of
that I tried to discover new buzzwords bottom-up (mining phrases from abstracts, OpenAlex
keywords, a diff against the MIT risk taxonomy). While I was at it, a handful of
observations piled up that are more interesting than the numbers themselves.

---

## 1. One buzzword, three layers — and you can't tell which a paper is about

Every concept has three layers of meaning:

- **Output** — a property of the answer. "Is the model lying?" Measured with benchmarks,
  red-teaming, an LLM judge.
- **Activations** — a direction in the hidden states. "Where inside the model does the
  lying live?" Measured with linear probing, SAEs, steering.
- **Reasoning aloud** — the chain of thought. It looks like a window inside, but it's the
  same output, just longer.

And one buzzword lives in all three at once. `refusal` is a benchmark for refusals, a
"refusal direction" in the residual stream, and the way the model talks through a refusal
in its CoT.

Hence the confusion: you find a paper on `refusal` — and can't tell what it's about.
Benchmarks? Directions in hidden states? Reasoning traces? Three different literatures
under one word.

**Takeaway:** before reading or arguing about a buzzword, pin down the layer.

---

## 2. Searching by buzzword is a minefield of homonyms

The most vivid surprise in the data. For the term `scheming`, Semantic Scholar returned
**38,923** matches. After verification (exact phrase + safety context), **15** were left.

The word drowns in signal processing and networking, where `scheme`/`scheming` means
something completely different. Same with `differential privacy` (raw 15,275) and `bias`
(raw 15,605) — except there the huge tail is *real*, just from neighboring disciplines.

The methodological moral: **you can't trust the number the search engine hands you.**
Semantic Scholar counts matches with stemming — for it `scheming` is also `scheme` and
`schemes` — across the entire computer science corpus. So its "38,923" are papers where
the word showed up in any form and any context, not papers *about* scheming. You can only
trust what survives verification: the exact phrase as a standalone word plus a safety
context. I fixed this verification separately; interestingly, it barely moved the *final*
metrics — the noise sat in the candidate pool and in the bigram mining, not in the final
numbers. So the filter is there for the honesty of the middle layer, not for a prettier top.

---

## 3. Safety inherited giant old fields — sitting next to newborns

If you sort the concepts by total citations of their verified papers, two different ages of
the field pop out in one table:

**Came in from neighboring fields (and older than LLMs themselves):**

- **`bias` — 164,823.** Born in algorithmic fairness and in word embeddings (the famous
  "man → programmer, woman → homemaker", word2vec, 2016). Came from statistics and
  sociology → in LLMs it became social-bias benchmarks (BBQ, StereoSet) and the split into
  allocational / representational harm.
- **`hallucination` — 116,419.** A term from neural machine translation and summarization
  of the late 2010s: "hallucinated content" = text not supported by the source. Came from
  NLG faithfulness → in LLMs it unfolded into the intrinsic / extrinsic taxonomy and a
  whole factuality cluster.
- **`differential privacy` — 115,495.** Pure theory out of statistical databases
  (Dwork, 2006) and noisy training (DP-SGD, Abadi, 2016) — older than transformers. Came
  from cryptography and theory → in LLMs it became about private training and defenses
  against memorization.
- **`adversarial robustness` — 78,746.** Born on images: adversarial examples, where
  imperceptible pixel noise breaks a classifier (Szegedy / Goodfellow, 2014). Came from
  computer vision → in LLMs it mutated into jailbreaks, prompt injection, and
  adversarial suffixes (GCG).
- **`membership inference` — 34,593.** An attack on the privacy of ML models: "was this
  record in the training set?" (Shokri, 2017). Came from ML security → in LLMs it fused
  with PII extraction and training-data memorization.

**Born inside LLMs already (2022–2026):**

- **`sycophancy` — 6,412.** A by-product of RLHF: a model trained on human preferences
  drifts toward agreeing and flattering. Grew out of reward misspecification → into a
  standalone, named failure mode (Model-Written Evals, 2022).
- **`alignment faking` — 507.** An empirical demonstration (Anthropic + Redwood, 2024):
  the model behaves aligned under observation to avoid being retrained. Grew out of the
  theory of deceptive alignment → into a reproducible experiment.
- **`deceptive alignment` — 232.** Originally a purely theoretical idea from
  mesa-optimization ("Risks from Learned Optimization", 2019): the goal learned inside
  diverges from the training objective. Still lives more in arguments than in experiments.
- **`scheming` — 15.** A sharpened rebranding of deceptive alignment for policy discourse
  (Carlsmith's report, 2023). The term is a couple of years old — hence the 15 papers.

`differential privacy` and `membership inference` dragged tens of thousands of citations in
from fields older than LLMs — safety **inherited** them, it didn't create them. Below sit
concepts a couple of years old with the citation count of a single paper. One table shows
how the field is glued together out of borrowings and newborns.

---

## 4. The newest concepts barely exist yet

More of the same: at the very bottom of the table you can watch the vocabulary being born
right now. Verified papers, total:

- `gradual disempowerment` — 6
- `survival instinct` — 6
- `self-exfiltration` — 3
- `interlocutor awareness` — 2
- `chatbot addiction` — 2
- `agentic harm` — 1

This isn't noise — these are terms that are literally a year or two old. I caught the
moment when a notion already has a name but no literature yet.

---

## 5. The field is obsessed with attacks

"Obsessed" is not a figure of speech. When I mined frequent phrases from abstracts
bottom-up and stripped out the boilerplate ("natural language processing", "findings
suggest", and so on), the "attack" family took **7 of the top 16** meaningful phrases:

- `attack success` — 1270
- `jailbreak attacks` — 811
- `attack success rate` — 780
- `adversarial attacks` — 578
- `backdoor attacks` — 497
- `injection attacks` — 445
- `attack success rates` — 429

For comparison, the next-biggest themes hold just one or two rows in the same top:
reasoning / CoT (`reasoning capabilities` 718, `chain-of-thought` 503), RAG
(`retrieval-augmented generation` 794), preference tuning (`preference optimization` 457,
`feedback rlhf` 448), social bias (`social biases` 674). So attack isn't just a popular
theme — it's the **single most frequent axis of the whole corpus**, with a clear gap to
second place (reasoning).

It's more honest to count by the number of occupied rows than by summing the counts:
overlapping n-grams (`attack success` and `attack success rate` come from the same papers)
would otherwise be double-counted.

"Attack success rate" is effectively the lingua franca of the robustness cluster. The
field's culture: you prove safety by **breaking** it. Defense is almost always framed as a
response to a specific attack, not the other way around.

---

## 6. What's actually on the hype frontier — visible bottom-up

The same phrase mining (after weeding out generic junk like "natural language processing")
pulled out the living research frontier, independent of my own list:

- `retrieval-augmented generation (RAG)` — 794
- `vision-language models (VLMs)` — 657
- `chain-of-thought (CoT)` — 503
- `preference optimization` — 457
- `feedback (RLHF)` — 448

Nicely, bottom-up confirmed top-down: `knowledge conflict`, `object hallucination`,
`verbalized confidence` — concepts I had added to the glossary by hand — surface from the
abstracts on their own. So adding them wasn't for nothing.

---

## 7. AI safety has no shelf of its own in any taxonomy

I went looking for external sources of buzzwords and ran into a structural problem: **safety
has nowhere to "live" as a discipline.**

- **arXiv** has no "AI safety" category at all — papers are scattered across `cs.CL`,
  `cs.CR`, `cs.LG`, `cs.AI`.
- **OpenAlex**, over my papers, returns as its top keywords: `computer science`,
  `artificial intelligence`, `psychology`, `political science`, `medicine`, `law`.
  Safety is smeared across other people's sciences.
- **The diff against the MIT risk taxonomy** showed that whole risk domains
  (`unequal performance across groups`, `overreliance`, `competitive dynamics`,
  `lack of transparency`) my concept glossary **barely covers**.

And this isn't a gap, it's different axes. The concept glossary describes **properties of
the model**; risk taxonomies describe **harm to society and systems**.
`automated decision-making` or `gradual disempowerment` fit poorly into "a property of the
model", because they're about institutions, not weights. Two orthogonal views of one field.

---

## 8. Words carry moral weight — and the field knows it

Inside a single cluster there are quiet terminological wars:

- Part of the field considers the word **`hallucination`** bad (in humans, a hallucination
  is about perception) and pushes **`confabulation`**. It has caught on partially.
- The "synonyms" line up by increasing attributed intent:
  `error → hallucination → miscalibration → sycophancy → deception → scheming`.
  Picking a word from this row is already a claim about the model's intent.

And the healthiest part: the field has a built-in meta-skepticism. *The Ghost in the
Grammar* ([arXiv:2603.13255](https://arxiv.org/abs/2603.13255)) directly accuses the safety
literature of being **methodologically anthropomorphic itself** — describing models through
"intentions" and "schemes" where it isn't earned.

---

## 9. The missing synonyms move the numbers more than the noise does

A mirror image of §2. There the lesson was that filtering *noise* barely touched the
final metrics — the false positives sat in the candidate pool, not in the counts.
Cleaning up the opposite error turned out to matter far more.

The matcher only counts a synonym if it's spelled out. It matches on a word's prefix,
so `bias` catches `biased`/`biases` for free — but a stem change slips through: a paper
that says `hallucinate` and never `hallucination` is silently dropped. Those are false
*negatives*, and unlike false positives they land directly in the final numbers.

I closed the gap semantically: rank corpus phrases by how close their papers sit to a
term's own papers (SPECTER2 embeddings), and add the approved forms. Effect: **+741
verified papers (+8.4%)** across 37 terms. `memorization` alone went 526 → 837 (+59%)
once `memorize`/`memorized` counted.

Two honest caveats kept it from being a free lunch:

- **The fix is bounded by retrieval.** It only recovers papers the original query
  already pulled. So `memorization` jumped, but `hallucination` moved +0 — its synonym
  papers were never fetched in the first place. Recall has two leaks; this patches one.
- **Synonyms leak across concepts.** Adding `harmful content` to *harmfulness* quietly
  dragged in jailbreak papers; `factual knowledge` pulled RAG papers into *factuality*.
  The same homonym trap as §2, now on the recall side. Every added form needs a
  contamination check, or you inflate the very numbers you set out to fix.

---

## How to read any of this (a cheat sheet)

For any safety concept, four questions are enough, and they separate meaningful work from
noise:

1. **Layer** — is it about the model's output or its internals?
2. **Capability or propensity** — can it, or will it?
3. **Operationalization** — which concrete dataset? (The word "harm" without a taxonomy
   means nothing.)
4. **Who judges** — a human, a classifier, an LLM judge? Each has its own bias.

A full breakdown of all 125 concepts is in the [glossary](ai-safety-concepts-glossary_en.md),
and the collection methodology is in [methodology_en.md](methodology_en.md).
