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
    global app
    return app


# get the path of the folder that is parent to this one
def get_parent_path():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def start_server(storage_path=None, port=8000):
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
    global app
    app = None


@app.get("/")
async def get():
    return HTMLResponse(page)


def send_message(message):
    global ws
    if ws is not None:
        print("send text")
        loop = asyncio.get_event_loop()  # gets current event loop
        asyncio.run_coroutine_threadsafe(ws.send_text(message), loop)


def register_message_handler(handler):
    global handlers
    handlers.append(handler)


def unregister_message_handler(handler):
    global handlers
    handlers.remove(handler)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
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
    check_files()
    with open(os.path.join(storage_path, path), "wb") as f:
        f.write(await file.read())
    return {"message": "File created"}


@router.delete("/file/{path}")
def http_remove_file(path: str):
    check_files()
    try:
        os.remove(os.path.join(storage_path, path))
        return {"message": "File removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/file/")
async def http_update_file(path: str = Form(...), file: UploadFile = File(...)):
    check_files()
    with open(os.path.join(storage_path, path), "wb") as f:
        f.write(await file.read())
    return {"message": "File updated"}


@router.get("/files/")
def http_list_files(path: str = "."):
    check_files()
    return {"files": os.listdir(os.path.join(storage_path, path))}


@router.get("/file/{path}")
def http_get_file(path: str):
    check_files()
    try:
        return FileResponse(os.path.join(storage_path, path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
