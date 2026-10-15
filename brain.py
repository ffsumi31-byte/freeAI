"""BrickForge AI v8 — fail-safe build pipeline + 10k Context Upgrade (Pure HTTP)."""
import json
import urllib.request
# ... [Keep your existing imports, SPECIES, ROOTS, BUILDERS, etc., below] ...

LOCAL_API_URL = "http://localhost:11434/api/chat"


def trim_history_to_limit(messages, max_tokens=10000):
  """Estimates tokens (~4 chars per token) and drops old messages

  when passing the 10k threshold to protect local memory and prevent overflow.
  """
  def est_tokens(text):
    return len(str(text)) // 4

  total_tokens = sum(est_tokens(m.get("content", "")) for m in messages)
  if total_tokens <= max_tokens:
    return messages

  system_msg = messages[0] if messages and messages[0]["role"] == "system" else None
  history = messages[1:] if system_msg else messages

  while history and (sum(est_tokens(m.get("content", "")) for m in history)) > (
      max_tokens - 500
  ):
    history.pop(0)

  return ([system_msg] if system_msg else []) + history


def ask_local_brain(messages_history, model_name="llama3"):
  """Sends message history via pure HTTP to your local AI host with a 10k context window."""
  managed_messages = trim_history_to_limit(messages_history, max_tokens=10000)

  payload = {
      "model": model_name,
      "messages": managed_messages,
      "options": {
          "num_ctx": 10240,  # Forces local runtime to allocate 10k context buffer
          "temperature": 0.7,
      },
      "stream": False,
  }

  req = urllib.request.Request(
      LOCAL_API_URL,
      data=json.dumps(payload).encode("utf-8"),
      headers={"Content-Type": "application/json"},
      method="POST",
  )

  try:
    with urllib.request.urlopen(req) as response:
      res_data = json.loads(response.read().decode("utf-8"))
      return res_data.get("message", {}).get("content", "")
  except Exception as e:
    return f"Error communicating with local host: {e}"
