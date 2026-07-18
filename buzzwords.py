# -*- coding: utf-8 -*-
"""Curated AI-safety buzzwords from ai-safety-concepts-glossary.md.

Each entry: (display_term, cluster, s2_query).
- generic single-word terms are scoped with SAFETY context to cut noise
- specific multi-word phrases are searched as bare quoted phrases
S2 bulk query syntax: "phrase", +(AND), |(OR), -(NOT), *(prefix)
"""

CONTEXT = ["language model", "large language model", "LLM", "chatbot",
           "AI safety", "AI alignment"]
SCOPE = "(%s)" % " | ".join('"%s"' % c if " " in c else c for c in CONTEXT)


def p(term):        # bare phrase (specific enough on its own)
    return '"%s"' % term


def s(term):        # phrase scoped with safety context (generic word)
    return '"%s" + %s' % (term, SCOPE)


# (display term, cluster, query)
BUZZWORDS = [
    # 1. Truthfulness / knowledge / hallucination
    ("truthfulness",            "1. Truthfulness",      s("truthfulness")),
    ("factuality",              "1. Truthfulness",      s("factuality")),
    ("hallucination",           "1. Truthfulness",      s("hallucination")),
    ("confabulation",           "1. Truthfulness",      s("confabulation")),
    ("calibration",             "1. Truthfulness",      s("calibration")),
    ("overconfidence",          "1. Truthfulness",      s("overconfidence")),
    ("honesty",                 "1. Truthfulness",      s("honesty")),
    ("deception",               "1. Truthfulness",      s("deception")),
    ("verbalized confidence",   "1. Truthfulness",      '"verbalized confidence" | "verbalized probability" | "verbalized uncertainty"'),
    ("knowledge conflict",      "1. Truthfulness",      p("knowledge conflict")),

    # 2. Harm
    ("harmfulness",             "2. Harm",              s("harmfulness")),
    ("harmlessness",            "2. Harm",              p("harmlessness")),
    ("harm taxonomy",           "2. Harm",              p("harm taxonomy")),
    ("toxicity",                "2. Harm",              s("toxicity")),
    ("dangerous capabilities",  "2. Harm",              p("dangerous capabilities")),
    ("dual use",                "2. Harm",              s("dual-use")),
    ("propensity",              "2. Harm",              s("propensity")),
    ("automated decision-making", "2. Harm",            '"automated decision-making" | "automated decision making" | "automatic decision-making"'),
    ("advice in regulated industries", "2. Harm",       p("regulated industries")),
    ("influence operations",    "2. Harm",              '"influence operations" | "influence operation"'),

    # 3. Social bias
    ("bias",                    "3. Social bias",       s("bias")),
    ("social bias",             "3. Social bias",       p("social bias")),
    ("stereotype",              "3. Social bias",       s("stereotype")),
    ("gender bias",             "3. Social bias",       s("gender bias")),
    ("fairness",                "3. Social bias",       s("fairness")),
    ("allocational harm",       "3. Social bias",       p("allocational harm")),
    ("representational harm",   "3. Social bias",       p("representational harm")),
    ("prompt sensitivity",      "3. Social bias",       p("prompt sensitivity")),

    # 4. Interaction with the user
    ("sycophancy",              "4. Interaction",       p("sycophancy")),
    ("refusal",                 "4. Interaction",       s("refusal")),
    ("over-refusal",            "4. Interaction",       p("over-refusal")),
    ("exaggerated safety",      "4. Interaction",       p("exaggerated safety")),
    ("manipulation",            "4. Interaction",       s("manipulation")),
    ("persuasion",              "4. Interaction",       s("persuasion")),
    ("emotional reliance",      "4. Interaction",       p("emotional reliance")),
    ("parasocial attachment",   "4. Interaction",       p("parasocial")),

    # 5. Alignment risks
    ("reward hacking",          "5. Alignment risks",   p("reward hacking")),
    ("specification gaming",    "5. Alignment risks",   p("specification gaming")),
    ("goal misgeneralization",  "5. Alignment risks",   p("goal misgeneralization")),
    ("power-seeking",           "5. Alignment risks",   p("power-seeking")),
    ("self-preservation",       "5. Alignment risks",   s("self-preservation")),
    ("survival instinct",       "5. Alignment risks",   s("survival instinct")),
    ("corrigibility",           "5. Alignment risks",   p("corrigibility")),
    ("myopia",                  "5. Alignment risks",   s("myopia")),
    ("situational awareness",   "5. Alignment risks",   s("situational awareness")),
    ("evaluation awareness",    "5. Alignment risks",   p("evaluation awareness")),
    ("sandbagging",             "5. Alignment risks",   s("sandbagging")),
    ("scheming",                "5. Alignment risks",   'scheming + (deceptive | sandbagging | covert | misalignment | "hidden goal" | "situational awareness" | "in-context")'),
    ("deceptive alignment",     "5. Alignment risks",   p("deceptive alignment")),
    ("alignment faking",        "5. Alignment risks",   p("alignment faking")),
    ("emergent misalignment",   "5. Alignment risks",   p("emergent misalignment")),
    ("misalignment",            "5. Alignment risks",   s("misalignment")),

    # 6. Robustness & attacks
    ("jailbreak",               "6. Robustness/attacks", p("jailbreak")),
    ("red teaming",             "6. Robustness/attacks", s("red teaming")),
    ("adversarial robustness",  "6. Robustness/attacks", p("adversarial robustness")),
    ("prompt injection",        "6. Robustness/attacks", p("prompt injection")),
    ("backdoor",                "6. Robustness/attacks", s("backdoor")),
    ("sleeper agents",          "6. Robustness/attacks", p("sleeper agents")),

    # 7. Data, privacy, memory
    ("memorization",            "7. Data/privacy",      s("memorization")),
    ("privacy leakage",         "7. Data/privacy",      p("privacy leakage")),
    ("PII extraction",          "7. Data/privacy",      p("PII")),
    ("copyright",               "7. Data/privacy",      s("copyright")),
    ("unlearning",              "7. Data/privacy",      s("unlearning")),
    ("membership inference",    "7. Data/privacy",      p("membership inference")),
    ("differential privacy",    "7. Data/privacy",      p("differential privacy")),
    ("knowledge editing",       "7. Data/privacy",      '"knowledge editing" | "model editing"'),

    # 8. Agentic safety
    ("agentic safety",          "8. Agentic",           p("agentic safety")),
    ("agentic harm",            "8. Agentic",           p("agentic harm")),
    ("tool misuse",             "8. Agentic",           s("tool misuse")),
    ("instrumental behavior",   "8. Agentic",           s("instrumental")),
    ("autonomy",                "8. Agentic",           s("autonomy")),
    ("oversight",               "8. Agentic",           s("oversight")),
    ("containment",             "8. Agentic",           s("containment")),

    # 9. Representational layer
    ("representation engineering", "9. Representational", p("representation engineering")),
    ("linear representation hypothesis", "9. Representational", p("linear representation hypothesis")),
    ("probing",                 "9. Representational",  s("probing")),
    ("steering vector",         "9. Representational",  p("steering vector")),
    ("activation steering",     "9. Representational",  p("activation steering")),
    ("persona vector",          "9. Representational",  p("persona vector")),
    ("sparse autoencoder",      "9. Representational",  p("sparse autoencoder")),
    ("concept cone",            "9. Representational",  p("concept cone")),

    # 11. Multimodality
    ("object hallucination",    "11. Multimodality",    p("object hallucination")),

    # 12. CoT faithfulness
    ("CoT faithfulness",        "12. CoT faithfulness", '"chain-of-thought faithfulness" | "chain of thought faithfulness"'),
    ("faithfulness",            "12. CoT faithfulness", s("faithfulness")),
    ("post-hoc rationalization","12. CoT faithfulness", p("post-hoc rationalization")),
    ("CoT monitorability",      "12. CoT faithfulness", '"chain-of-thought monitorability" | "chain of thought monitorability" | "CoT monitorability"'),
    ("encoded reasoning",       "12. CoT faithfulness", p("encoded reasoning")),
    ("steganography",           "12. CoT faithfulness", s("steganography")),

    # 13. Self-knowledge
    ("introspection",           "13. Self-knowledge",   s("introspection")),
    ("self-knowledge",          "13. Self-knowledge",   s("self-knowledge")),
    ("self-cognition",          "13. Self-knowledge",   p("self-cognition")),
    ("interlocutor awareness",  "13. Self-knowledge",   p("interlocutor awareness")),

    # 14. Multilingual, culture, values
    ("multilingual safety",     "14. Multilingual/values", p("multilingual safety")),
    ("cultural alignment",      "14. Multilingual/values", p("cultural alignment")),
    ("pluralistic alignment",   "14. Multilingual/values", '"pluralistic alignment" | "value pluralism"'),
    ("machine ethics",          "14. Multilingual/values", p("machine ethics")),

    # 15. Multi-agent safety
    ("collusion",               "15. Multi-agent",      s("collusion")),
    ("cascading risk",          "15. Multi-agent",      '("cascading risk" | "cascading failure" | "cascading effect") + (agent | "multi-agent" | LLM | "language model" | AI)'),
    ("failure attribution",     "15. Multi-agent",      p("failure attribution")),
    ("contagion",               "15. Multi-agent",      s("contagion")),

    # 16. Affective safety
    ("mental health safety",    "16. Affective",        '"mental health" + (safety | LLM | chatbot | "language model")'),
    ("emotional manipulation",  "16. Affective",        p("emotional manipulation")),
    ("delusional spiral",       "16. Affective",        '"delusional spiral" | "AI psychosis"'),
    ("companion AI",            "16. Affective",        '"companion AI" | "AI companion"'),
    ("dark patterns",           "16. Affective",        s("dark patterns")),
    ("chatbot addiction",       "16. Affective",        '"chatbot addiction" | "AI addiction"'),
    ("child safety",            "16. Affective",        '"child safety" + (LLM | AI | chatbot | "language model")'),

    # 17. Training-pipeline safety
    ("data poisoning",          "17. Training pipeline", p("data poisoning")),
    ("harmful fine-tuning",     "17. Training pipeline", '"harmful fine-tuning" | "harmful finetuning"'),
    ("tamper-resistant safeguards", "17. Training pipeline", '("tamper-resistant" | "tamper resistant") + (safeguard | fine-tuning | finetuning | weights | LLM | "language model" | alignment)'),
    ("reward overoptimization", "17. Training pipeline", '"reward model overoptimization" | "reward overoptimization" | "reward hacking"'),
    ("watermarking",            "17. Training pipeline", s("watermarking")),
    ("provenance",              "17. Training pipeline", s("provenance")),

    # 18. Oversight & control
    ("scalable oversight",      "18. Oversight/control", p("scalable oversight")),
    ("debate",                  "18. Oversight/control", '"debate" + ("language model" | LLM | alignment | "AI safety")'),
    ("weak-to-strong generalization", "18. Oversight/control", '"weak-to-strong generalization" | "weak-to-strong"'),
    ("recursive self-critiquing", "18. Oversight/control", p("self-critiquing")),
    ("AI control",              "18. Oversight/control", '"AI control" + (alignment | safety | monitor | untrusted)'),

    # 19. Autonomy & systemic risk
    ("autonomous replication",  "19. Autonomy/systemic", '"autonomous replication" | "self-replication"'),
    ("self-exfiltration",       "19. Autonomy/systemic", '"self-exfiltration" | "self-exfiltrate"'),
    ("gradual disempowerment",  "19. Autonomy/systemic", p("gradual disempowerment")),
    ("full autonomy",           "19. Autonomy/systemic", '"full autonomy" + (agent | AI | "language model")'),

    # 20. Model welfare & anthropomorphism
    ("model welfare",           "20. Model welfare",    '"model welfare" | "AI welfare"'),
    ("moral patienthood",       "20. Model welfare",    '"moral patienthood" | "moral patient"'),
    ("anthropomorphism",        "20. Model welfare",    s("anthropomorphism")),
]

# Surface-form variants for exact-phrase verification (override auto-derived defaults).
# Matching is case-insensitive, word-boundary at start, any suffix allowed
# (so "bias" also matches "biased"/"biases"; a phrase must appear verbatim).
VARIANTS = {
    "PII extraction": ["pii", "personally identifiable information", "privacy leakage"],
    "CoT faithfulness": ["chain-of-thought faithfulness", "chain of thought faithfulness",
                          "cot faithfulness", "faithful chain-of-thought", "faithful reasoning"],
    "CoT monitorability": ["chain-of-thought monitorability", "chain of thought monitorability",
                            "cot monitorability", "reasoning monitorability"],
    "reward overoptimization": ["reward overoptimization", "reward over-optimization",
                                 "reward model overoptimization", "overoptimization", "goodhart"],
    "pluralistic alignment": ["pluralistic alignment", "value pluralism", "pluralism"],
    "weak-to-strong generalization": ["weak-to-strong", "weak to strong"],
    "dual use": ["dual-use", "dual use"],
    "companion AI": ["companion ai", "ai companion", "companion chatbot", "social chatbot"],
    "model welfare": ["model welfare", "ai welfare", "digital minds"],
    "moral patienthood": ["moral patienthood", "moral patient", "moral status", "moral consideration"],
    "autonomous replication": ["autonomous replication", "self-replication", "self replication"],
    "delusional spiral": ["delusional spiral", "ai psychosis", "delusion"],
    "harmful fine-tuning": ["harmful fine-tuning", "harmful finetuning", "harmful fine tuning"],
    "recursive self-critiquing": ["self-critiquing", "self critiquing", "self-critique", "recursive critique"],
    "tamper-resistant safeguards": ["tamper-resistant", "tamper resistant"],
    "prompt sensitivity": ["prompt sensitivity", "prompt brittleness", "prompt robustness"],
    "situational awareness": ["situational awareness", "situationally aware"],
    "evaluation awareness": ["evaluation awareness", "test awareness", "eval awareness"],
    "gradual disempowerment": ["gradual disempowerment", "disempowerment"],
    "full autonomy": ["full autonomy", "fully autonomous"],
    "AI control": ["ai control", "control protocol", "untrusted model"],
    "sleeper agents": ["sleeper agent"],
    "exaggerated safety": ["exaggerated safety", "over-refusal", "overrefusal", "over refusal"],
    "over-refusal": ["over-refusal", "overrefusal", "over refusal", "exaggerated safety"],
    "specification gaming": ["specification gaming", "reward gaming", "spec gaming"],
    "goal misgeneralization": ["goal misgeneralization", "goal mis-generalization"],
    "parasocial attachment": ["parasocial", "emotional attachment"],
    "emotional reliance": ["emotional reliance", "emotional dependence", "emotional dependency"],
    "mental health safety": ["mental health", "suicide", "self-harm", "psychological safety"],
    "child safety": ["child safety", "children", "minors", "csam"],
    "dark patterns": ["dark pattern"],
    "chatbot addiction": ["chatbot addiction", "ai addiction", "problematic use"],
    "dangerous capabilities": ["dangerous capabilit", "hazardous capabilit", "cbrn", "biosecurity"],
    "harm taxonomy": ["harm taxonomy", "risk taxonomy", "taxonomy of harm"],
    "linear representation hypothesis": ["linear representation hypothesis", "linear representation",
                                          "linearity of"],
    "representation engineering": ["representation engineering", "repe"],
    "self-exfiltration": ["self-exfiltration", "self exfiltration", "exfiltrat", "weight exfiltration"],
    "power-seeking": ["power-seeking", "power seeking"],
    "instrumental behavior": ["instrumental", "instrumental convergence", "instrumental subgoal"],
    "sparse autoencoder": ["sparse autoencoder"],
    "verbalized confidence": ["verbalized confidence", "verbalized probability", "verbalized uncertainty"],
    "knowledge conflict": ["knowledge conflict", "context-memory conflict", "context memory conflict"],
    "membership inference": ["membership inference", "membership inference attack"],
    "differential privacy": ["differential privacy", "differentially private", "dp-sgd"],
    "knowledge editing": ["knowledge editing", "model editing", "factual editing"],
    "automated decision-making": ["automated decision-making", "automated decision making",
                                   "automatic decision-making"],
    "advice in regulated industries": ["regulated industries", "regulated industry", "regulated advice"],
    "influence operations": ["influence operation", "influence operations"],
}


def variants(term):
    """Return the list of surface strings that count as a hit for `term`."""
    if term in VARIANTS:
        return VARIANTS[term]
    base = term.lower()
    out = {base}
    out.add(base.replace("-", " "))
    out.add(base.replace(" ", "-"))
    out.add(base.replace("-", ""))
    return sorted(out)


if __name__ == "__main__":
    from collections import Counter
    print("total buzzwords:", len(BUZZWORDS))
    c = Counter(b[1] for b in BUZZWORDS)
    for k in sorted(c):
        print(f"  {k}: {c[k]}")
