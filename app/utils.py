import re


def slugify(text: str, *, sep: str = "-", max_len: int = 80, fallback: str = "") -> str:
    """Lowercase, collapse non-alphanumerics to `sep`, trim and cap length.

    Used for both article slugs (sep="-") and author handles (sep="_").
    """
    cleaned = re.sub(r"<[^>]+>", " ", text)  # strip any tags first
    s = re.sub(r"[^a-z0-9]+", sep, cleaned.lower()).strip(sep)[:max_len].strip(sep)
    return s or fallback
