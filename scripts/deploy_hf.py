"""Hugging Face Space로 배포한다 (Streamlit SDK, 폴백 전용 = 키 없음).

먼저 한 번 로그인(토큰은 로컬에만 저장, 채팅에 붙이지 말 것):
    hf auth login

이후 배포:
    .venv/bin/python -m scripts.deploy_hf <user>/<space-name>

예:
    .venv/bin/python -m scripts.deploy_hf JSK9999/aircraft-maintenance-rag

토큰은 huggingface.co/settings/tokens 에서 'write' 권한으로 발급한다.
HF_TOKEN 환경변수가 있으면 그것을, 없으면 `hf auth login`으로 저장된 토큰을 사용한다.
공개 Space에는 OPENAI_API_KEY를 설정하지 않으므로 검색 추출형 폴백으로만 동작한다.
"""
import os
import sys

from huggingface_hub import HfApi

IGNORE = [".venv/*", ".chroma/*", ".env", "*.pyc", "**/__pycache__/*", ".git/*"]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("사용법: python -m scripts.deploy_hf <user>/<space-name>")
    repo_id = sys.argv[1]
    # HF_TOKEN 환경변수 → 없으면 `hf auth login`으로 저장된 토큰 자동 사용
    api = HfApi(token=os.getenv("HF_TOKEN"))
    api.create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api.upload_folder(folder_path=root, repo_id=repo_id, repo_type="space",
                      ignore_patterns=IGNORE)
    print(f"배포 완료 → https://huggingface.co/spaces/{repo_id}")


if __name__ == "__main__":
    main()
