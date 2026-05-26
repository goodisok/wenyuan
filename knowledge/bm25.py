# -*- coding: utf-8 -*-
"""轻量 BM25，用于语料文本重排（中文按字切分）。"""
from __future__ import annotations

import math
import re
from typing import Iterable


def _tokenize(text: str) -> list[str]:
    text = re.sub(r"\s+", "", text or "")
    if not text:
        return []
    tokens: list[str] = []
    for i, ch in enumerate(text):
        if "\u4e00" <= ch <= "\u9fff":
            tokens.append(ch)
            if i + 1 < len(text) and "\u4e00" <= text[i + 1] <= "\u9fff":
                tokens.append(ch + text[i + 1])
    return tokens


class SimpleBM25:
    def __init__(self, corpus: list[str], *, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs = [_tokenize(d) for d in corpus]
        self.nd = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / self.nd if self.nd else 0.0
        df: dict[str, int] = {}
        for doc in self.docs:
            for t in set(doc):
                df[t] = df.get(t, 0) + 1
        self.idf = {
            t: math.log(1 + (self.nd - freq + 0.5) / (freq + 0.5))
            for t, freq in df.items()
        }

    def score(self, query: str, doc_index: int) -> float:
        if doc_index < 0 or doc_index >= self.nd:
            return 0.0
        q_tokens = _tokenize(query)
        if not q_tokens:
            return 0.0
        doc = self.docs[doc_index]
        dl = len(doc)
        tf: dict[str, int] = {}
        for t in doc:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for t in q_tokens:
            if t not in tf:
                continue
            idf = self.idf.get(t, 0.0)
            freq = tf[t]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            score += idf * freq * (self.k1 + 1) / denom
        return score

    def rank(self, query: str, indices: Iterable[int] | None = None) -> list[tuple[int, float]]:
        pool = list(indices) if indices is not None else list(range(self.nd))
        scored = [(i, self.score(query, i)) for i in pool]
        scored.sort(key=lambda x: -x[1])
        return scored
