import os

from prometheus_client import REGISTRY, Counter, make_asgi_app

CLIENT = os.environ.get("CLIENT_NAME", "metabelly")

llm_tokens = Counter(
    "api_tokens_used_total",
    "LLM API token consumption",
    ["client", "provider", "token_type", "model"],
)


def track_mistral(response) -> None:
    model = response.model or "mistral-small-latest"
    provider = "mistral-small" if any(x in model for x in ("small", "nemo", "7b")) else "mistral"
    usage = response.usage
    if usage:
        llm_tokens.labels(client=CLIENT, provider=provider, token_type="input",  model=model).inc(usage.prompt_tokens)
        llm_tokens.labels(client=CLIENT, provider=provider, token_type="output", model=model).inc(usage.completion_tokens)


metrics_app = make_asgi_app(registry=REGISTRY)
