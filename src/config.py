"""프로젝트 설정과 도메인 룰셋.

교수님 코멘트 반영: 온톨로지를 처음부터 완성하지 않고
기종·계통·증상·조치 같은 기본 룰셋만 정의하여 세션이 쌓이면서 진화하도록 한다.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SESSIONS_PATH = DATA_DIR / "sessions.json"
KNOWLEDGE_PATH = DATA_DIR / "knowledge.json"
CHROMA_DIR = ROOT / ".chroma"
COLLECTION = "maintenance"

# 임베딩 모델 (fastembed, ONNX 기반 다국어 - 한국어 지원, torch 불필요)
# 질문-질문 대칭 매칭에 적합한 paraphrase 계열 사용 (프리픽스 불필요)
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# 검색 파라미터
TOP_K = 5
# 코사인 유사도가 이 값보다 낮으면 "근거 자료 없음"으로 처리 (도메인 가드)
# 도메인 패러프레이즈는 0.45 이상, 도메인 밖 질문은 0.25 미만으로 갈린다.
MIN_SIMILARITY = 0.45

# 답변 생성 모델 (OpenAI)
ANSWER_MODEL = "gpt-4o"

# 도메인 룰셋 (검색 필터 및 입력 검증에 사용)
AIRCRAFT = ["KF-16", "T-50", "F-15K"]
SYSTEMS = ["유압", "엔진", "전기", "통신", "착륙장치"]
SYMPTOMS = ["압력 저하", "누유", "경고등", "센서 이상", "배기가스온도 상승", "진동", "송수신 불량", "시동 불량"]
