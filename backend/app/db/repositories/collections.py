from .base import BaseMongoRepository

class UserRepository(BaseMongoRepository):
    collection_name = "users"

class ConversationRepository(BaseMongoRepository):
    collection_name = "conversations"

class MessageRepository(BaseMongoRepository):
    collection_name = "messages"

class MemoryRepository(BaseMongoRepository):
    collection_name = "memory"

class PreferenceRepository(BaseMongoRepository):
    collection_name = "preferences"

class ProjectRepository(BaseMongoRepository):
    collection_name = "projects"

class ProviderRepository(BaseMongoRepository):
    collection_name = "providers"

class SessionRepository(BaseMongoRepository):
    collection_name = "sessions"

class SearchCacheRepository(BaseMongoRepository):
    collection_name = "search_cache"

class MetricsRepository(BaseMongoRepository):
    collection_name = "metrics"

class FeedbackRepository(BaseMongoRepository):
    collection_name = "feedback"
