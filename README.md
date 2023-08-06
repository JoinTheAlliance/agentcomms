# agentcomms <a href="https://discord.gg/qetWd7J9De"><img style="float: right" src="https://dcbadge.vercel.app/api/server/qetWd7J9De" alt=""></a>

Connectors for your agent to the outside world.

- Discord connector with (voice and chat, DMs coming)
- Twitter connector (feed only, DMs coming)
- Admin Panel - simple web interface to chat with your agent and upload files

<img src="resources/image.jpg">

[![Lint and Test](https://github.com/AutonomousResearchGroup/agentcomms/actions/workflows/test.yml/badge.svg)](https://github.com/AutonomousResearchGroup/agentcomms/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/agentcomms.svg)](https://badge.fury.io/py/agentcomms)

# Installation

```bash
pip install agentcomms
```

# Twitter Usage Guide

This module uses a set of environment variables to interact with Twitter, so you'll need to set the following before using:

- `TWITTER_EMAIL`: The email address for your Twitter account.
- `TWITTER_USERNAME`: The username for your Twitter account.
- `TWITTER_PASSWORD`: The password for your Twitter account.

## Setting up the Twitter connector

Before you can start using the Twitter connector, you have to initialize it. The initialization is done using the `start_twitter_connector` function.

```python
import twitter
twitter.start_twitter_connector()
```

This will start the twitter connector with default parameters. If you wish to customize the email, username, password, or session storage path, you can use the `start_twitter` function like so:

```python
twitter.start_twitter(email="my_email@example.com", username="my_username", password="my_password", session_storage_path="my_session.cookies")
```

### Liking a tweet

To like a tweet, you can use the `like_tweet` function. Pass in the id of the tweet you wish to like.

```python
twitter.like_tweet("1234567890")
```

### Replying to a tweet

To reply to a tweet, you can use the `reply_to_tweet` function. Pass in the message you wish to send, and the id of the tweet you're replying to.

```python
twitter.reply_to_tweet("This is a great tweet!", "1234567890")
```

### Posting a tweet

To post a new tweet, you can use the `tweet` function. Pass in the message you wish to tweet. You can optionally pass in a media object to attach to the tweet.

```python
twitter.tweet("Hello, Twitter!")
```

## Registering feed handlers

Feed handlers are functions that get called whenever there are new tweets in the feed. They can be registered using the `register_feed_handler` function.

```python
def my_feed_handler(tweet):
    print(f"New tweet from {tweet['user']['name']}: {tweet['text']}")

twitter.register_feed_handler(my_feed_handler)
```

You can also unregister a handler using the `unregister_feed_handler` function.

```python
twitter.unregister_feed_handler(my_feed_handler)
```

## Getting account information

To get the current account object, you can use the `get_account` function.

```python
account = twitter.get_account()
print(account.username)
```

This will print out the username of the current Twitter account.

# Discord Usage Guide

The Discord connector works with both voice and text. For voice, you will need an Elevenlabs API key.

## Environment Variables

Before you start, you need to set the environment variables for the bot to function correctly. Create a `.env` file in your project directory and set these variables:

```env
DISCORD_API_TOKEN=your_discord_bot_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE=voice_you_want_to_use
ELEVENLABS_MODEL=model_you_want_to_use
```

- `DISCORD_API_TOKEN` is your Discord bot token, which you get when you create a new bot on the Discord developer portal.
- `ELEVENLABS_API_KEY` is your Eleven Labs API key for their TTS service.
- `ELEVENLABS_VOICE` is the voice you want to use for the TTS. You will have to check the Eleven Labs API documentation for the voices they support.
- `ELEVENLABS_MODEL` is the TTS model you want to use. Again, you will have to check the Eleven Labs API documentation for the supported models.

## Running the Bot

After setting your environment variables, you can run your bot by calling the `start_connector` function:

```python
start_connector()
```

## Registering Message Handlers

Message handlers are functions that are executed when certain events happen in Discord, such as receiving a message. Here's how you can register a message handler:

### Create the Handler Function

First, you need to create a function that will be executed when a message is received. This function should take one argument, which is the message that was received. The message object will contain all the information about the message, such as the content of the message, the author, and the channel where it was sent.

Here's an example of a simple message handler function:

```python
def handle_message(message):
    print(f"Received a message from {message.author}: {message.content}")
```

This function will simply print the author and content of every message that is received.

### Register the Handler Function

To register the handler function, you use the `register_feed_handler` function and pass the handler function as an argument:

```python
register_feed_handler(handle_message)
```

After calling this function, the `handle_message` function will be executed every time a message is received on Discord.

## Public Functions

### `send_message(message: str, channel_id: int)`

This function is used to add a message to the queue. The message will be sent to the channel with the ID specified.

```python
send_message("Hello world!", 1234567890)
```

### `start_connector(discord_api_token: str)`

This function is used to start the bot and the event loop, setting the bot to listen for events on Discord.

```python
start_connector("your_discord_api_token")
```

### `register_feed_handler(func: callable)`

This function is used to register a new function as a feed handler. Feed handlers are functions that process or respond to incoming data in some way.

```python
def my_func(data):
    print(data)

register_feed_handler(my_func)
```

### `unregister_feed_handler(func: callable)`

This function is used to remove a function from the list of feed handlers.

```python
unregister_feed_handler(my_func)
```

# Admin Panel Usage Guide

## Quickstart

1. **Start the server**:
   You can start the server with uvicorn like this:

```python
import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentcomms:start_server", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

This will start the server at `http://localhost:8000`.

2. **Get a file**:
   Once the server is up and running, you can retrieve file content by sending a GET request to `/file/{path}` endpoint, where `{path}` is the path to the file relative to the server's current storage directory.

```python
from agentcomms import get_file

# Fetches the content of the file located at "./files/test.txt"
file_content = get_file("test.txt")
print(file_content)
```

3. **Save a file**:
   Similarly, you can save content to a file by sending a POST request to `/file/` endpoint, with JSON data containing the `path` and `content` parameters.

```python
from agentcomms import add_file

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
from agentcomms import start_server

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
from agentcomms import get_server

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
from agentcomms import set_storage_path

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
from agentcomms import add_file

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
from agentcomms import remove_file

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
from agentcomms import update_file

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
from agentcomms import list_files

files = list_files()
```

### `list_files_formatted(path='.')`

Lists all files in the specified directory as a formatted string. Convenient!

**Arguments**:

- `path` (str, optional): The path to the directory. Defaults to `'.'` (current directory).

**Returns**:

- A string containing a list of file names in the specified directory.

**Example**:

```python
from agentcomms import list_files

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
from agentcomms import get_file

content = get_file("test.txt")
```

# Contributions Welcome

If you like this library and want to contribute in any way, please feel free to submit a PR and I will review it. Please note that the goal here is simplicity and accesibility, using common language and few dependencies.

<img src="resources/youcreatethefuture.jpg">
