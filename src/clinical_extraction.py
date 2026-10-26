import json
import re
from src.core import generation_client


def extract_clinical_information(question, sources, model=None):
    """
    RAG tarafından bulunan makale parçalarından
    yapılandırılmış klinik bilgiler çıkarır.
    """

    if not sources:
        return {"findings": [], "message": "Kaynak bulunamadı."}

    evidence_parts = []

    for i, source in enumerate(sources, start=1):
        text = (
            source.get("text")
            or source.get("content")
            or source.get("document")
            or ""
        )

        evidence_parts.append(
            f"[{i}]\n"
            f"Makale: {source.get('title', 'Bilinmiyor')}\n"
            f"PMID: {source.get('pmid', '')}\n"
            f"Metin: {text[:5000]}"
        )

    evidence = "\n\n".join(evidence_parts)

    prompt = f"""
Sen bilimsel kardiyoloji makalelerinden yapılandırılmış
klinik bilgi çıkaran bir araştırma asistanısın.

Kullanıcının sorusu:
{question}

Kanıt metinleri:
{evidence}

Aşağıdaki bilgileri çıkar:
- diagnosis: Tanı / hastalık
- treatment: Tedavi
- patient_population: Hasta grubu
- intervention: Müdahale
- comparator: Karşılaştırma grubu
- outcome: Klinik sonuç
- effect_size: Etki büyüklüğü (HR, RR, OR, yüzde vb.)
- confidence_interval: Güven aralığı
- evidence_reference: Kaynak numarası ([1], [2] vb.)

Kurallar:
1. Yalnızca verilen kanıtlardan bilgi çıkar.
2. Eksik bilgileri tahmin etme; null kullan.
3. Etki büyüklüğünü kaynakta yazdığı biçimde koru.
4. Farklı çalışmalardan gelen sonuçları birleştirme.
5. Her bulgunun evidence_reference alanını doldur.
6. Yalnızca geçerli JSON üret.
7. Her bulgu yalnızca evidence_reference ile belirtilen
   kaynak parçasında açıkça bulunan bilgilere dayanmalıdır.

8. Her bulguya "evidence_quote" alanı ekle.
   Bu alan, ilgili kaynak metninden alınan kısa ve
   birebir bir kanıt ifadesi içermelidir.

9. Hasta grubu, müdahale, karşılaştırma ve etki büyüklüğü
   aynı çalışmaya ait değilse tek bulguda birleştirme.

10. Yüzde değerlerini klinik sonlanımlarla karıştırma.
    Örneğin kardiyovasküler mortalite ve hastaneye yatış
    farklı sonuçlardır.

11. Bir bulgunun doğrudan metinsel kanıtı yoksa
    o bulguyu findings listesine ekleme.

JSON biçimi:
{{
  "findings": [
    {{
      "diagnosis": null,
      "treatment": null,
      "patient_population": null,
      "intervention": null,
      "comparator": null,
      "outcome": null,
      "effect_size": null,
      "evidence_quote": null,
      "confidence_interval": null,
      "evidence_reference": "[1]"
    }}
  ]
}}
"""

    client, default_model = generation_client()
    model = model or default_model

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    # Olası Markdown JSON bloklarını temizle
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)

    result = json.loads(raw)

    source_map = {
        f"[{s['number']}]": s.get("text", "")
        for s in sources
    }

    verified_findings = []

    for finding in result.get("findings", []):
        reference = finding.get("evidence_reference")
        quote = finding.get("evidence_quote")

        source_text = source_map.get(reference, "")

        if not isinstance(quote, str) or not quote.strip():
            continue

        # Satır sonu ve fazla boşluk farklılıklarını temizle
        normalized_quote = " ".join(quote.split()).casefold()
        normalized_source = " ".join(source_text.split()).casefold()

        if normalized_quote in normalized_source:
            finding["quote_verified"] = True
            verified_findings.append(finding)

    result["findings"] = verified_findings
    result["verified_count"] = len(verified_findings)

    return result