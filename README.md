# Chatbot DB

A conversational AI chatbot built with Flask and PostgreSQL. 
Uses the Claude API to generate responses and persists full 
conversation history to a database.

## Tech Stack

- Python / Flask
- PostgreSQL
- SQLAlchemy
- Claude API (Anthropic)

## Features

- Create users and conversations
- Chat with Claude via a REST API
- Full conversation history saved to PostgreSQL
- Context-aware responses — Claude remembers previous messages

## Setup

1. Clone the repo
2. Install dependencies

```

pip install -r requirements.txt

```

3. Create a `.env` file with your credentials

```

PSQL_PASSWORD=your_password
ANTHROPIC_API_KEY=your_api_key

```

4. Run the app

```

python app.py

```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /users | Create a user |
| POST | /conversations | Start a conversation |
| POST | /conversations/:id/chat | Send a message |