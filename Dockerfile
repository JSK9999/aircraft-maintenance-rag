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

# 임베딩 모델 사전 다운로드 (앱 코드 변경과 무관하게 캐시되어 재배포가 빨라짐)
RUN python -c "from fastembed import TextEmbedding; \
    TextEmbedding(model_name='sentence-transformers/paraphrase-multilingual-mpnet-base-v2')"

COPY --chown=user . .

# 인덱스 사전 구축 (모델은 위에서 캐시됨 → 빠름)
RUN python -m scripts.build_index

EXPOSE 7860
CMD ["streamlit", "run", "app.py", \
     "--server.port=7860", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
