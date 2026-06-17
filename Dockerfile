# Hugging Face Space (Docker SDK) — Streamlit 정비 질의응답 콘솔
FROM python:3.12-slim

# HF Spaces는 uid 1000 비루트 사용자로 실행 → 쓰기 권한 확보
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface

WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY --chown=user . .

# 이미지 빌드 시 임베딩 모델 다운로드 + 인덱스 사전 구축 (첫 실행 빠르게)
RUN python -m scripts.build_index

EXPOSE 7860
CMD ["streamlit", "run", "app.py", \
     "--server.port=7860", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
