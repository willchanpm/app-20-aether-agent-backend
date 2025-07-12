from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import AsyncCallbackHandler
from typing import List, Optional, TypedDict
import asyncio
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@tool
def search_attractions(city: str, theme: str, num_days: int) -> str:
    """Finds themed attractions in a city for a multi-day trip"""
    # Calculate how many attractions we need based on trip duration
    # Assume 2-3 attractions per day for a good variety
    num_attractions = min(num_days * 3, 15)  # Cap at 15 to avoid overwhelming results
    
    prompt = f"List {num_attractions} real or plausible {theme}-related attractions in {city}. Include a mix of museums, landmarks, cultural spots, restaurants, and activities. Format as a simple comma-separated list. Focus on attractions that would work well for a {num_days}-day trip."
    response = ChatOpenAI(model="gpt-4", temperature=0.7).invoke(prompt)
    return response.content

@tool
def check_budget(amount: int, currency: str, num_days: int) -> str:
    """Checks if the budget is sufficient for a multi-day trip"""
    prompt = f"As a travel expert, evaluate if {amount} {currency} is sufficient for a {num_days}-day trip, considering average hotel, food, activities, and transportation costs. Provide a brief 1-2 sentence assessment and suggest budget adjustments if needed."
    response = ChatOpenAI(model="gpt-4", temperature=0.3).invoke(prompt)
    return response.content

tools = [search_attractions, check_budget]
# Upgrade to GPT-4 for better reasoning and planning capabilities
llm = ChatOpenAI(model="gpt-4", temperature=0, streaming=True)
agent_executor = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

class DayActivity(TypedDict):
    day: int
    activities: List[str]

class Itinerary(TypedDict):
    title: str
    days: List[DayActivity]

def parse_itinerary(text: str, destination: str) -> Itinerary:
    """Parse the agent's response into a structured itinerary"""
    # Improved regex to catch more day formats
    day_sections = re.split(r'Day \d+:|DAY \d+:|Day \d+ -|DAY \d+ -', text)
    if len(day_sections) <= 1:
        return {
            "title": f"Trip to {destination}",
            "days": [{
                "day": 1,
                "activities": [text.strip()]
            }]
        }
    
    days = []
    for i, section in enumerate(day_sections[1:], 1):
        activities = [
            activity.strip()
            for activity in section.split('\n')
            if activity.strip() and not activity.lower().startswith(('day', 'morning', 'afternoon', 'evening'))
        ]
        days.append({
            "day": i,
            "activities": activities
        })
    
    return {
        "title": f"Trip to {destination}",
        "days": days
    }

@app.get("/stream-plan")
async def stream_plan(
    destination: str = Query(...),
    dates: str = Query(...),
    currency: str = Query(...),
    budget: int = Query(...),
    interests: List[str] = Query(default=[])
):
    # Extract number of days from the dates parameter
    # This helps us pass the correct duration to our tools
    num_days = 1  # Default fallback
    try:
        # Try to extract number from dates string (e.g., "5 days", "1 week", "3-day")
        if "day" in dates.lower():
            match = re.search(r'(\d+)', dates)
            if match:
                num_days = int(match.group(1))
        elif "week" in dates.lower():
            match = re.search(r'(\d+)', dates)
            if match:
                num_days = int(match.group(1)) * 7
        else:
            # If we can't parse it, assume it's a number
            match = re.search(r'(\d+)', dates)
            if match:
                num_days = int(match.group(1))
    except (AttributeError, ValueError):
        # If parsing fails, keep default of 1 day
        pass
    
    theme = ", ".join(interests) if interests else "general"
    
    # Much more explicit prompt that emphasizes the exact duration
    prompt = (
        f"You are a travel planning expert. Create a detailed {dates}-long trip itinerary to {destination} focused on {theme}. "
        f"IMPORTANT: Your response MUST include exactly {num_days} days of activities, no more and no less. "
        f"Use the search_attractions tool to find {num_days * 3} relevant attractions in {destination}. "
        f"Use the check_budget tool to validate if {budget} {currency} is sufficient for {num_days} days. "
        f"Structure your response with clear 'Day X:' headers for each of the {num_days} days. "
        f"Each day should include 2-4 activities, meals, and transportation suggestions. "
        f"Make sure to plan for the FULL {num_days} days as requested."
    )

    async def event_stream():
        try:
            async for event in agent_executor.astream_events({"input": prompt}, version="v1"):
                kind = event.get("event")

                if kind == "on_chain_start":
                    agent_input = event.get("data", {}).get("input", "")
                    message = f"🤔 Agent thinking: {agent_input}"
                    yield f"data: {json.dumps({'type': 'thought', 'content': message})}\n\n"

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    tool_input = event.get("data", {}).get("input", {})
                    message = f"🔧 Starting tool `{tool_name}` with inputs: {tool_input}"
                    yield f"data: {json.dumps({'type': 'thought', 'content': message})}\n\n"

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown_tool")
                    tool_output = event.get("data", {}).get("output", "")
                    message = f"✅ Done with tool `{tool_name}`. Output: {tool_output}"
                    yield f"data: {json.dumps({'type': 'thought', 'content': message})}\n\n"

                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        yield f"data: {json.dumps({'type': 'narration', 'content': chunk.content})}\n\n"

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {}).get("output")
                    if output:
                        match = re.search(r"trip to ([^.]+)", prompt)
                        dest = match.group(1) if match else "your destination"
                        itinerary = parse_itinerary(output, dest)
                        yield f"data: {json.dumps({'type': 'final', 'payload': itinerary})}\n\n"
                        yield f"data: {json.dumps({'type': 'status', 'content': '✅ Trip planning complete!'})}\n\n"
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        finally:
            # Ensure connection is flushed and closed
            yield "event: done\ndata: \n\n"
            print("🛑 Stream closed by finally block")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )