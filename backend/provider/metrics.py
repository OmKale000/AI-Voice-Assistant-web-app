"""
metrics.py — Shared provider metrics to avoid circular imports.
"""

class ProviderMetrics:
    def __init__(self):
        self.active_provider = "groq"
        self.groq_failures = 0
        self.gemini_failures = 0
        self.fallbacks = 0

    def reset(self):
        self.active_provider = "groq"
        self.groq_failures = 0
        self.gemini_failures = 0
        self.fallbacks = 0

# Global singleton
provider_metrics = ProviderMetrics()
