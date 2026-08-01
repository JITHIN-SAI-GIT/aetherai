class PipelineError(Exception):
    """Base class for all pipeline errors."""
    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")


class PipelineValidationError(PipelineError):
    """Raised when request validation fails inside the pipeline."""
    pass


class PipelineRoutingError(PipelineError):
    """Raised when no provider is available to handle the request."""
    pass


class PipelineStageError(PipelineError):
    """Raised when a generic pipeline stage encounters an unrecoverable error."""
    pass
