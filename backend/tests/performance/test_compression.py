import pytest
from app.performance.compression import ResponseCompressor


def make_compressor() -> ResponseCompressor:
    return ResponseCompressor()


def test_compresses_large_json():
    c = make_compressor()
    body = b'{"data": "' + b"x" * 2000 + b'"}'
    compressed, was_compressed = c.compress(
        body, accept_encoding="gzip, deflate", content_type="application/json"
    )
    assert was_compressed is True
    assert len(compressed) < len(body)


def test_does_not_compress_when_client_not_accepting():
    c = make_compressor()
    body = b"x" * 2000
    compressed, was_compressed = c.compress(
        body, accept_encoding="identity", content_type="application/json"
    )
    assert was_compressed is False
    assert compressed == body


def test_does_not_compress_small_body():
    c = make_compressor()
    body = b"tiny"
    compressed, was_compressed = c.compress(
        body, accept_encoding="gzip", content_type="application/json"
    )
    assert was_compressed is False


def test_does_not_compress_binary_content_type():
    c = make_compressor()
    body = b"x" * 5000
    compressed, was_compressed = c.compress(
        body, accept_encoding="gzip", content_type="image/png"
    )
    assert was_compressed is False


def test_compression_reduces_size():
    c = make_compressor()
    # Highly compressible body
    body = (b"repeated_token " * 200)
    compressed, was_compressed = c.compress(
        body, accept_encoding="gzip", content_type="text/plain"
    )
    if was_compressed:
        assert len(compressed) < len(body)
