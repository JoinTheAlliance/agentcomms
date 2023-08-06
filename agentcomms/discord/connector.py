import discord
import os
import openai
import time
import asyncio
from random import *
from elevenlabs import set_api_key, generate, save
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

message_queue = asyncio.Queue()

temp_folder_tts = "./temp"
temp_path = "./temp/output.mp3"

intents = discord.Intents().all()
intents.message_content = True
bot = discord.Client(intents=intents)
vc = None


async def send_queued_messages():
    """
    Function to send all messages that have been queued.
    """
    while True:
        print("Waiting for message")
        message, channel_id = await message_queue.get()
        channel = bot.get_channel(channel_id)
        if channel is not None:
            # Send the message
            # determine if this is a voice channel
            if channel.type == discord.ChannelType.voice:
                try:
                    sources = []
                    sentences = message.split("\n")
                    for sentence in sentences:
                        tts_reply = generate_tts(str(sentence))
                        sources.append(tts_reply)
                    for source in sources:
                        vc.play(discord.FFmpegPCMAudio(source))
                        while vc.is_playing():
                            await asyncio.sleep(0.10)
                except:
                    raise
            else:
                await channel.send(message)

        # Mark the message as handled
        message_queue.task_done()
        print("Message sent from queue")


def send_message(message, channel_id):
    """
    Function to send a message. Adds the message to the queue.

    Args:
        message (str): Message to send
        channel_id (int): ID of the channel where the message will be sent
    """
    message_queue.put_nowait((message, channel_id))
    print("Message sent")


def start_connector(discord_api_token=None):
    """
    Starts the Discord bot connector

    Args:
        discord_api_token (str, optional): Discord API token. Defaults to None.
    """
    global bot
    print("Starting Discord connector")
    if discord_api_token is None:
        discord_api_token = os.getenv("DISCORD_API_TOKEN")
    print("Discord connector started")

    def bot_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def main():
            await bot.start(discord_api_token)

        loop.run_until_complete(asyncio.gather(main(), send_queued_messages()))

    # Create a new thread that will run the bot
    t = Thread(target=bot_thread, daemon=True)
    t.start()
    return t


def generate_tts(message):
    """
    Generates TTS for a given message.

    Args:
        message (str): Message to convert to speech.

    Returns:
        str: File path of the audio file.
    """
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))
    voice = os.getenv("ELEVENLABS_VOICE")
    model = os.getenv("ELEVENLABS_MODEL")
    timestamp = str(time.time())
    # check that temp_folder_tts exists
    if not os.path.exists(temp_folder_tts):
        os.makedirs(temp_folder_tts)
    file_path = temp_folder_tts + "/reply_" + timestamp + ".mp3"
    print(message)
    audio = generate(text=message, voice=voice, model=model, stream=False)
    save(audio, file_path)
    return file_path


handlers = []


def register_feed_handler(func):
    """
    Registers a new feed handler.

    Args:
        func (callable): Function to be registered as a handler.
    """
    handlers.append(func)


def unregister_feed_handler(func):
    """
    Unregisters a feed handler.

    Args:
        func (callable): Function to be unregistered as a handler.
    """
    handlers.remove(func)


@bot.event
async def on_ready():
    """
    Callback function that is called when the bot is ready.
    """
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message):
    """
    Callback function that is called when a new message is received.

    Args:
        message (Message): Message object.
    """
    global vc
    if message.author == bot.user:
        return

    if not message.guild.me.permissions_in(message.channel).manage_messages:
        print("Missing permissions to manage messages")
        return

    if discord.utils.get(bot.voice_clients, guild=message.guild) != None:
        if (
            discord.utils.get(bot.voice_clients, guild=message.guild).is_playing()
            == True
        ):
            await message.delete()
            return

    # Execute registered handlers
    for handler in handlers:
        await handler(message)

    contents = message.content
    speaker_id = contents
    await message.delete()
    channel = message.channel
    members = channel.members

    for themember in members:
        if themember.id == int(speaker_id):
            voice = themember.voice

    voice_client = discord.utils.get(bot.voice_clients, guild=voice.channel.guild)
    if voice_client is None:
        vc = await voice.channel.connect()
    else:
        vc = voice_client

    if os.path.exists(temp_path):
        os.remove(temp_path)

    # Assuming you have a start_recording method implemented in your voice client
    vc.start_recording(
        discord.sinks.MP3Sink(),
        vgpt_after,
        voice.channel,
    )

    await asyncio.sleep(5)
    vc.stop_recording()

    while not os.path.exists(temp_path):
        await asyncio.sleep(0.1)
    audio_file = open(temp_path, "rb")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = str(transcript.text)

    if transcript == "ok":
        return

    message["speaker_id"] = speaker_id
    message["transcript"] = transcript
    message["vc"] = vc

    for handler in handlers:
        # if handler is async, await it
        if asyncio.iscoroutinefunction(handler):
            await handler(message)
        else:
            handler(message)
    return message


async def vgpt_after(sink: discord.sinks, channel: discord.TextChannel, *args):
    """
    Post-processing function to be executed after receiving a message.

    Args:
        sink (discord.sinks): Audio sink.
        channel (discord.TextChannel): Channel where the message was received.
        args: Additional arguments.
    """
    user_id = ""
    for user_id, audio in sink.audio_data.items():
        user_id = f"<@{user_id}>"
        with open(temp_path, "wb") as f:
            f.write(audio.file.getbuffer())
