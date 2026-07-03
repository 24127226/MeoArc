# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/embeddings.py — TÌM THEO Ý NGHĨA (semantic, UC005)        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Ý tưởng: đổi CHỮ thành VECTOR (Gemini gemini-embedding-001) rồi so  ║
# ║ độ gần cosine → "thư về tiền nong" khớp được "Invoice #123" dù      ║
# ║ không chung từ nào. Đây là bản re-rank TẠI THỜI ĐIỂM HỎI trên nhóm  ║
# ║ ứng viên nhỏ (~30 thư gần nhất) — KHÔNG cần cài pgvector/đánh index ║
# ║ (pgvector là đường nâng cấp khi cần persist embeddings, xem Design).║
# ║ Quota embedding TÁCH RIÊNG quota chat → không ăn lượt Gemini chat.  ║
# ╚══════════════════════════════════════════════════════════════════╝

import hashlib
import math

from app.core.config import settings

_EMBED_MODEL = "models/gemini-embedding-001"  # model key hiện có hỗ trợ (probe 02/07)

_embedder = None

# NFR-Memory/Speed: cache vector theo NỘI DUNG (hash) — cùng 1 thư được hỏi lại
# thì khỏi embed lại (tiết kiệm API + nhanh). Trần 512 mục, FIFO.
_VEC_CACHE: dict[str, list[float]] = {}
_VEC_CACHE_MAX = 512


def _get_embedder():
    """Client embeddings (lazy singleton). Chưa có AI_API_KEY → RuntimeError để tool báo lỗi đẹp."""
    global _embedder
    if _embedder is None:
        if not settings.ai_api_key:
            raise RuntimeError("Chưa cấu hình AI_API_KEY nên không dùng được tìm kiếm ngữ nghĩa.")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        _embedder = GoogleGenerativeAIEmbeddings(
            model=_EMBED_MODEL, google_api_key=settings.ai_api_key,
        )
    return _embedder


def cosine(a: list[float], b: list[float]) -> float:
    """Độ gần cosine ∈ [-1, 1] — càng lớn càng giống nghĩa. Thuần toán, test được offline."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def rank_by_similarity(query_vec: list[float], doc_vecs: list[list[float]],
                       top_k: int) -> list[tuple[int, float]]:
    """Xếp hạng tài liệu theo độ gần với câu hỏi. Trả [(chỉ_số_gốc, điểm)] giảm dần.
    Thuần toán (không mạng) → unit-test khách quan được."""
    scored = [(i, cosine(query_vec, v)) for i, v in enumerate(doc_vecs)]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:max(1, top_k)]


def _cache_key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed 1 lô văn bản, có cache theo nội dung (thư cũ hỏi lại = 0 API call)."""
    out: list[list[float] | None] = [None] * len(texts)
    missing_idx, missing_txt = [], []
    for i, t in enumerate(texts):
        v = _VEC_CACHE.get(_cache_key(t))
        if v is not None:
            out[i] = v
        else:
            missing_idx.append(i)
            missing_txt.append(t)
    if missing_txt:
        fresh = _get_embedder().embed_documents(missing_txt)
        for i, t, v in zip(missing_idx, missing_txt, fresh):
            out[i] = v
            if len(_VEC_CACHE) >= _VEC_CACHE_MAX:
                _VEC_CACHE.pop(next(iter(_VEC_CACHE)))
            _VEC_CACHE[_cache_key(t)] = v
    return out  # type: ignore[return-value]


def embed_query(text: str) -> list[float]:
    """Embed CÂU HỎI (không cache — câu hỏi mỗi lần mỗi khác)."""
    return _get_embedder().embed_query(text)
