---
title: 항공기 정비 세션 아카이브 RAG
emoji: 🛩️
colorFrom: blue
colorTo: gray
sdk: streamlit
app_file: app.py
pinned: false
---

# 항공기 정비 세션 아카이브 — 도메인 특화 RAG MVP

정비사의 질문에 **과거 정비 사례와 매뉴얼을 근거로** 답변하고, **출처를 함께 제시**하는 도메인 특화 RAG 시스템입니다. 정비 지식의 **축적 · 검색 · 재사용**에 집중한 최소 기능 제품(MVP)입니다.

> AI는 최종 판단자가 아닙니다. 모든 답변은 출처와 함께 제공되며 **정비사의 검증**을 거칩니다.

## 무엇을 하나

```
정비사 질문 → 유사 사례 검색(Top-K) → 근거 기반 답변 → 출처 제공 → 정비사 검증 → 재저장(폐쇄 루프)
```

- **도메인 한정**: 항공정비(기종·계통·증상·조치) 자료 안에서만 답변. 근거가 약하면 **"근거 자료 없음"**.
- **의미 기반 검색**: 표현이 달라도 의미가 가까운 질문을 찾음 (예: "압력이 낮다" ↔ "압력 상승이 안 된다").
- **룰셋만**: 온톨로지를 처음부터 완성하지 않고 기종/계통/증상/조치 기본 분류만 부여 → 세션이 쌓이며 진화.
- **폐쇄 루프**: 정비사가 검증한 세션이 다시 검색 대상이 되어 아카이브가 성장.

## 기술 구성

| 구성 | 선택 | 이유 |
|------|------|------|
| 임베딩 | `fastembed` (ONNX, 다국어 mpnet) | torch 불필요·오프라인·키 불필요 |
| 벡터 DB | `chromadb` (로컬 영속) | 메타데이터 필터(기종/계통) + Top-K 유사검색 |
| 답변 생성 | OpenAI (`gpt-4o`) **선택** | 키 없으면 검색 추출형으로 자동 폴백 |
| UI | Streamlit | 기획서의 정비 질의응답 콘솔 |

## 설치 및 실행

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# (선택) OpenAI 답변 생성 활성화 — 키가 없으면 검색 추출형으로 동작
# 키는 로컬에서만 사용하세요. 공개 배포에는 키를 두지 않습니다.
cp .env.example .env   # .env에 OPENAI_API_KEY 입력

# 인덱스 구축 (최초 1회 임베딩 모델 자동 다운로드, 약 1GB)
python -m scripts.build_index

# 콘솔 실행
streamlit run app.py
```

Streamlit 사이드바의 **"인덱스 구축/재구축"** 버튼으로도 인덱스를 만들 수 있습니다.

## 데이터 (더미)

- `data/sessions.json` — 정비 세션 16건 (KF-16 / T-50 / F-15K, 유압·엔진·전기·통신·착륙장치)
- `data/knowledge.json` — 매뉴얼·FAQ·체크리스트 12건

실제 정비 데이터가 아닌 **데모용 더미 데이터**입니다.

## 구조

```
src/
  config.py     도메인 룰셋·설정
  embedder.py   다국어 임베딩 (fastembed)
  index.py      세그먼트화 → 임베딩 → Chroma 적재
  retriever.py  Top-K 검색 + 도메인 가드(근거 자료 없음)
  generator.py  근거 기반 답변 (OpenAI / 추출형 폴백)
  pipeline.py   오케스트레이션 + 검증 세션 재저장
app.py          정비 질의응답 콘솔 (Streamlit)
scripts/build_index.py   인덱스 구축 CLI
```

## 한계 (MVP 범위)

- 더미 데이터 기반이며 실제 정비 판단에 사용할 수 없습니다.
- 유사 사례가 없으면 답변하지 않습니다(근거 자료 없음). 무근거 추론은 의도적으로 배제했습니다.
- 고장예측·일정최적화·부품수요예측은 범위에 포함하지 않습니다(향후 확장).
