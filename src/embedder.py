"""fastembed 기반 다국어 임베딩 래퍼.

ONNX 런타임을 사용하므로 torch 없이 동작하고, clone 후 첫 실행 시 모델을 자동 내려받는다.
paraphrase-multilingual 계열은 대칭 모델이라 별도 접두 없이 질의·문서를 동일하게 임베딩한다.
"""
from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from . import config


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=config.EMBED_MODEL)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def embed_passages(texts: list[str]) -> list[list[float]]:
    vectors = np.array(list(_model().embed(texts)))
    return _normalize(vectors).tolist()


def embed_query(text: str) -> list[float]:
    vectors = np.array(list(_model().embed([text])))
    return _normalize(vectors)[0].tolist()
