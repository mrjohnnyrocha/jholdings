from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from typing import Generator
import asyncio

from groq import AsyncGroq  # make sure to import AsyncGroq
from configs import GROQ_API_KEY, GROQ_MODEL_NAME
from news import getNews
from prompts import SYSTEM_PROMPT

app = FastAPI()

# Initialize the Groq API client
client = AsyncGroq(api_key=GROQ_API_KEY)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI News Search API"}

@app.get("/api/news")
async def fetch_news(query: str):
    """
    Endpoint to fetch news and generate a summary based on a user query.
    Utilizes a stream response to handle potentially long-running AI generation tasks.
    """
    news_items = await getNews(query)
    if not news_items or 'results' not in news_items:
        raise HTTPException(status_code=404, detail="No news items found for the given query")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Query: {query}\nNews Items: {news_items['results']}"}
    ]

    return StreamingResponse(generate_responses(messages), media_type="text/plain")

@app.post("/api/groq-response")
async def generate_responses(messages: list) -> Generator[str, None, None]:
    """
    Generate responses from the LLM in a streaming fashion using the Groq API.
    """
    chat_completion = await client.chat.completions.create(
        messages=messages,
        model=GROQ_MODEL_NAME
    )

    yield chat_completion.choices[0].message.content  # Streaming the response content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
