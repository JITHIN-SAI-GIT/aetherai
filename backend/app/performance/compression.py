import gzip
import logging
from typing import Optional, Tuple

logger = logging.getLogger("performance.compression")

# Minimum response size before compression is applied
_MIN_COMPRESS_BYTES = 1024


class ResponseCompressor:
    """
    Transparent gzip compression for HTTP responses.
    Only compresses if:
    - Client accepts gzip (Accept-Encoding header contains 'gzip')
    - Response body >= _MIN_COMPRESS_BYTES (default 1KB)
    - Content-Type is text-based (json, html, plain, event-stream)
    Application behavior is unchanged for clients that don't accept gzip.
    """

    def compress(
        self,
        content: bytes,
        accept_encoding: str = "",
        content_type: str = "application/json",
    ) -> Tuple[bytes, bool]:
        """
        Returns (body, was_compressed).
        If compressed, the caller must set Content-Encoding: gzip header.
        """
        if not self._should_compress(content, accept_encoding, content_type):
            return content, False

        compressed = gzip.compress(content, compresslevel=6)
        ratio = len(compressed) / len(content)

        # Discard if compression made it larger
        if ratio >= 1.0:
            return content, False

        logger.debug(
            "Response compressed",
            extra={
                "original_bytes": len(content),
                "compressed_bytes": len(compressed),
                "ratio": round(ratio, 3),
            },
        )
        return compressed, True

    def _should_compress(
        self,
        content: bytes,
        accept_encoding: str,
        content_type: str,
    ) -> bool:
        if "gzip" not in accept_encoding.lower():
            return False
        if len(content) < _MIN_COMPRESS_BYTES:
            return False
        compressible_types = (
            "application/json",
            "text/html",
            "text/plain",
            "text/event-stream",
            "application/javascript",
        )
        return any(ct in content_type.lower() for ct in compressible_types)
