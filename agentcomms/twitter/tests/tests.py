import asyncio
import os
from agentcomms.twitter import (
    start_twitter,
    like_tweet,
    reply_to_tweet,
    tweet,
    register_feed_handler,
    unregister_feed_handler,
)

# Define constants or load them from environment variables
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
SESSION_STORAGE_PATH = "twitter.cookies"


# Custom setup function
def setup_function():
    # Call the start_connector function and check behavior (this is likely to have side effects)
    start_twitter(
        email=TWITTER_EMAIL,
        username=TWITTER_USERNAME,
        password=TWITTER_PASSWORD,
        session_storage_path=SESSION_STORAGE_PATH,
        start_loop=False,
    )


# Add more tests as required for other functions and behaviors
def test_like_tweet():
    setup_function()
    tweet_id = "1687657490584928256"  # Replace with actual tweet ID
    like_tweet(tweet_id)


def test_reply_to_tweet():
    setup_function()
    message = "Test reply!"
    tweet_id = "1687657490584928256"  # Replace with actual tweet ID
    reply_to_tweet(message, tweet_id)


def test_tweet():
    setup_function()
    message = "Test tweet!"
    tweet(message)


def test_register_and_unregister_feed_handler():
    setup_function()
    handler = lambda x: print(x)
    register_feed_handler(handler)
    # Here you can add logic to verify the handler was registered, such as checking the feed_handlers list
    unregister_feed_handler(handler)