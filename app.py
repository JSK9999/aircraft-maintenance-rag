"""정비 질의응답 콘솔 (Streamlit).

입력(기종/계통/증상/질문) → AI 응답(원인 후보·점검 순서) → 출처(유사 세션·매뉴얼) → 정비사 검증·재저장.
실행:  streamlit run app.py
"""
import os

from dotenv import load_dotenv
import streamlit as st

from src import config, index, pipeline

load_dotenv()

st.set_page_config(page_title="항공기 정비 세션 아카이브 RAG", page_icon="🛩️", layout="wide")


def ensure_index() -> bool:
    try:
        index.get_collection()
        return True
    except Exception:
        return False


# ---- 사이드바: 상태 / 인덱스 관리 ----
with st.sidebar:
    st.header("🛩️ 정비 세션 아카이브")
    st.caption("도메인 특화 RAG · 항공기 정비 질의응답 MVP")

    llm_on = bool(os.getenv("OPENAI_API_KEY"))
    st.markdown(f"**답변 엔진:** {'OpenAI (LLM)' if llm_on else '검색 추출형 (키 없음)'}")
    if not llm_on:
        st.info("로컬에서 OPENAI_API_KEY를 .env에 설정하면 LLM 답변이 활성화됩니다. (공개 배포는 키 없이 폴백 전용)")

    indexed = ensure_index()
    st.markdown(f"**인덱스 상태:** {'준비됨 ✅' if indexed else '미구축 ⚠️'}")
    if st.button("인덱스 구축/재구축", use_container_width=True):
        with st.spinner("임베딩 및 적재 중... (최초 1회 모델 다운로드)"):
            n = index.build()
        st.success(f"{n}개 세그먼트 적재 완료")
        st.rerun()

st.title("정비 질의응답 콘솔")

if not ensure_index():
    with st.spinner("최초 인덱스 구축 중입니다 (임베딩 모델 다운로드 포함, 1~2분 소요)..."):
        index.build()

# ---- 입력 영역 ----
st.subheader("정비사 입력")
c1, c2, c3 = st.columns(3)
aircraft = c1.selectbox("기종", ["(전체)"] + config.AIRCRAFT)
system = c2.selectbox("계통", ["(전체)"] + config.SYSTEMS)
symptom = c3.selectbox("증상(참고)", ["(선택 안 함)"] + config.SYMPTOMS)
default_q = "유압 압력이 정상보다 낮습니다. 우선 확인할 항목은 무엇인가요?"
query = st.text_area("질문", value=default_q, height=90)

if st.button("유사 사례 검색 + 답변", type="primary"):
    if not query.strip():
        st.error("질문을 입력하세요.")
    else:
        with st.spinner("검색 및 답변 생성 중..."):
            result = pipeline.answer(
                query,
                aircraft=None if aircraft == "(전체)" else aircraft,
                system=None if system == "(전체)" else system,
            )
        st.session_state["result"] = result

# ---- AI 응답 영역 ----
result = st.session_state.get("result")
if result:
    st.subheader("AI 응답")
    mode_label = {"llm": "OpenAI 생성", "fallback": "검색 추출형", "no_evidence": "근거 없음"}
    st.caption(f"처리 모드: {mode_label.get(result['mode'], result['mode'])}")

    if result["mode"] == "no_evidence":
        st.error(result["answer"])
    else:
        st.markdown(result["answer"])

        st.markdown("##### 출처")
        for ref in result["sources"]:
            manuals = " · ".join(ref["manuals"]) if ref["manuals"] else "-"
            st.markdown(
                f"- **{ref['title']}** (유사도 {ref['similarity']}, {ref['kind']}) "
                f"— 근거: {manuals}"
            )

        with st.expander("유사 세션·자료 원문 보기"):
            for ref in result["sources"]:
                st.write(f"**{ref['title']}** — 유사도 {ref['similarity']}")

# ---- 정비사 검증 · 재저장 (폐쇄 루프) ----
st.divider()
st.subheader("정비사 검증 · 세션 재저장")
st.caption("AI는 최종 판단자가 아닙니다. 정비사가 검증한 결과를 세션으로 저장하면 아카이브가 진화합니다.")

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
