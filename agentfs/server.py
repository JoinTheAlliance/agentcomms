import os

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agentfs.constants import app, storage_path
from agentfs.files import check_files, set_storage_path

router = APIRouter()


class FileData(BaseModel):
    path: str
    content: str


def get_server():
    global app
    return app


def start_server(storage_path=None, port=8000):
    global app
    if storage_path:
        set_storage_path(storage_path)
    app = FastAPI()
    app.include_router(router)
    app.mount("/", StaticFiles(directory="static"), name="static")
    if port:
        os.environ["PORT"] = str(port)
    return app


def stop_server():
    global app
    app = None


@router.post("/file/")
def http_add_file(file: FileData):
    check_files()
    with open(os.path.join(storage_path, file.path), "w") as f:
        f.write(file.content)
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
def http_update_file(file: FileData):
    check_files()
    with open(os.path.join(storage_path, file.path), "a") as f:
        f.write(file.content)
    return {"message": "File updated"}


@router.get("/files/")
def http_list_files(path: str = "."):
    check_files()
    return {"files": os.listdir(os.path.join(storage_path, path))}


@router.get("/file/{path}")
def http_get_file(path: str):
    check_files()
    try:
        with open(os.path.join(storage_path, path), "r") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
