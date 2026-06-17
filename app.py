"""정비 질의응답 콘솔 (Streamlit, 채팅 스타일).

탭1: 채팅형 질의응답 (질문 → 근거 기반 답변 + 출처)
탭2: 정비사 검증 · 세션 재저장 (폐쇄 루프) — 일반 사용자 입력과 분리
실행:  streamlit run app.py
"""
import os

from dotenv import load_dotenv
import streamlit as st

from src import config, index, pipeline

load_dotenv()

st.set_page_config(page_title="항공기 정비 세션 아카이브 RAG", page_icon="🛩️", layout="wide")

EXAMPLES = [
    "유압 압력이 낮고 경고등이 점등됩니다. 우선 확인할 항목은?",
    "압력 상승이 안 됩니다",
    "엔진 배기 온도가 평소보다 올라가요",
    "무전기 소리가 잘 안 들려요",
]


def ensure_index() -> bool:
    try:
        index.get_collection()
        return True
    except Exception:
        return False


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"출처 {len(sources)}건 보기"):
        for ref in sources:
            manuals = " · ".join(ref["manuals"]) if ref["manuals"] else "-"
            st.markdown(
                f"- **{ref['title']}** (유사도 {ref['similarity']}, {ref['kind']}) "
                f"— 근거: {manuals}"
            )


# ---- 사이드바: 상태 / 검색 필터 ----
with st.sidebar:
    st.header("🛩️ 정비 세션 아카이브")
    st.caption("도메인 특화 RAG · 항공기 정비 질의응답 MVP")

    llm_on = bool(os.getenv("OPENAI_API_KEY"))
    st.markdown(f"**답변 엔진:** {'OpenAI (LLM)' if llm_on else '검색 추출형 (키 없음)'}")
    if not llm_on:
        st.info("로컬에서 OPENAI_API_KEY를 .env에 설정하면 LLM 답변이 활성화됩니다. (공개 배포는 키 없이 폴백 전용)")

    st.divider()
    st.subheader("검색 필터")
    aircraft = st.selectbox("기종", ["(전체)"] + config.AIRCRAFT)
    system = st.selectbox("계통", ["(전체)"] + config.SYSTEMS)

st.title("정비 질의응답 콘솔")

if not ensure_index():
    with st.spinner("최초 인덱스 구축 중입니다 (임베딩 모델 다운로드 포함, 1~2분 소요)..."):
        index.build()

tab_chat, tab_verify = st.tabs(["🛠️ 정비 질의응답", "📝 세션 검증·재저장"])

# ---- 탭 1: 채팅형 질의응답 ----
with tab_chat:
    if "chat" not in st.session_state:
        st.session_state.chat = [{
            "role": "assistant",
            "content": "정비 질문을 입력하세요. 기종·계통은 왼쪽 사이드바에서 좁힐 수 있습니다.\n"
                       "예) \"유압 압력이 낮고 경고등이 점등됩니다. 우선 확인할 항목은?\"",
            "sources": [], "mode": None,
        }]

    mode_label = {"llm": "OpenAI 생성", "fallback": "검색 추출형", "no_evidence": "근거 없음"}
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            if msg.get("mode"):
                st.caption(f"처리 모드: {mode_label.get(msg['mode'], msg['mode'])}")
            st.markdown(msg["content"])
            render_sources(msg.get("sources", []))

    st.caption("예시 질문 — 클릭하면 바로 질의됩니다")
    ex_cols = st.columns(2)
    picked = None
    for i, ex in enumerate(EXAMPLES):
        if ex_cols[i % 2].button(ex, key=f"ex{i}", use_container_width=True):
            picked = ex

    if st.button("대화 비우기"):
        del st.session_state["chat"]
        st.rerun()

    user_q = st.chat_input("증상이나 질문을 입력하세요...") or picked
    if user_q:
        st.session_state.chat.append({"role": "user", "content": user_q})
        with st.spinner("검색 및 답변 생성 중..."):
            result = pipeline.answer(
                user_q,
                aircraft=None if aircraft == "(전체)" else aircraft,
                system=None if system == "(전체)" else system,
            )
        st.session_state.chat.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "mode": result["mode"],
        })
        st.rerun()

# ---- 탭 2: 정비사 검증 · 세션 재저장 (폐쇄 루프) ----
with tab_verify:
    st.subheader("정비사 검증 · 세션 재저장")
    st.caption("AI는 최종 판단자가 아닙니다. 정비사가 검증한 결과를 세션으로 저장하면 아카이브가 진화합니다. "
               "(질문은 위 '정비 질의응답' 탭에서 하세요)")

    with st.form("verify"):
        v1, v2, v3 = st.columns(3)
        v_aircraft = v1.selectbox("기종", config.AIRCRAFT, key="v_air")
        v_system = v2.selectbox("계통", config.SYSTEMS, key="v_sys")
        v_symptom = v3.selectbox("증상", config.SYMPTOMS, key="v_sym")
        v_question = st.text_input("질문")
        v_causes = st.text_input("원인 후보 (쉼표로 구분)")
        v_action = st.text_input("조치")
        v_result = st.text_input("결과")
        v_manual = st.text_input("참고 매뉴얼 (쉼표로 구분)")
        v_by = st.text_input("검증 정비사")
        submitted = st.form_submit_button("검증 완료 → 재저장")

        if submitted:
            if not (v_question and v_action and v_result):
                st.error("질문·조치·결과는 필수입니다.")
            else:
                new_id = pipeline.save_verified_session({
                    "aircraft": v_aircraft, "system": v_system, "symptom": v_symptom,
                    "fault_code": "", "question": v_question,
                    "cause_candidates": [c.strip() for c in v_causes.split(",") if c.strip()],
                    "action": v_action, "result": v_result,
                    "manual_refs": [m.strip() for m in v_manual.split(",") if m.strip()],
                    "verified_by": v_by or "미상", "date": "",
                })
                st.success(f"세션 #{new_id} 저장 및 인덱스 재구축 완료")

    st.divider()
    st.caption("관리 도구 — 데이터 파일을 직접 수정했을 때만 사용")
    if st.button("인덱스 재구축"):
        with st.spinner("재구축 중..."):
            n = index.build()
        st.success(f"{n}개 세그먼트 재적재 완료")
