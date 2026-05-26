from knowledge.bm25 import SimpleBM25


def test_bm25_ranks_relevant_higher():
    corpus = [
        "甲木参天 得令 通根",
        "庚金带煞 得水而清",
        "子酉破 穿 父母宫",
    ]
    bm25 = SimpleBM25(corpus)
    ranked = bm25.rank("甲木 得令")
    assert ranked[0][0] == 0
