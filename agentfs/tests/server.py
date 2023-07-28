from fastapi.testclient import TestClient
from agentfs.server import start_server

client = TestClient(start_server())


def test_http_add_file():
    file_contents = "Hello, world!"
    response = client.post(
        "/file/",
        data={"path": "test.txt"},
        files={"file": ("test.txt", file_contents, "text/plain")},
    )
    print("Response:", response.json())
    assert response.status_code == 200
    assert response.json() == {"message": "File created"}


def test_http_get_file():
    response = client.get("/file/test.txt")
    assert response.status_code == 200
    assert response.content.decode() == "Hello, world!"


def test_http_update_file():
    file_contents = " Updated"
    response = client.put(
        "/file/",
        data={"path": "test.txt"},
        files={"file": ("test.txt", file_contents, "text/plain")},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "File updated"}


def test_http_list_files():
    test_http_add_file()
    print("Files:", client.get("/files/").json())
    response = client.get("/files/")
    assert response.status_code == 200
    assert "test.txt" in response.json()["files"]


def test_http_remove_file():
    response = client.delete("/file/test.txt")
    assert response.status_code == 200
    assert response.json() == {"message": "File removed"}
