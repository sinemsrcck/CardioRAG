import json
import re
from src.medical_coding import code_symptom_relations
from src.core import generation_client


def extract_symptom_relations(question, sources):
    if not sources:
        return {"relations": []}

    evidence = "\n\n".join(
        f"[{s['number']}]\n{s.get('text', '')}"
        for s in sources
    )

    client, model = generation_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract diagnosis-symptom relationships "
                    "from biomedical literature. Return valid JSON only. "
                    "Never invent clinical findings."
                )
            },
            {
                "role": "user",
                "content": f"""
Question: {question}

Evidence:
{evidence}

Extract diagnosis-symptom relationships.

Return JSON:
{{
  "relations": [
    {{
      "diagnosis": "heart failure",
      "symptom": "dyspnea",
      "relationship": "associated_with",
      "evidence_reference": "[1]",
      "evidence_quote": "Patients with heart failure commonly experience dyspnea, fatigue, and peripheral edema."
    }},
    {{
      "diagnosis": "heart failure",
      "symptom": "fatigue",
      "relationship": "associated_with",
      "evidence_reference": "[1]",
      "evidence_quote": "Patients with heart failure commonly experience dyspnea, fatigue, and peripheral edema."
    }},
    {{
      "diagnosis": "heart failure",
      "symptom": "peripheral edema",
      "relationship": "associated_with",
      "evidence_reference": "[1]",
      "evidence_quote": "Patients with heart failure commonly experience dyspnea, fatigue, and peripheral edema."
    }}
  ]
}}

Rules:
- Use only the provided evidence.
- Extract only explicitly supported relationships.
- Do not infer causation from association.
- Do not invent ICD-10 or SNOMED CT codes.
- Use an empty relations list if no relationships exist.
- Extract EVERY explicitly mentioned symptom separately.
- If a sentence lists multiple symptoms, create one relation
  for each symptom.
- Do not combine multiple symptoms into one relation.
- Each relation must have its own evidence_quote.
- The evidence_quote must be an exact substring of the source.
- A single evidence_quote may support multiple relations
  if it explicitly mentions all their symptoms.
  - Preserve diagnosis and symptom names exactly as written
  in the source text.
"""
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)

    result = json.loads(raw)

    source_map = {
        f"[{s['number']}]": " ".join(s.get("text", "").split()).casefold()
        for s in sources
    }

    verified = []

    for relation in result.get("relations", []):
        reference = relation.get("evidence_reference")
        quote = relation.get("evidence_quote")

        if not isinstance(quote, str) or not quote.strip():
            continue

        normalized_quote = " ".join(quote.split()).casefold()

        symptom = relation.get("symptom")

        if not isinstance(symptom, str) or not symptom.strip():
            continue

        normalized_symptom = " ".join(symptom.split()).casefold()

        if (
            normalized_quote in source_map.get(reference, "")
            and normalized_symptom in normalized_quote
        ):
            relation["quote_verified"] = True
            verified.append(relation)
    return {
        "relations": code_symptom_relations(verified),
        "verified_count": len(verified)
    }