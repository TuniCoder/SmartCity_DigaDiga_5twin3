# OpenAI Chat Assistant - Setup Guide

This guide will help you set up the AI chat assistant for the SmartCity application.

## Prerequisites

- Python 3.8+
- Django 5.2+
- OpenAI API key (get one from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys))

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the OpenAI Python library and other required dependencies.

### 2. Configure Environment Variables

Create a `.env` file in the project root directory with the following content:

```env
OPENAI_API_KEY=sk-proj-YOUR_API_KEY_HERE
OPENAI_MODEL=gpt-4
```

**Important:** Replace `YOUR_API_KEY_HERE` with your actual OpenAI API key.

### 3. Environment Variables

The application reads configuration from environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: The model to use (default: `gpt-4`)

These are automatically loaded from your `.env` file using `python-dotenv`.

## Running the Application

### 1. Start the Django Server

```bash
python manage.py runserver
```

### 2. Access the Chat Assistant

Navigate to: `http://localhost:8000/gestion_vehicules/assistant/`

You must be logged in to use the chat assistant.

## Features

### Chat Interface
- Clean, modern UI with Bootstrap styling
- Real-time message exchange
- Message history with timestamps
- Loading indicators during API calls
- Error handling with user-friendly messages

### Conversation Context
- Maintains conversation history for contextual responses
- Stores last 5 messages for context
- Persists conversation history in the database

### Database Models

- **ChatMessage**: Stores individual chat messages
- **AIAssistant**: Configuration for the AI assistant system

### API Endpoints

- `POST /gestion_vehicules/api/chat/` - Send a message to the AI
- `GET /gestion_vehicules/api/chat/history/` - Get chat history
- `DELETE /gestion_vehicules/api/chat/clear/` - Clear chat history

## Error Handling

The application gracefully handles various error scenarios:

1. **Missing API Key**: Clear error message instructing to configure `OPENAI_API_KEY`
2. **Quota Exceeded**: User-friendly message about rate limits
3. **Authentication Errors**: Clear indication of invalid API key
4. **Model Not Found**: Information about unavailable models
5. **Network Errors**: Retry prompts for connection issues

## Security Best Practices

1. **Never commit your `.env` file** to version control
2. **Keep your API key secret** - never share it publicly
3. **Use environment variables** for all sensitive data
4. **Rotate your API keys** regularly

## Troubleshooting

### Issue: "La clé API OpenAI n'est pas configurée"

**Solution**: Ensure your `.env` file exists in the project root and contains `OPENAI_API_KEY=your_key_here`

### Issue: "Limite de quota atteinte"

**Solution**: Check your OpenAI account usage at [https://platform.openai.com/usage](https://platform.openai.com/usage)

### Issue: "Le modèle gpt-4 n'est pas disponible"

**Solution**: Your API key might not have access to GPT-4. Try using `gpt-3.5-turbo` instead:

```env
OPENAI_MODEL=gpt-3.5-turbo
```

### Issue: Chat not responding

**Check**: 
1. You're logged in
2. The API key is valid
3. No network issues
4. Check the browser console for JavaScript errors

## Code Structure

### Key Files

- `smartcity_app/gestion_vehicules/views.py` - API endpoints and view logic
- `smartcity_app/gestion_vehicules/models.py` - ChatMessage and AIAssistant models
- `smartcity_app/gestion_vehicules/urls.py` - URL routing
- `smartcity_app/templates/gestion_vehicules/ai_assistant.html` - Chat UI template
- `smartcity_core/settings.py` - Configuration and environment variables

### Key Functions

- `api_chat_with_ai()`: Main chat endpoint with OpenAI integration
- `ai_assistant()`: Chat interface page
- `api_chat_history()`: Retrieve chat history
- `api_clear_chat_history()`: Clear chat history

## API Integration Details

The chat uses OpenAI's Chat Completions API:

```python
client = OpenAI(api_key=settings.OPENAI_API_KEY)
response = client.chat.completions.create(
    model=settings.OPENAI_MODEL,
    messages=messages,
    max_tokens=500,
    temperature=0.7
)
```

## Testing

Test the chat functionality:

1. Login to the application
2. Navigate to the AI assistant page
3. Send a test message
4. Verify the AI response appears
5. Check conversation history is saved

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Python Library](https://github.com/openai/openai-python)
- [Django Environment Variables](https://django-environ.readthedocs.io/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django logs in `smartcity.log`
3. Check OpenAI API status at [status.openai.com](https://status.openai.com/)

