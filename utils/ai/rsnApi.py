from rsnchat import RsnChat
import os
import dotenv
dotenv.load_dotenv()

apiKey = os.environ.get("RSNCHATAPIKEY")

rsnchat = RsnChat(apiKey)

async def gemini(content: str) -> dict:
    
    resp = rsnchat.gemini(content)

    output = resp.get('message', '')


    return {
        "status": "success", "message": output

    }

async def gpt(content: str) -> dict:
    
    resp = rsnchat.gpt(content)
    output = resp.get('message', '')
    
    return {
        "status": "success", "message": output

    }
#! DISCLAIMER: IF IT WORKS, DON'T TOUCH IT
#! 免責事項: 動作する場合は、触れないでください。