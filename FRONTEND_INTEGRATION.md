## RichTV Frontend → Chatbot Service Contract (Very Brief)

### 1. Base URL

RICHTV_CHATBOT_API_URL in .env
- The backend will expose the chatbot at something like: `https://api.richtv.io/chatbot`  
  (frontend should call the **main app backend**, not the chatbot directly).

All examples below are **frontend → main app backend**; the backend then calls this chatbot service.

---

### 2. Sending a message

**Request (to backend):**

```http
POST /chatbot/query
Content-Type: application/json

{
  "prompt": "What's NVDA price?",
  "conversation_id": "<optional-uuid>"
}
```

- `prompt`: user’s text input.
- `conversation_id`:
  - Omit for a **new conversation**.
  - Send the existing `conversation_id` to **continue** a conversation.
- `user_id` is **not sent by the frontend**; the backend injects it from the authenticated user.

**Response (from backend):**

```json
{
  "answer": "...",
  "conversation_id": "uuid-string"
}
```

- Always store `conversation_id` with that chat thread in the frontend.

---

### 3. Listing user conversations

Frontend asks the main backend for the user’s conversations; backend calls:

```http
GET /chatbot/conversations
```

**Response:**

```json
[
  {
    "id": "uuid-string",
    "user_id": "implicit (for backend only)",
    "title": "Short chat title",
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp"
  },
  ...
]
```

Use this to build the “Previous conversations” list.

---

### 4. Fetching messages for a conversation

```http
GET /chatbot/conversations/{conversation_id}/messages?limit=50
```

**Response:**

```json
[
  {
    "role": "user",
    "content": "User message",
    "created_at": "ISO timestamp"
  },
  {
    "role": "assistant",
    "content": "Bot reply",
    "created_at": "ISO timestamp"
  }
]
```

Render these messages in order to reconstruct the chat history.

