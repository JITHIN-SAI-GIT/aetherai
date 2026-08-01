import re
import unicodedata
import hashlib
from typing import Optional


class QueryNormalizer:
    """
    Normalizes a raw query string into a stable, cache-safe form.

    Steps:
      1. Unicode NFC normalization
      2. Lowercase
      3. Strip leading/trailing whitespace
      4. Remove punctuation (except hyphens inside words)
      5. Collapse multiple spaces into one
      6. Sort tokens alphabetically (for cache-key stability across equivalent queries)
    """

    def normalize(self, query: str) -> str:
        """Return a normalized query string."""
        text = unicodedata.normalize("NFC", query)
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)          # strip punctuation
        text = re.sub(r"\s+", " ", text).strip()      # collapse spaces
        return text

    def cache_key(self, query: str, prefix: str = "search") -> str:
        """
        Produce a deterministic Redis cache key.
        Tokens are sorted so 'AI news latest' and 'latest AI news' share the same key.
        """
        normalized = self.normalize(query)
        tokens = sorted(normalized.split())
        canonical = " ".join(tokens)
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        return f"{prefix}:{digest}"
