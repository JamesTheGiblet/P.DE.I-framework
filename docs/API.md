# P.DE.I Server API Reference

The P.DE.I Server exposes a REST API and WebSocket interface for interacting with the Exocortex.

**Base URL**: `http://localhost:8000`

## 💬 Chat & Interaction

### WebSocket Chat

- **URL**: `ws://localhost:8000/api/ws/chat`
- **Payload**:

  ```json
  {
    "message": "Write a PID controller",
    "model": "fast",
    "forge_mode": "2",
    "user_id": "default"
  }
  ```

- **Response**: Streams JSON tokens `{ "type": "token", "content": "..." }` followed by `{ "type": "end", "message_id": 123 }`.

### REST Chat

- **POST** `/api/chat`
- **Body**: `{ "message": "str", "model": "str", "forge_mode": "str" }`
- **Returns**: `{ "response": "str", "message_id": int }`

### Feedback

- **POST** `/api/feedback`
- **Body**: `{ "message_id": int, "positive": bool, "comment": "str" }`
- **Description**: Reinforces the learning model based on user feedback.

---

## 💾 Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sessions` | List all saved sessions. |
| `GET` | `/api/history` | Get message history for current session. |
| `POST` | `/api/session/new` | Start a fresh session. |
| `POST` | `/api/session/load` | Load a specific session by ID. |
| `POST` | `/api/session/rename` | Rename a session title. |
| `POST` | `/api/session/delete` | Permanently delete a session. |
| `POST` | `/api/session/clear` | Clear context of current session. |
| `GET` | `/api/session/{id}/export/json` | Download session as JSON. |
| `POST` | `/api/session/import` | Upload a session JSON file. |

---

## ⚙️ System & Tools

### System Status

- **GET** `/api/system/status`
- **Returns**: `{ "cpu": float, "memory": float }`

### GPU Management

- **POST** `/api/system/reset-gpu`
- **Description**: Unloads models from VRAM to free resources.

### File Upload (RAG)

- **POST** `/api/upload`
- **Body**: `multipart/form-data` (File)
- **Supported**: `.zip` (auto-extracted), `.py`, `.cpp`, `.js`, etc.
- **Description**: Indexes code files into the active memory for context-aware answers.

### Utilities

- **GET** `/api/utils/qrcode?url=...`: Generates a QR code for mobile connection.
- **GET** `/api/system/backup`: Triggers and downloads a database backup.
