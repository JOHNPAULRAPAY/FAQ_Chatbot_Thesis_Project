class ConversationState:
    def __init__(self):
        self.fallback_count = 0
        self.context = {}

    def record_fallback(self):
        self.fallback_count += 1

    def reset_fallback(self):
        self.fallback_count = 0

    def remember(self, key: str, value):
        self.context[key] = value

    def recall(self, key:str, default = None):
        return self.context.get(key, default)