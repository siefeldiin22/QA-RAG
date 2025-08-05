from app.agent.client import client,MODEL_NAME

SYSTEM_MESSAGE= """You are an AI assistant that rephrases user follow-up questions into complete, standalone questions.

Your goal is to make the question fully self-contained by including all necessary context from the previous conversation, so it can be used for accurate semantic search using FAISS.

if the user input not a follow-up question, leave it the same."

Do not answer the question. Simply return the standalone version of the last user message.
"""

def chat_history_handler(chat_history: list[str]):
    messages=[]
    for message in chat_history:
        messages.append({"role": "user", "content": message['user_message']})
        messages.append({"role": "assistant", "content": message['assistant_message']})
    return messages

async def chat_history_analyzer(user_input: str, chat_history: list[str]):
    """
    Async generator that streams response from Azure OpenAI ChatCompletion
    """
    messages = [
        {
            "role": "system",
            "content": SYSTEM_MESSAGE,
        }]
    history_messages= chat_history_handler(chat_history)
    messages.extend(history_messages)
    messages.append({"role": "user", "content": user_input})

    # Use Azure OpenAI's acreate with stream=True
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
    )

    return response.choices[0].message.content
