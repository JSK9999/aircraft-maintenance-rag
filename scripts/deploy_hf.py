"""Hugging Face Space로 배포한다 (Streamlit SDK, 폴백 전용 = 키 없음).

사용법:
    HF_TOKEN=hf_xxx .venv/bin/python -m scripts.deploy_hf <user>/<space-name>

예:
    HF_TOKEN=hf_xxx .venv/bin/python -m scripts.deploy_hf JSK9999/aircraft-maintenance-rag

토큰은 huggingface.co/settings/tokens 에서 'write' 권한으로 발급한다.
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
    token = os.getenv("HF_TOKEN")
    if not token:
        sys.exit("HF_TOKEN 환경변수가 필요합니다 (huggingface.co/settings/tokens, write 권한).")

    api = HfApi(token=token)
    api.create_repo(repo_id, repo_type="space", space_sdk="streamlit", exist_ok=True)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api.upload_folder(folder_path=root, repo_id=repo_id, repo_type="space",
                      ignore_patterns=IGNORE)
    print(f"배포 완료 → https://huggingface.co/spaces/{repo_id}")


if __name__ == "__main__":
    main()
