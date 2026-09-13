"""
Optional LLM layer: activates only when both rules and ML fail to
confidently understand the message. Currently STUBBED - no real API
calls are made, so this costs nothing to run or demonstrate.

To activate with a real API later:
1. Sign up at console.anthropic.com (or another provider)
2. Set your API key as an environment variable (never hardcode it)
3. Uncomment the real implementation below and remove the stub
"""
import os

# Sentinel: is a real API key configured? If not, we stay in stub mode.
LLM_ENABLED = os.environ.get("ANTHROPIC_API_KEY") is not None


def ask_llm(user_message: str) -> str | None:
    """
    Attempts to get an LLM-generated answer for a message that rules
    and ML both failed to classify confidently.

    Returns None if the LLM layer is disabled/unavailable, so the
    caller can gracefully fall back to the standard fallback message.
    This is the key safety property: the chatbot must work correctly
    even with LLM_ENABLED = False.
    """
    if not LLM_ENABLED:
        return None  # LLM not configured - caller falls back gracefully

    # --- Real implementation (uncomment once you have an API key) ---
    #
    # import anthropic
    # client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env automatically
    #
    # system_prompt = (
    #     "You are a narrow-purpose FAQ assistant for a school. "
    #     "Only answer questions about admissions, tuition, enrollment, "
    #     "or academic programs, using general knowledge about typical "
    #     "school processes. If the question is unrelated to these topics, "
    #     "or you are not confident in the answer, say clearly that you "
    #     "don't know and suggest the student contact the school office. "
    #     "Keep answers to 2-3 sentences."
    # )
    #
    # response = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=150,
    #     system=system_prompt,
    #     messages=[{"role": "user", "content": user_message}]
    # )
    #
    # answer = response.content[0].text.strip()
    #
    # # Basic sanity check before trusting the output
    # if len(answer) > 500 or not answer:
    #     return None
    #
    # return answer

    return None  # placeholder while real implementation is commented out