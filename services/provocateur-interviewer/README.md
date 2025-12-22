# Provocateur & Real-Time Interviewer

This service hosts:
- **The Provocateur**: A background worker that crawls the knowledge vault and generates provocative questions for stale notes.
- **Real-Time Interviewer**: A WebSocket-based service for interactive "Journalist" style interviewing.

## Development

```bash
# Install dependencies
pip install .

# Run dev server
uvicorn app.main:app --reload
```
