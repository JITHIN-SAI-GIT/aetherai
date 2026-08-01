class ConversationError(Exception):
    pass

class QualityError(ConversationError):
    def __init__(self, issue: str):
        self.issue = issue
        super().__init__(f"Quality issue: {issue}")

class ClarificationError(ConversationError):
    pass
