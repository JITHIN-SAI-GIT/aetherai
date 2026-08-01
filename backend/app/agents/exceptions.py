class AgentError(Exception):
    pass


class AgentNotFoundError(AgentError):
    def __init__(self, intent: str):
        self.intent = intent
        super().__init__(f"No agent found for intent: {intent!r}")


class AgentRejectedError(AgentError):
    def __init__(self, agent_name: str, reason: str):
        self.agent_name = agent_name
        self.reason = reason
        super().__init__(f"Agent {agent_name!r} rejected request: {reason}")


class AgentConfigError(AgentError):
    def __init__(self, message: str):
        super().__init__(f"Agent configuration error: {message}")
