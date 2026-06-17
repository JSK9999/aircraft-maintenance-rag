"""인덱스 구축 CLI:  python -m scripts.build_index"""
from src import index

if __name__ == "__main__":
    n = index.build()
    print(f"인덱스 구축 완료: {n}개 세그먼트 적재 → {index.config.CHROMA_DIR}")
