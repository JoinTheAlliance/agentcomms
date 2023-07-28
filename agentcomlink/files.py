import os

from agentcomlink.constants import storage_path


def check_files():
    if not os.path.exists(storage_path):
        os.makedirs(storage_path, exist_ok=True)

def get_storage_path():
    return storage_path

def set_storage_path(new_path):
    global storage_path
    if os.path.exists(new_path):  # Check if the new_path exists
        storage_path = new_path
        return True
    else:
        return False  # The new path doesn't exist


def add_file(path, content):
    check_files()
    with open(os.path.join(storage_path, path), "w") as f:
        f.write(content)
    return True


def remove_file(path):
    check_files()
    os.remove(os.path.join(storage_path, path))  # Removes the file
    return True


def update_file(path, content):
    check_files()
    with open(os.path.join(storage_path, path), "a") as f:  # 'a' for appending
        f.write(content)
    return True


def list_files(path="."):
    check_files()
    return os.listdir(os.path.join(storage_path, path))  # Returns the list of files


def get_file(path):
    check_files()
    with open(os.path.join(storage_path, path), "r") as f:  # 'r' for reading
        content = f.read()
    return content
