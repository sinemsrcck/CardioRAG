
import csv
from collections import Counter

from src.retrieval_v4 import v4_collection
from src.chunk_quality import is_reference_chunk

CSV_PATH = "data/evaluation/reranker_comparison_v4.csv"

with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

# Aynı chunk birden fazla yöntemde bulunabilir.
unique_chunks = {
    row["chunk_id"]: row
    for row in rows
    if row.get("chunk_id")
}

ids = list(unique_chunks)
collection = v4_collection()

result = collection.get(
    ids=ids,
    include=["documents", "metadatas"]
)

counts = Counter()
flagged = []

for chunk_id, text, metadata in zip(
    result["ids"],
    result["documents"],
    result["metadatas"]
):
    counts["total"] += 1

    if is_reference_chunk(text):
        counts["reference"] += 1
        flagged.append((chunk_id, metadata, text))

print("\n========== SONUCLAR ==========")
print("Benzersiz chunk:", counts["total"])
print("Kaynakca olarak isaretlenen:", counts["reference"])
print("Diger:", counts["total"] - counts["reference"])

print("\n========== ISARETLENEN CHUNK'LAR ==========")

for chunk_id, metadata, text in flagged:
    print("\nDosya:", metadata.get("filename"))
    print("Chunk:", chunk_id)
    print("Metin:", text[:600].replace("\n", " "))

if not flagged:
    print("Kaynakca olarak isaretlenen chunk bulunamadi.")
