"""Top-K 유사 사례 검색과 도메인 가드.

교수님 원칙: 항공정비 도메인 자료 안에서만 답하고, 근거가 약하면 "근거 자료 없음"으로 처리한다.
유사도가 임계값 미만이면 결과를 비워 상위 계층이 답변을 생성하지 않도록 한다.
"""
import json

from . import config, embedder, index


def _where(aircraft: str | None, system: str | None) -> dict | None:
    clauses = []
    if aircraft:
        clauses.append({"aircraft": aircraft})
    if system:
        clauses.append({"system": system})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def search(query: str, aircraft: str | None = None, system: str | None = None,
           top_k: int = config.TOP_K) -> list[dict]:
    """유사 사례를 유사도 내림차순으로 반환한다. 임계값 미만은 제외한다."""
    collection = index.get_collection()
    res = collection.query(
        query_embeddings=[embedder.embed_query(query)],
        n_results=top_k,
        where=_where(aircraft, system),
    )
    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        similarity = 1.0 - dist  # cosine 거리 → 유사도
        if similarity < config.MIN_SIMILARITY:
            continue
        hits.append({
            "title": meta["title"],
            "kind": meta["kind"],
            "aircraft": meta["aircraft"],
            "system": meta["system"],
            "similarity": round(similarity, 3),
            "segment": doc,
            "record": json.loads(meta["record"]),
        })
    return hits
