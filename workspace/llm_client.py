"""
LLM client helper — OpenRouter (lab default) or direct Anthropic API.

Ubuntu lab: set OPENROUTER_API_KEY in ~/.bashrc.
Claude Code: uses ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN.

Used by common/patterns.py to run ML-style fraud pattern matching over
transaction batches. Keep prompts small and structured — the engine only
sends the pre-filtered candidate transactions here, not the full 1,000.
"""

from __future__ import annotations

import os

import anthropic


def get_llm_client() -> anthropic.Anthropic:
    """Return an Anthropic SDK client configured for OpenRouter or Anthropic direct."""
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        return anthropic.Anthropic(
            api_key=openrouter_key,
            # NOTE: no trailing /v1 here — the Anthropic SDK appends /v1/messages
            # itself. OpenRouter's Anthropic-compatible endpoint is
            # https://openrouter.ai/api/v1/messages; base_url="…/api/v1" would
            # double up to "…/api/v1/v1/messages" and 404 (OpenRouter's website
            # 404 page, not a JSON API error — the request never reaches the API).
            base_url="https://openrouter.ai/api",
            default_headers={
                "HTTP-Referer": "https://github.com/bfsi-claude-lab",
                "X-Title": "BFSI Claude Hands-On Lab",
            },
        )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        return anthropic.Anthropic(api_key=anthropic_key)

    raise RuntimeError(
        "No API key found. Set OPENROUTER_API_KEY (lab default) or ANTHROPIC_API_KEY."
    )


def resolve_model(model: str) -> str:
    """Map Anthropic-style model IDs to OpenRouter IDs when using OpenRouter."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        return model

    mapping = {
        "claude-sonnet-4-5": "anthropic/claude-sonnet-4.5",
        "claude-haiku-4-5": "anthropic/claude-haiku-4.5",
        "claude-opus-4-5": "anthropic/claude-opus-4.5",
        "claude-3-5-sonnet-20241022": "anthropic/claude-3.5-sonnet",
    }
    if model in mapping:
        return mapping[model]
    if "/" in model:
        return model
    return f"anthropic/{model}"
