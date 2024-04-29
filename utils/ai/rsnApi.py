from rsnchat import RsnChat
import os
import dotenv
dotenv.load_dotenv()

apiKey = os.environ.get("RSNCHATAPIKEY")

rsnchat = RsnChat(apiKey)




async def claude(content: str) -> dict:
    resp = rsnchat.claude(content)

    output = resp.get('message', '')

    return  {
        "status": "success", "message": output
    }


async def gemini(content: str) -> dict:
    
    resp = rsnchat.gemini(content)

    output = resp.get('message', '')


    return {
        "status": "success", "message": output

    }


async def bard(content: str) -> dict:
    
    resp = rsnchat.bard(content)

    output = resp.get('message', '')


    return {
        "status": "success", "message": output

    }

#! IF IT WORK, DONT TOUCH