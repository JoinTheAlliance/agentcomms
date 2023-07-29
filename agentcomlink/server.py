import json
import os
import asyncio
from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentcomlink.constants import app, storage_path
from agentcomlink.files import check_files, get_storage_path, set_storage_path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from agentcomlink.page import page
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=1)

router = APIRouter()
app = FastAPI()

ws: WebSocket = None

handlers = []
loop = None


class FilePath(BaseModel):
    path: str


def get_server():
    """Retrieve the global FastAPI instance."""
    global app
    return app


def get_parent_path():
    """Return the absolute path of the parent directory of this script."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def start_server(storage_path=None, port=8000):
    """
    Start the FastAPI server.

    :param storage_path: The path where to store the files.
    :param port: The port on which to start the server.
    :return: The FastAPI application.
    """
    # start an event loop
    global loop
    loop = asyncio.new_event_loop()
    global app
    if storage_path:
        set_storage_path(storage_path)
    check_files()
    app.include_router(router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount(
        "/files", StaticFiles(directory=get_storage_path(), html=False), name="files"
    )
    if port:
        os.environ["PORT"] = str(port)

    return app


def stop_server():
    """Stop the FastAPI server by setting the global app to None."""
    global app
    app = None


@app.get("/")
async def get():
    """Handle a GET request to the root of the server, responding with an HTML page."""
    return HTMLResponse(page)


def send_message(message, type="chat"):
    """
    Send a message to the websocket.

    :param message: The message to send.
    """
    global ws
    global loop
    if ws is not None and loop is not None:
        print("send text")
        message = json.dumps({"type": type, "message": message})
        print(message)
        asyncio.run(ws.send_text(message))


async def async_send_message(message, type="chat"):
    """
    Send a message to the websocket.

    :param message: The message to send.
    """
    global ws
    global loop
    if ws is not None and loop is not None:
        print("send text")
        message = json.dumps({"type": type, "message": message})
        print(message)
        await ws.send_text(message)

def register_message_handler(handler):
    """
    Register a handler for messages received through the websocket.

    :param handler: The handler to register.
    """
    global handlers
    handlers.append(handler)


def unregister_message_handler(handler):
    """
    Unregister a handler for messages received through the websocket.

    :param handler: The handler to unregister.
    """
    global handlers
    handlers.remove(handler)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Establish a websocket connection.

    :param websocket: The websocket through which to communicate.
    """
    global ws
    ws = websocket
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # data is a string, convert to json
            data = json.loads(data)
            print(data)
            for handler in handlers:
                await handler(data)
    except WebSocketDisconnect:
        ws = None


@router.post("/file/")
async def http_add_file(path: str = Form(...), file: UploadFile = File(...)):
    """
    Create a new file at a given path with the provided content.

    :param path: The path where to create the file.
    :param file: The content to put in the file.
    :return: A success message.
    """
    check_files()
    with open(os.path.join(storage_path, path), "wb") as f:
        f.write(await file.read())
    return {"message": "File created"}


@router.delete("/file/{path}")
def http_remove_file(path: str):
    """
    Delete a file at a given path.

    :param path: The path of the file to delete.
    :return: A success message.
    """
    check_files()
    try:
        os.remove(os.path.join(storage_path, path))
        return {"message": "File removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/file/")
async def http_update_file(path: str = Form(...), file: UploadFile = File(...)):
    """
    Update a file at a given path with the provided content.

    :param path: The path of the file to update.
    :param file: The new content to put in the file.
    :return: A success message.
    """
    check_files()
    with open(os.path.join(storage_path, path), "wb") as f:
        f.write(await file.read())
    return {"message": "File updated"}


@router.get("/files/")
def http_list_files(path: str = "."):
    """
    List all files in a given directory.

    :param path: The path of the directory.
    :return: A list of files.
    """
    check_files()
    return {"files": os.listdir(os.path.join(storage_path, path))}


@router.get("/file/{path}")
def http_get_file(path: str):
    """
    Retrieve a file at a given path.

    :param path: The path of the file to retrieve.
    :return: The file as a response.
    """
    check_files()
    try:
        return FileResponse(os.path.join(storage_path, path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    async def test_send(input):
        print(input)
        await async_send_message("test")

    register_message_handler(test_send)
    import uvicorn
    uvicorn.run("agentcomlink:start_server", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))