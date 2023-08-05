import os

from agentcomms.adminpanel.files import (
    add_file,
    get_file,
    list_files,
    list_files_formatted,
    remove_file,
    set_storage_path,
    update_file,
)

# Define a test directory
TEST_DIR = "./test_dir/"


def setup_module():
    os.makedirs(TEST_DIR, exist_ok=True)
    set_storage_path(TEST_DIR)


def teardown_module():
    # check if TEST_DIR exists
    if not os.path.exists(TEST_DIR):
        return
    for file in os.listdir(TEST_DIR):
        os.remove(os.path.join(TEST_DIR, file))
    os.rmdir(TEST_DIR)


def test_add_file():
    setup_module()
    assert add_file("test.txt", "Hello, world!")
    assert os.path.isfile(os.path.join(TEST_DIR, "test.txt"))
    teardown_module()


def test_get_file():
    setup_module()
    add_file("test.txt", "Hello, world!")
    assert get_file("test.txt") == "Hello, world!"
    teardown_module()


def test_update_file():
    setup_module()
    assert update_file("test.txt", "Hello, world! Updated")
    assert get_file("test.txt") == "Hello, world! Updated"
    teardown_module()


def test_list_files():
    setup_module()
    add_file("test.txt", "Hello, world!")
    assert "test.txt" in list_files()
    teardown_module()


def test_list_files_formatted():
    setup_module()
    add_file("test.txt", "Hello, world!")
    assert "test.txt" in list_files_formatted()
    teardown_module()


def test_remove_file():
    setup_module()
    add_file("test.txt", "Hello, world!")
    assert remove_file("test.txt")
    assert "test.txt" not in list_files()
    teardown_module()
