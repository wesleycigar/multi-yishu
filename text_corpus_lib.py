#!/usr/bin/env python3
"""
木雷易术引擎 - 补充向量语料库（E）
索引 HuggingFace 文本集（44万行），过滤短行/导航杂质后建成补充检索语料
与主 vector_library（典籍正文）互补，供断卦检索更多卦例/口诀佐证
"""
import os, re, math, pickle

KB = os.path.dirname(os.path.abspath(__file__))
PARQUET = os.path.join(KB, "术数文本集", "data", "train-00000-of-00001.parquet")
CACHE = os.path.join(KB, "text_corpus_index.pkl")

NAV = ["来源:","经部","史部","【","书签","www","http","&nbsp;","浏览","目录","版权","本站"]

def clean_row(t):
    t = re.sub(r"\s+", "", t)
    if len(t) < 8 or len(t) > 300:      # 过滤过短/过长
        return None
    if any(n in t for n in NAV):
        return None
    return t

def tokenize(text):
    return [text[i:i+2] for i in range(len(text)-1)] if len(text) >= 2 else [text]

class TextCorpus:
    def __init__(self):
        self.rows, self.df, self.index, self.doc_len, self.n = [], {}, {}, [], 0

    def build(self, limit=None):
        import pandas as pd
        df = pd.read_parquet(PARQUET)
        kept = 0
        for _, row in df.iterrows():
            t = clean_row(str(row["text"]))
            if t is None:
                continue
            self.rows.append(t)
            kept += 1
            if limit and kept >= limit:
                break
        self.n = len(self.rows)
        for bid, t in enumerate(self.rows):
            feats = tokenize(t)
            self.doc_len.append(len(feats))
            tf = {}
            for ft in feats:
                tf[ft] = tf.get(ft, 0) + 1
            for ft in tf:
                self.index.setdefault(ft, {})[bid] = tf[ft]
        for ft, posts in self.index.items():
            self.df[ft] = len(posts)
        print(f"文本集语料: {self.n} 行, {len(self.index)} 特征")

    def search(self, query, k=5):
        qtf = {}
        for ft in tokenize(query):
            qtf[ft] = qtf.get(ft, 0) + 1
        scores = {}
        for ft, q in qtf.items():
            if ft not in self.index:
                continue
            idf = math.log((self.n + 1) / (self.df.get(ft, 0) + 1)) + 1
            for bid, tf in self.index[ft].items():
                scores[bid] = scores.get(bid, 0) + q * idf * (tf / math.sqrt(self.doc_len[bid]))
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
        return [{"score": round(sc,4), "text": self.rows[bid][:180]} for bid, sc in ranked]

    def save(self):
        with open(CACHE, "wb") as f:
            pickle.dump({"rows": self.rows, "df": self.df, "index": self.index,
                         "doc_len": self.doc_len, "n": self.n}, f)

    def load(self):
        with open(CACHE, "rb") as f:
            d = pickle.load(f)
        self.rows, self.df = d["rows"], d["df"]
        self.index, self.doc_len, self.n = d["index"], d["doc_len"], d["n"]

_lib = None
def get_corpus(reuse_cache=True):
    global _lib
    if _lib is None:
        _lib = TextCorpus()
        if reuse_cache and os.path.exists(CACHE):
            _lib.load()
        else:
            _lib.build(); _lib.save()
    return _lib

def search_corpus(query, k=3):
    try:
        return get_corpus().search(query, k=k)
    except Exception:
        return []

if __name__ == "__main__":
    c = get_corpus(reuse_cache=False)
    print("\n=== 文本集检索测试 ===")
    for r in c.search("官鬼持世 求财 妻财 应期"):
        print(f"  {r['text'][:70]}")
    print("\n=== 文本集检索测试2 ===")
    for r in c.search("六爻 月建 日辰 旺衰 断卦"):
        print(f"  {r['text'][:70]}")
