#!/usr/bin/env python3
"""
木雷易术引擎 - 轻量向量检索库（C：语料增强）
字符bigram TF-IDF + 余弦相似度，索引各模块典籍正文
供断卦/解读时检索相关原文片段，做语料增强
"""
import os, re, math, json, pickle

KB = os.path.dirname(os.path.abspath(__file__))
MODULES = ["01_经部易类","03_六爻纳甲","04_子平八字","05_梅花易数",
           "06_奇门遁甲","07_风水堪舆","08_式盘类"]
CACHE = os.path.join(KB, "vector_index.pkl")

def chunk_text(text, size=180, overlap=40):
    """切成长块，带重叠"""
    text = re.sub(r"\s+", "", text)
    if len(text) <= size:
        return [text] if text else []
    out = []
    i = 0
    while i < len(text):
        out.append(text[i:i+size])
        i += size - overlap
    return out

def tokenize(text):
    """字符 bigram 特征"""
    if len(text) < 2:
        return [text]
    return [text[i:i+2] for i in range(len(text)-1)]

class VectorLibrary:
    def __init__(self):
        self.blocks = []          # 每条: {"text":..., "book":..., "module":...}
        self.df = {}              # 特征 -> 文档数
        self.doc_len = []         # 每块特征数
        self.index = {}           # 特征 -> {block_id: tf}
        self.n = 0

    def build(self):
        """索引各模块典籍正文"""
        for mod in MODULES:
            d = os.path.join(KB, mod)
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if not f.endswith((".txt",".md")):
                    continue
                fp = os.path.join(d, f)
                try:
                    raw = open(fp, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                book = f.replace(".txt","").replace(".md","")
                for blk in chunk_text(raw):
                    self.blocks.append({"text": blk, "book": book, "module": mod})
        self.n = len(self.blocks)
        # 建倒排
        for bid, blk in enumerate(self.blocks):
            feats = tokenize(blk["text"])
            self.doc_len.append(len(feats))
            tf = {}
            for ft in feats:
                tf[ft] = tf.get(ft, 0) + 1
            for ft in tf:
                self.index.setdefault(ft, {})[bid] = tf[ft]
        # df
        for ft, posts in self.index.items():
            self.df[ft] = len(posts)
        print(f"索引完成: {self.n} 个语块, {len(self.index)} 个特征")

    def search(self, query, k=5, module=None):
        """返回相关原文片段（带来源）"""
        qfeats = tokenize(query)
        if not qfeats:
            return []
        qtf = {}
        for ft in qfeats:
            qtf[ft] = qtf.get(ft, 0) + 1
        scores = {}
        for ft, q in qtf.items():
            if ft not in self.index:
                continue
            idf = math.log((self.n + 1) / (self.df.get(ft, 0) + 1)) + 1
            for bid, tf in self.index[ft].items():
                blk = self.blocks[bid]
                if module and blk["module"] != module:
                    continue
                norm = math.sqrt(self.doc_len[bid])
                scores[bid] = scores.get(bid, 0) + (q * idf * (tf / norm))
        # 查询归一化
        qnorm = math.sqrt(sum(q*idf for q in qtf.values() for idf in [1]))
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
        out = []
        for bid, sc in ranked:
            blk = self.blocks[bid]
            out.append({"score": round(sc, 4), "book": blk["book"],
                        "module": blk["module"], "text": blk["text"][:180]})
        return out

    def save(self, path=CACHE):
        with open(path, "wb") as f:
            pickle.dump({"blocks": self.blocks, "df": self.df,
                         "doc_len": self.doc_len, "index": self.index, "n": self.n}, f)
        print(f"索引已缓存: {path}")

    def load(self, path=CACHE):
        with open(path, "rb") as f:
            d = pickle.load(f)
        self.blocks, self.df = d["blocks"], d["df"]
        self.doc_len, self.index, self.n = d["doc_len"], d["index"], d["n"]
        print(f"已加载缓存索引: {self.n} 语块")

_lib = None
def get_lib(reuse_cache=True):
    global _lib
    if _lib is None:
        _lib = VectorLibrary()
        if reuse_cache and os.path.exists(CACHE):
            _lib.load()
        else:
            _lib.build(); _lib.save()
    return _lib

def enhance(query, k=3, module=None):
    """断卦语料增强：返回相关原文片段"""
    try:
        lib = get_lib()
        return lib.search(query, k=k, module=module)
    except Exception:
        return []

if __name__ == "__main__":
    lib = get_lib(reuse_cache=False)
    print("\n=== 检索测试：'官鬼持世 财运 求财' ===")
    for r in lib.search("官鬼 财爻 求财 妻财"):
        print(f"  [{r['book']}] {r['text'][:60]}")
    print("\n=== 检索测试：'梅花 体用 生克 旺衰' ===")
    for r in lib.search("体用生克 旺衰 梅花 起卦"):
        print(f"  [{r['book']}] {r['text'][:60]}")
