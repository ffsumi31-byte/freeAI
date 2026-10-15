"""BrickForge AI v8 — fail-safe build pipeline + 10k Context Upgrade.
Upgraded to enforce a 10,240 token context window and intelligent history trimming.
"""
import ollama  # Or your direct local client wrapper


def trim_history_to_limit(messages, max_tokens=10000):
  """Estimates tokens (~4 chars per token) and drops old messages

  when passing the 10k threshold to protect local memory and prevent overflow.
  """
  # Rough heuristic: ~4 characters per token for general text/code
  def est_tokens(text):
    return len(str(text)) // 4

  total_tokens = sum(est_tokens(m.get("content", "")) for m in messages)
  if total_tokens <= max_tokens:
    return messages

  # Separate system prompt if present to preserve instructions
  system_msg = messages[0] if messages and messages[0]["role"] == "system" else None
  history = messages[1:] if system_msg else messages

  # Pop oldest messages until we fit safely under the 10k limit
  while history and (sum(est_tokens(m.get("content", "")) for m in history)) > (
      max_tokens - 500
  ):
    history.pop(0)

  return ([system_msg] if system_msg else []) + history


def ask_local_brain(messages_history, model_name="llama3"):
  """Sends your message history to the local AI host with a forced 10k context window."""
  # 1. Automatically trim history to stay safely under your 10k limit
  managed_messages = trim_history_to_limit(messages_history, max_tokens=10000)

  # 2. Call local model with explicit options forcing 10k context
  response = ollama.chat(
      model=model_name,
      messages=managed_messages,
      options={
          "num_ctx": 10240,  # Forces local runtime to allocate 10k context buffer
          "temperature": 0.7,
      },
  )

  return response["message"]["content"]
