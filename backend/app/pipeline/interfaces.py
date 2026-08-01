from typing import Protocol, runtime_checkable
from .context import PipelineContext


@runtime_checkable
class IntentDetectorProtocol(Protocol):
    def detect(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class ContextLoaderProtocol(Protocol):
    async def load(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class SearchDetectorProtocol(Protocol):
    def detect(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class ProviderRouterProtocol(Protocol):
    def route(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class CriticProtocol(Protocol):
    def review(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class FormatterProtocol(Protocol):
    def format(self, context: PipelineContext) -> PipelineContext:
        ...


@runtime_checkable
class MemoryUpdaterProtocol(Protocol):
    async def update(self, context: PipelineContext) -> PipelineContext:
        ...
