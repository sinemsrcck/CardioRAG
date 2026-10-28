
import random
from src.retrieval_v4 import v4_collection
from src.chunk_quality import is_reference_chunk

random.seed(42)

collection = v4_collection()
total = collection.count()

sample_size = min(200, total)
offsets = random.sample(range(total), sample_size)

flagged = []

for offset in offsets:
    result = collection.get(
        limit=1,
        offset=offset,
        include=["documents", "metadatas"]
    )

    if not result["ids"]:
        continue

    text = result["documents"][0]
    metadata = result["metadatas"][0]

    if is_reference_chunk(text):
        flagged.append({
            "filename": metadata.get("filename"),
            "text": text,
        })

print("\nToplam chunk:", total)
print("Orneklenen:", sample_size)
print("Kaynakca olarak isaretlenen:", len(flagged))

for item in flagged:
    print("\n========== KAYNAKCA ADAYI ==========")
    print("Dosya:", item["filename"])
    print("Metin:", item["text"][:700].replace("\n", " "))
