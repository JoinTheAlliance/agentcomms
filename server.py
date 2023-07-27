import os
from agentfs import get_server

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentfs:start_server", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

    from fastapi.staticfiles import StaticFiles
    app = get_server()
    app.mount("/", StaticFiles(directory="static"), name="static")
