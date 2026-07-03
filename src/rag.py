from pathlib import Path

import chromadb
from sklearn.feature_extraction.text import TfidfVectorizer

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "chroma_db"

# ponytail: TF-IDF (sklearn, already a project dep) instead of Chroma's default
# ONNX embedding download — that model fetch times out on this network. Corpus
# is a handful of short docs, so rebuilding the collection on every search() is
# still instant; re-embed with a real model if the knowledge base grows a lot.


def _load_docs() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(KNOWLEDGE_DIR.glob("*.md"))}


def _build_collection():
    docs = _load_docs()
    vectorizer = TfidfVectorizer().fit(list(docs.values()))

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection("knowledge")
    except Exception:
        pass
    collection = client.create_collection("knowledge")
    embeddings = vectorizer.transform(list(docs.values())).toarray().tolist()
    collection.add(documents=list(docs.values()), ids=list(docs.keys()), embeddings=embeddings)
    return collection, vectorizer


def search(query: str, n_results: int = 3) -> list[tuple[str, str]]:
    collection, vectorizer = _build_collection()
    n_results = min(n_results, collection.count())
    query_embedding = vectorizer.transform([query]).toarray().tolist()
    result = collection.query(query_embeddings=query_embedding, n_results=n_results)
    return list(zip(result["ids"][0], result["documents"][0]))


if __name__ == "__main__":
    hits = search("우산 강수확률")
    assert hits, "no knowledge docs indexed"
    for doc_id, _ in hits:
        print(doc_id)
