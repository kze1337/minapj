import openai
from openai.error import *
import os
import dotenv
dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_SEC")


chatgpt_cache = {}

def chatgpt(user_content: str, uid = None):
    global chatgpt_cache
    
    if len(chatgpt_cache) > 100: chatgpt_cache = {}
    
    if uid:
        try:
            messages = chatgpt_cache[uid]
        except KeyError:
            create_thread(uid)
            messages = chatgpt_cache[uid]
    else:
        messages = []
    
    messages.append({
        "role": "user",
        "content": user_content
    })

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5,
        max_tokens=768
    )

    if uid:
        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })

    return {
        "status": "success",
        "message": response.choices[0].message.content,
        "response_time": response.response_ms
    }

def create_thread(uid: int, sys_message: str = None):
    global chatgpt_cache
    messages = []
    if sys_message:
        messages.append({
            "role": "system",
            "content": sys_message
        })
    chatgpt_cache[uid] = messages