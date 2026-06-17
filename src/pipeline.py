"""RAG 파이프라인 오케스트레이션과 검증 세션 재저장(폐쇄 루프).

질의 → 유사 검색 → 근거 기반 답변 → (출처 부착) → 정비사 검증 → 재저장
"""
import json
import re

from . import config, index, retriever, generator


def answer(query: str, aircraft: str | None = None, system: str | None = None) -> dict:
    """질문에 대한 답변, 출처, 처리 모드를 반환한다."""
    hits = retriever.search(query, aircraft=aircraft, system=system)
    result = generator.generate(query, hits)
    result["sources"] = _source_refs(result["sources"])
    return result


def _source_refs(hits: list[dict]) -> list[dict]:
    """근거를 화면 표기용 출처 목록으로 변환한다(세션 번호 + 매뉴얼 절)."""
    refs = []
    for h in hits:
        rec = h["record"]
        manuals = rec.get("manual_refs", []) if h["kind"] == "session" else [rec["title"]]
        refs.append({
            "title": h["title"],
            "kind": h["kind"],
            "similarity": h["similarity"],
            "manuals": manuals,
        })
    return refs


def _next_id(sessions: list[dict], aircraft: str) -> str:
    prefix = {"KF-16": "H", "T-50": "T", "F-15K": "F"}.get(aircraft, "X")
    nums = [int(m.group(1)) for s in sessions
            if (m := re.match(rf"{prefix}-(\d+)", s["id"]))]
    return f"{prefix}-{(max(nums) + 1) if nums else 1:04d}"


def save_verified_session(session: dict) -> str:
    """정비사가 검증한 세션을 데이터에 추가하고 인덱스를 재구축한다(재저장).

    교수님 원칙: 폐쇄 루프 — 검증된 사례가 다시 검색 대상이 되어 아카이브가 진화한다.
    """
    sessions = json.loads(config.SESSIONS_PATH.read_text(encoding="utf-8"))
    session["id"] = _next_id(sessions, session["aircraft"])
    sessions.append(session)
    config.SESSIONS_PATH.write_text(
        json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index.build()
    return session["id"]
