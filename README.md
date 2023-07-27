# agentfs <a href="https://discord.gg/qetWd7J9De"><img style="float: right" src="https://dcbadge.vercel.app/api/server/qetWd7J9De" alt=""></a>

Simple file management and serving for agents

<img src="resources/image.jpg">

# Installation

```bash
pip install agentfs
```

## Quickstart

1. **Start the server**:
   You can start the server by using the `start_server()` function:

```python
from agentfs import start_server

start_server()
```

This will start the server at `http://localhost:8000`.

You can start the server with uvicorn like this:
```python
import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentfs:start_server", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

2. **Get a file**:
   Once the server is up and running, you can retrieve file content by sending a GET request to `/file/{path}` endpoint, where `{path}` is the path to the file relative to the server's current storage directory.

```python
from agentfs import get_file

# Fetches the content of the file located at "./files/test.txt"
file_content = get_file("test.txt")
print(file_content)
```

3. **Save a file**:
   Similarly, you can save content to a file by sending a POST request to `/file/` endpoint, with JSON data containing the `path` and `content` parameters.

```python
from agentfs import add_file

# Creates a file named "test.txt" in the current storage directory
# and writes "Hello, world!" to it.
add_file("test.txt", "Hello, world!")
```

## API Documentation

AgentFS provides the following public functions:

### `start_server(storage_path=None)`

Starts the FastAPI server. If a `storage_path` is provided, it sets the storage directory to the given path.

**Arguments**:

- `storage_path` (str, optional): The path to the storage directory.

**Returns**:

- None

**Example**:

```python
from agentfs import start_server

start_server("/my/storage/directory")
```

### `get_server()`

Returns the FastAPI application instance.

**Arguments**:

- None

**Returns**:

- FastAPI application instance.

**Example**:

```python
from agentfs import get_server

app = get_server()
```

### `set_storage_path(new_path)`

Sets the storage directory to the provided path.

**Arguments**:

- `new_path` (str): The path to the new storage directory.

**Returns**:

- `True` if the path was successfully set, `False` otherwise.

**Example**:

```python
from agentfs import set_storage_path

set_storage_path("/my/storage/directory")
```

### `add_file(path, content)`

Creates a file at the specified path and writes the provided content to it.

**Arguments**:

- `path` (str): The path to the new file.
- `content` (str): The content to be written to the file.

**Returns**:

- `True` if the file was successfully created.

**Example**:

```python
from agentfs import add_file

add_file("test.txt", "Hello, world!")
```

### `remove_file(path)`

Removes the file at the specified path.

**Arguments**:

- `path` (str): The path to the file to be removed.

**Returns**:

- `True` if the file was successfully removed.

**Example**:

```python
from agentfs import remove_file

remove_file("test.txt")
```

### `update_file(path, content)`

Appends the provided content to the file at the specified path.

**Arguments**:

- `path` (str): The path to the file to be updated.
- `content` (str): The content to be appended to the file.

**Returns**:

- `True` if the file was successfully updated.

**Example**:

```python
from agentfs import update_file

update_file("test.txt", "New content")
```

### `list_files(path='.')`

Lists all files in the specified directory.

**Arguments**:

- `path` (str, optional): The path to the directory. Defaults to `'.'` (current directory).

**Returns**:

- A list of file names in the specified directory.

**Example**:

```python
from agentfs import list_files

files = list_files()
```

### `get_file(path)`

Returns the content of the file at the specified path.

**Arguments**:

- `path` (str): The path to the file.

**Returns**:

- A string containing the content of the file.

**Example**:

```python
from agentfs import get_file

content = get_file("test.txt")
```

# Contributions Welcome

If you like this library and want to contribute in any way, please feel free to submit a PR and I will review it. Please note that the goal here is simplicity and accesibility, using common language and few dependencies.

<img src="resources/youcreatethefuture.jpg">
