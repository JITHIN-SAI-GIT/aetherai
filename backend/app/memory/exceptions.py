class MemoryError(Exception):
    pass

class MemoryStorageError(MemoryError):
    def __init__(self, backend: str, message: str):
        self.backend = backend
        super().__init__(f"[{backend}] {message}")

class MemoryPrivacyError(MemoryError):
    """Raised when a privacy operation is attempted without proper confirmation."""
    pass

class MemoryExtractionError(MemoryError):
    """Raised when the extractor encounters an unrecoverable parsing error."""
    pass
