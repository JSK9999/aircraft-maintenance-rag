"""검색된 근거를 바탕으로 답변을 생성한다.

OPENAI_API_KEY가 있으면 OpenAI로 근거 기반 답변을 생성하고,
없으면 검색 결과를 그대로 요약하는 추출형 답변으로 자동 폴백한다(키 없이도 동작).
공개 배포 환경에서는 키를 두지 않아 폴백 전용으로 동작한다(비용·키 노출 위험 없음).
AI 신뢰 원칙: AI는 최종 판단자가 아니며 모든 답변은 정비사 검증을 전제로 한다.
"""
import os

from . import config

NO_EVIDENCE = "근거 자료 없음 — 항공정비 도메인 내 유사 사례나 매뉴얼 근거를 찾지 못했습니다."

SYSTEM_PROMPT = (
    "당신은 항공기 정비 의사결정 지원 도우미입니다. 아래 [근거 자료]에 포함된 내용만으로 답하십시오. "
    "근거에 없는 내용은 추측하지 말고, 근거가 부족하면 '근거 자료 없음'이라고 답하십시오. "
    "답변은 (1) 1차 확인 항목/원인 후보, (2) 권고 점검 순서로 간결히 제시하고, "
    "마지막에 'AI 답변이며 실제 조치 전 정비사 검증이 필요합니다.'를 덧붙이십시오. "
    "출처 표기는 시스템이 별도로 부착하므로 본문에 나열하지 마십시오."
)


def _format_evidence(hits: list[dict]) -> str:
    blocks = []
    for h in hits:
        blocks.append(f"- (유사도 {h['similarity']}) {h['title']}\n{h['segment']}")
    return "\n\n".join(blocks)


def _llm_answer(query: str, hits: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI()  # OPENAI_API_KEY 환경변수에서 키를 읽는다
    user = f"[정비사 질문]\n{query}\n\n[근거 자료]\n{_format_evidence(hits)}"
    resp = client.chat.completions.create(
        model=config.ANSWER_MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def _fallback_answer(query: str, hits: list[dict]) -> str:
    """키가 없을 때: 가장 유사한 근거에서 원인 후보와 점검 항목을 추출한다."""
    lines = ["[검색 기반 요약 — LLM 미사용]", ""]
    top = hits[0]
    rec = top["record"]
    if top["kind"] == "session":
        lines.append(f"가장 유사한 과거 세션 #{rec['id']} 기준:")
        lines.append("• 원인 후보: " + ", ".join(rec["cause_candidates"]))
        lines.append("• 당시 조치: " + rec["action"])
        lines.append("• 결과: " + rec["result"])
    else:
        lines.append(f"가장 유사한 {top['kind']} — {rec['title']}:")
        lines.append(rec["content"])
    lines.append("")
    lines.append("AI 답변이며 실제 조치 전 정비사 검증이 필요합니다.")
    return "\n".join(lines)


def generate(query: str, hits: list[dict]) -> dict:
    if not hits:
        return {"answer": NO_EVIDENCE, "mode": "no_evidence", "sources": []}
    if os.getenv("OPENAI_API_KEY"):
        return {"answer": _llm_answer(query, hits), "mode": "llm", "sources": hits}
    return {"answer": _fallback_answer(query, hits), "mode": "fallback", "sources": hits}
