import os

from agentcomlink import async_send_message, register_message_handler

async def send(asdf):
    await async_send_message("test")

if __name__ == "__main__":
    register_message_handler(send)
    import uvicorn
    uvicorn.run("agentcomlink:start_server", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))