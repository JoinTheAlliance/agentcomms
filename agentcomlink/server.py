import os

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentcomlink.constants import app, storage_path
from agentcomlink.files import check_files, get_storage_path, set_storage_path

router = APIRouter()

class FilePath(BaseModel):
    path: str

def get_server():
    global app
    return app

def start_server(storage_path=None, port=8000):
    global app
    if storage_path:
        set_storage_path(storage_path)
    check_files()
    app = FastAPI()
    app.include_router(router)
    app.mount(
        "/", StaticFiles(directory="static", html=True), name="static"
    )  # enable HTML support
    app.mount(
        "/files", StaticFiles(directory=get_storage_path(), html=False), name="files"
    )
    if port:
        os.environ["PORT"] = str(port)
    return app

def stop_server():
    global app
    app = None

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

app = FastAPI()
ws: WebSocket

# Define a chat storage
chats: List[str] = []

@app.get("/")
async def get():
    return FileResponse("static/index.html")

async def send_message(message):
    print("sending message", message)
    await ws.send_text(message)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global ws
    ws = websocket
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")
            await send_message(data)
            chats.append(data)
    except WebSocketDisconnect:
        ws = None

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
