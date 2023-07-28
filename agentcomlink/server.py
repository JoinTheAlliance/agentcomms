import os
import asyncio
from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentcomlink.constants import app, storage_path
from agentcomlink.files import check_files, get_storage_path, set_storage_path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from agentcomlink.page import page
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=1)

router = APIRouter()
app = FastAPI()

ws: WebSocket

handlers = []


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
    global app
    if storage_path:
        set_storage_path(storage_path)
    check_files()
    app.include_router(router)
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


def send_message(message):
    """
    Send a message to the websocket.

    :param message: The message to send.
    """
    global ws
    if ws is not None:
        print("send text")
        loop = asyncio.get_event_loop()  # gets current event loop
        asyncio.run_coroutine_threadsafe(ws.send_text(message), loop)


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
            print("data received")
            for handler in handlers:
                print("sending data to handler")
                print(data)
                handler(data)
    except WebSocketDisconnect:
        ws = None
        print("socket disconnected")


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
