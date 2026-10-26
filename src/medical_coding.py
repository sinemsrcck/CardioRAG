import re

# İlk prototip için ICD-10 eşleştirmeleri
# Klinik kullanım öncesinde terminoloji sürümüyle doğrulanmalıdır.
ICD10_TERMS = {
    "heart failure": {
        "code": "I50.9",
        "label": "Heart failure, unspecified"
    },
    "dyspnea": {
        "code": "R06.0",
        "label": "Dyspnoea"
    },
    "fatigue": {
        "code": "R53",
        "label": "Malaise and fatigue"
    },
    "peripheral edema": {
        "code": "R60.0",
        "label": "Localized oedema"
    }
}


def normalize_term(term):
    return re.sub(r"\s+", " ", term.strip().lower())


def match_icd10(term):
    normalized = normalize_term(term)

    match = ICD10_TERMS.get(normalized)

    if not match:
        return {
            "term": term,
            "icd10_code": None,
            "icd10_label": None,
            "coding_status": "unmatched"
        }

    return {
        "term": term,
        "icd10_code": match["code"],
        "icd10_label": match["label"],
        "coding_status": "matched"
    }


def code_symptom_relations(relations):
    coded_relations = []

    for relation in relations:
        coded = relation.copy()

        coded["diagnosis_coding"] = match_icd10(
            relation.get("diagnosis", "")
        )

        coded["symptom_coding"] = match_icd10(
            relation.get("symptom", "")
        )

        coded_relations.append(coded)

    return coded_relations