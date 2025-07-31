# ATL Chatbot Web API Documentation

This document describes how to set up, run, and use the ATL Chatbot Web API.

## Staff
• Dr Kal Ng (Professional Practitioner)
• Mr Lawrence Shen (Professional Practitioner)
• Mr Aiden Yan (Senior Software Engineer)
• Dr Jenny Kwok (Lab Coordinator)

## Table of Contents
- [Setup](#setup)
- [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Integration Examples](#integration-examples)
- [Deployment Considerations](#deployment-considerations)

## Setup

1. Make sure you have Python installed and create a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\activate
# On Windows CMD:
venv\Scripts\activate.bat
# On Git Bash:
source venv/Scripts/activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

1. Start the API server:
```bash
python src/api.py
```

The server will start on `http://localhost:8000`. You can access:
- API documentation at `http://localhost:8000/docs`
- Alternative documentation at `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check
**GET /** 

Checks if the API is running.

**Response:**
```json
{
    "status": "ok",
    "message": "ATL Chatbot API is running"
}
```

### 2. Chat Endpoint
**POST /chat**

Send messages to the chatbot and receive responses.

**Request Body:**
```json
{
    "message": "Your message here",
    "session_id": "optional-session-id"
}
```

**Response:**
```json
{
    "response": "Chatbot's response text",
    "session_id": "optional-session-id",
    "metadata": {
        "timestamp": "2025-06-24 16:46:56.601339",
        "message_length": 28,
        "response_length": 7103
    }
}
```

## Testing

### Using Python
Create a file named `test_api.py`:
```python
import requests
import json

def test_chat_api():
    url = "http://localhost:8000/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "message": "Tell me about ATL facilities",
        "session_id": "test-1"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print("\nStatus Code:", response.status_code)
        print("\nResponse:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print("\nError:", str(e))

if __name__ == "__main__":
    test_chat_api()
```

Run the test:
```bash
python test_api.py
```

### Using PowerShell
```powershell
$headers = @{
    "Content-Type" = "application/json"
}
$body = @{
    "message" = "Tell me about ATL facilities"
    "session_id" = "test-1"
} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/chat" -Method Post -Headers $headers -Body $body
```

### Using cURL
```bash
curl -X POST "http://localhost:8000/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Tell me about ATL\",\"session_id\":\"user-123\"}"
```

## Integration Examples

### JavaScript/Frontend
```javascript
async function chatWithBot(message) {
    const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            session_id: 'user-123'
        })
    });
    const data = await response.json();
    return data.response;
}

// Usage example:
chatWithBot("Tell me about ATL")
    .then(response => console.log(response))
    .catch(error => console.error('Error:', error));
```

### Python
```python
import requests

def chat_with_bot(message):
    response = requests.post(
        'http://localhost:8000/chat',
        json={
            'message': message,
            'session_id': 'user-123'
        }
    )
    return response.json()['response']

# Usage example:
response = chat_with_bot("Tell me about ATL")
print(response)
```

## Deployment Considerations

When deploying to production, consider the following:

1. **Security**:
   - Add authentication
   - Use HTTPS
   - Implement rate limiting
   - Configure CORS properly

2. **Environment**:
   - Use environment variables for configuration
   - Set up proper logging
   - Configure error handling

3. **Scaling**:
   - Consider using a production WSGI server
   - Set up load balancing if needed
   - Monitor system resources

4. **Hosting Options**:
   - Cloud platforms (AWS, Azure, GCP)
   - VPS providers
   - Container orchestration (Docker, Kubernetes)

## Error Handling

The API uses standard HTTP status codes:
- 200: Successful request
- 400: Bad request (invalid input)
- 500: Server error

Error responses include a detail message:
```json
{
    "detail": "Error message describing what went wrong"
}