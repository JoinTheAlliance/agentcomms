import os
from agentfs import get_server, get_storage_path

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentfs:start_server", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

    from fastapi.staticfiles import StaticFiles
    app = get_server()