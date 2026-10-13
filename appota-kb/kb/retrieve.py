"""Retrieval trên tập tài liệu ĐÃ LỌC QUYỀN + chọn bản ưu tiên + phát hiện mâu thuẫn.

Không dùng AI. Quy tắc ưu tiên xác định: cấp cụ thể hơn thắng
(team > dept > company > group); cùng cấp thì bản có effective_date mới hơn thắng;
cùng cấp và cùng ngày mà là hai tài liệu khác nhau -> CONFLICT (không tự chọn).
"""
import math
import re
from collections import Counter, defaultdict

SCOPE_RANK = {"group": 0, "company": 1, "dept": 2, "team": 3}

# Từ hỏi/từ nối quá phổ biến, không mang nghĩa tìm kiếm
STOPWORDS = {
    "của", "tôi", "mình", "em", "anh", "chị", "như", "thế", "nào", "là", "gì", "có",
    "không", "được", "bao", "nhiêu", "thì", "và", "cho", "với", "các", "những", "một",
    "quy", "định", "quy_định", "cần", "phải", "hãy", "xin", "ở", "về", "khi", "nếu",
    "mấy", "sao", "làm", "thế_nào",
}

MIN_COVERAGE = 0.6   # tài liệu phải chứa >= 60% từ khóa của câu hỏi (0.5 từng cho kết quả nhiễu)
MIN_SCORE = 0.5      # điểm BM25 tối thiểu
TOPIC_SCORE_RATIO = 0.5  # chỉ giữ chủ đề có điểm >= 50% điểm cao nhất


def tokenize(text):
    toks = re.findall(r"\w+", text.lower())
    return toks


def query_terms(question):
    return [t for t in tokenize(question) if t not in STOPWORDS]


def _doc_tokens(doc):
    return tokenize(doc["title"] + " " + doc["text"])


def bm25_scores(terms, docs, k1=1.5, b=0.75):
    """BM25 tự cài (idf luôn dương, ổn định với tập rất nhỏ)."""
    tokenized = [_doc_tokens(d) for d in docs]
    n = len(docs)
    if n == 0:
        return []
    avgdl = sum(len(t) for t in tokenized) / n
    df = Counter()
    for toks in tokenized:
        for term in set(toks):
            df[term] += 1
    scores = []
    for toks in tokenized:
        tf = Counter(toks)
        dl = len(toks)
        s = 0.0
        for term in terms:
            if tf[term] == 0:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * dl / avgdl))
        scores.append(s)
    return scores


def _coverage(terms, doc):
    if not terms:
        return 0.0
    toks = set(_doc_tokens(doc))
    return sum(1 for t in set(terms) if t in toks) / len(set(terms))


def resolve_topic(docs):
    """Cho các tài liệu cùng topic: trả về (primary, lower_priority, conflict)."""
    ranked = sorted(docs, key=lambda d: (SCOPE_RANK[d["scope"]], d["effective_date"]),
                    reverse=True)
    top_key = (SCOPE_RANK[ranked[0]["scope"]], ranked[0]["effective_date"])
    top = [d for d in ranked
           if (SCOPE_RANK[d["scope"]], d["effective_date"]) == top_key]
    rest = [d for d in ranked if d not in top]
    return top, rest, len(top) > 1


def retrieve(question, allowed_docs):
    """Trả về dict:
    status: 'ok' | 'conflict' | 'no_answer'
    topics: list {topic, primary, lower_priority, conflict}
    scores: {doc_id: điểm}
    reason: lý do khi no_answer
    """
    terms = query_terms(question)
    if not terms:
        return {"status": "no_answer", "topics": [], "scores": {},
                "reason": "câu hỏi quá chung chung, không có từ khóa để tìm"}

    scores = bm25_scores(terms, allowed_docs)
    hits = []
    for d, s in zip(allowed_docs, scores):
        if s >= MIN_SCORE and _coverage(terms, d) >= MIN_COVERAGE:
            hits.append((d, s))
    score_map = {d["doc_id"]: round(s, 3) for d, s in zip(allowed_docs, scores)}
    if not hits:
        return {"status": "no_answer", "topics": [], "scores": score_map,
                "reason": "không có tài liệu phù hợp trong phạm vi được phép truy cập"}

    by_topic = defaultdict(list)
    for d, s in hits:
        by_topic[d["topic"]].append((d, s))
    topic_best = {t: max(s for _, s in items) for t, items in by_topic.items()}
    cutoff = max(topic_best.values()) * TOPIC_SCORE_RATIO

    topics, any_conflict = [], False
    for t, items in by_topic.items():
        if topic_best[t] < cutoff:
            continue
        primary, rest, conflict = resolve_topic([d for d, _ in items])
        any_conflict = any_conflict or conflict
        topics.append({"topic": t, "primary": primary,
                       "lower_priority": rest, "conflict": conflict})
    return {"status": "conflict" if any_conflict else "ok",
            "topics": topics, "scores": score_map, "reason": ""}
