# AI Travel Planner

A real-time travel planning application that uses AI to create personalized trip itineraries. The application leverages LangChain and GPT-4 to generate dynamic travel plans with streaming updates.

## Features

- 🌍 Personalized trip planning based on destination
- 💰 Dynamic budget assessment for any trip duration
- 🎯 Interest-based attraction recommendations
- ⚡ Real-time streaming responses
- 📅 Day-by-day itinerary generation
- 🧠 Powered by GPT-4 for enhanced reasoning and planning
- 📊 Smart attraction scaling based on trip duration

## API Endpoints

### GET `/stream-plan`

Creates a travel plan with real-time updates.

**Parameters:**

- `destination`: String - Where you want to go (e.g., "Paris", "Tokyo")
- `dates`: String - Duration of the trip (e.g., "5 days", "1 week", "3-day")
- `currency`: String - Currency for budget calculation (e.g., "USD", "EUR")
- `budget`: Integer - Available budget amount
- `interests`: Array[String] - Optional list of interests/themes (e.g., ["art", "food", "history"])

**Response Stream Events:**

- `thought`: Agent's thinking process and tool usage
- `narration`: Streaming narrative from the AI
- `final`: Structured itinerary
- `status`: Process completion status
- `done`: Stream end marker

## Technical Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **LangChain** - AI agent orchestration and tool management
- **GPT-4** - Advanced language model for intelligent planning
- **Server-Sent Events (SSE)** - Real-time streaming updates
- **Uvicorn** - ASGI server for running the application

## Response Format

The itinerary is returned in a structured format:

```json
{
  "title": "Trip to [Destination]",
  "days": [
    {
      "day": 1,
      "activities": [
        "Morning: Visit the Louvre Museum",
        "Afternoon: Walk along the Seine River",
        "Evening: Dinner at a local bistro"
      ]
    },
    {
      "day": 2,
      "activities": [
        "Morning: Explore Notre-Dame Cathedral",
        "Afternoon: Shopping in Le Marais",
        "Evening: Eiffel Tower visit"
      ]
    }
  ]
}
```

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key with GPT-4 access

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd app-20-aether-agent-backend
```

2. **Install dependencies:**
```bash
pip3 install -r requirements.txt
```

3. **Set up environment variables:**
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

4. **Run the server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## Usage Examples

### Example Request

```bash
curl "http://localhost:8000/stream-plan?destination=Paris&dates=5%20days&currency=USD&budget=2000&interests=art&interests=food"
```

### Example Response Stream

```
data: {"type": "thought", "content": "🤔 Agent thinking: Planning a 5-day trip to Paris..."}

data: {"type": "narration", "content": "Day 1: Start your Paris adventure..."}

data: {"type": "final", "payload": {"title": "Trip to Paris", "days": [...]}}

data: {"type": "status", "content": "✅ Trip planning complete!"}

data: {"type": "done"}
```

## Key Improvements

### 🚀 **Recent Updates:**

1. **Upgraded to GPT-4** - Enhanced reasoning and planning capabilities
2. **Dynamic Trip Duration** - Now properly handles any trip length (1 day to multiple weeks)
3. **Smart Attraction Scaling** - Automatically adjusts the number of attractions based on trip duration
4. **Improved Budget Analysis** - Budget evaluation now considers the actual trip duration
5. **Better Error Handling** - More robust date parsing and fallback mechanisms

### 🧠 **How It Works:**

1. **Date Parsing** - The system intelligently parses trip duration from various formats
2. **Tool Integration** - Uses specialized tools for attraction search and budget validation
3. **Real-time Planning** - Streams the planning process so users can see the AI thinking
4. **Structured Output** - Converts the AI response into a clean, organized itinerary

## Development

### Project Structure

```
app-20-aether-agent-backend/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .env               # Environment variables (create this)
```

### Adding New Features

The application is built with extensibility in mind:
- Add new tools by creating functions with the `@tool` decorator
- Modify the prompt in the `stream_plan` function to change AI behavior
- Extend the `Itinerary` and `DayActivity` types for additional data

## Troubleshooting

### Common Issues

1. **"pip command not found"** - Use `pip3` instead of `pip` on macOS
2. **OpenAI API errors** - Ensure your API key has GPT-4 access
3. **Stream connection issues** - Check that your client supports Server-Sent Events

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed correctly
2. Verify your OpenAI API key is valid and has sufficient credits
3. Ensure you're using Python 3.8+ for compatibility

## License

[Add your license information here]
