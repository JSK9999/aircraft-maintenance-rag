"""데이터(세션·매뉴얼·FAQ·체크리스트)를 Segment 단위로 임베딩하여 Chroma에 적재한다.

파이프라인: 수집 → 메타데이터 부여 → 세그먼트 텍스트 구성 → 임베딩 → Vector DB 저장
"""
import json

import chromadb

from . import config, embedder


def _load(path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _session_segment(s: dict) -> str:
    """표시·LLM 근거용 전체 세그먼트 (질문+증상+원인+조치+결과)."""
    causes = ", ".join(s["cause_candidates"])
    return (
        f"[정비 세션] {s['aircraft']} {s['system']} 계통 / 증상: {s['symptom']}\n"
        f"질문: {s['question']}\n"
        f"원인 후보: {causes}\n"
        f"조치: {s['action']}\n"
        f"결과: {s['result']}"
    )


def _session_match(s: dict) -> str:
    """임베딩(검색)용 질문 중심 매칭 텍스트. 짧게 유지해 질문-질문 유사도를 높인다."""
    return f"{s['aircraft']} {s['system']} {s['symptom']}: {s['question']}"


def _knowledge_segment(k: dict) -> str:
    return f"[{k['kind']}] {k['title']}\n{k['content']}"


def _knowledge_match(k: dict) -> str:
    return f"{k['system']} {k['title']}: {k['content']}"


def _records() -> tuple[list[str], list[str], list[str], list[dict]]:
    """(id, 매칭 텍스트, 표시 세그먼트, 메타데이터) 목록을 만든다."""
    ids, matches, docs, metas = [], [], [], []
    for s in _load(config.SESSIONS_PATH):
        ids.append(s["id"])
        matches.append(_session_match(s))
        docs.append(_session_segment(s))
        metas.append({
            "kind": "session",
            "aircraft": s["aircraft"],
            "system": s["system"],
            "symptom": s["symptom"],
            "title": f"정비 세션 #{s['id']}",
            "record": json.dumps(s, ensure_ascii=False),
        })
    for k in _load(config.KNOWLEDGE_PATH):
        ids.append(k["id"])
        matches.append(_knowledge_match(k))
        docs.append(_knowledge_segment(k))
        metas.append({
            "kind": k["kind"],
            "aircraft": k["aircraft"],
            "system": k["system"],
            "symptom": "",
            "title": k["title"],
            "record": json.dumps(k, ensure_ascii=False),
        })
    return ids, matches, docs, metas


def build() -> int:
    """인덱스를 새로 구축하고 적재된 세그먼트 수를 반환한다."""
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    try:
        client.delete_collection(config.COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        config.COLLECTION, metadata={"hnsw:space": "cosine"}
    )
    ids, matches, docs, metas = _records()
    collection.add(ids=ids, documents=docs, metadatas=metas,
                   embeddings=embedder.embed_passages(matches))
    return len(ids)


def get_collection():
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_collection(config.COLLECTION)
