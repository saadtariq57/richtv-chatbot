# RichTV Chatbot – Integration Overview

## What This Service Does

- **Financial Q&A** over your data (prices, market, fundamentals).
- **Conversations** per user: history stored in PostgreSQL; last N messages used as context.

---

## How the Main App Calls It

| Action | Call | Main app sends | Service returns |
|--------|------|----------------|-----------------|
| **New chat** | `POST /query` or `GET /query` | `prompt`, `user_id` (from your auth) | `answer`, `conversation_id` |
| **Continue chat** | Same | `prompt`, `user_id`, `conversation_id` (from previous response) | `answer`, same `conversation_id` |
| **One-off (no history)** | Same | `prompt` only (no `user_id`) | `answer`, no `conversation_id` |

**Main app must:**
- Authenticate the user and set `user_id`.
- Send `user_id` on every request when you want a persistent conversation.
- Store `conversation_id` from the response and send it back for follow-up messages in that thread.

---

## Data Flow (One Sentence)

Main app sends **user_id + optional conversation_id + prompt** → chatbot runs the pipeline (and loads/saves conversation when `user_id` is present) → returns **answer + conversation_id** (when conversation is used).
