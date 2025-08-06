from app.agent.client import client,MODEL_NAME

async def stream_llm_response(question: str, context_str: list[str]):
    """
    Async generator that streams response from Azure OpenAI ChatCompletion
    """
    # Compose the prompt/messages
    messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant. For questions, answer strictly based on the provided context. "
            "If the user asking question and the answer is not in the context, respond with 'I don't know based on the provided information.' "
            "For non-question messages such as greetings, openers, or polite endings (e.g., 'Hi', 'Thank you', 'Bye'), "
            "respond in a brief, friendly, and polite manner without requiring context(e.g., 'Hello, How Can I Help You', 'You Welcome')."
        ),
    },
    {
        "role": "user",
        "content": f"Context:\n{"\n\n".join(context_str).strip()}\n\nQuestion: {question.strip()}",
    },
]


    # Use Azure OpenAI's acreate with stream=True
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        stream=True,
    )

    # Stream tokens as they are received
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
