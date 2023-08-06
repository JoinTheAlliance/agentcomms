import os
import asyncio
from pathlib import Path
import random
import threading
import time
from httpx import Client
from twitter.account import Account
from twitter.scraper import Scraper
import orjson

from twitter.util import init_session

from dotenv import load_dotenv

load_dotenv()

first = True

params = {
    "include_profile_interstitial_type": 1,
    "include_blocking": 1,
    "include_blocked_by": 1,
    "include_followed_by": 1,
    "include_want_retweets": 1,
    "include_mute_edge": 1,
    "include_can_dm": 1,
    "include_can_media_tag": 1,
    "include_ext_has_nft_avatar": 1,
    "include_ext_is_blue_verified": 1,
    "include_ext_verified_type": 1,
    "include_ext_profile_image_shape": 1,
    "skip_status": 1,
    "cards_platform": "Web-12",
    "include_cards": 1,
    "include_ext_alt_text": "true",
    "include_ext_limited_action_results": "true",
    "include_quote_count": "true",
    "include_reply_count": 1,
    "tweet_mode": "extended",
    "include_ext_views": "true",
    "include_entities": "true",
    "include_user_entities": "true",
    "include_ext_media_color": "true",
    "include_ext_media_availability": "true",
    "include_ext_sensitive_media_warning": "true",
    "include_ext_trusted_friends_metadata": "true",
    "send_error_codes": "true",
    "simple_quoted_tweet": "true",
    "count": 20,
    "requestContext": "launch",
    "ext": "mediaStats,highlightedLabel,hasNftAvatar,voiceInfo,birdwatchPivot,superFollowMetadata,unmentionInfo,editControl",
}

feed_handlers = []
dm_handlers = []

account = None


def get_account():
    """
    Returns the global account object.
    """
    return account


def like_tweet(tweet_id):
    """
    Likes a tweet with the given tweet ID using the global account object.

    Parameters:
        tweet_id (str): The ID of the tweet to be liked.
    """
    account.like(tweet_id)


def reply_to_tweet(message, tweet_id):
    """
    Replies to a tweet with the given message and tweet ID using the global account object.

    Parameters:
        message (str): The message to be sent as a reply.
        tweet_id (str): The ID of the tweet to reply to.
    """
    account.reply(message, tweet_id)


def tweet(message, media=None):
    """
    Posts a new tweet with the given message and optional media using the global account object.

    Parameters:
        message (str): The message to be tweeted.
        media (str, optional): The media to be attached to the tweet. Defaults to None.
    """
    if media:
        account.tweet(message, media)
    else:
        account.tweet(message)


def register_feed_handler(handler):
    """
    Registers a new feed handler function. The handler function will be called whenever new feed messages are received.

    Parameters:
        handler (function): The function to be registered as a feed handler.
    """
    feed_handlers.append(handler)


def unregister_feed_handler(handler):
    """
    Unregisters a feed handler function. The handler will no longer be called when new feed messages are received.

    Parameters:
        handler (function): The function to be unregistered.
    """
    feed_handlers.remove(handler)


# async def dm_loop(account, session, scraper):
#     """
#     Main DM loop. This function checks for new DMs and passes them to all registered feed handlers.

#     Parameters:
#         account (twitter.account.Account): The account object to be used for the DM operations.
#         session (httpx.Client): The httpx session to be used for the DM operations.
#         scraper (twitter.scraper.Scraper): The Scraper object to be used for the DM operations.
#     """
#     last_responded_notification = None
#     global params

#     while True:
#         inbox = account.dm_inbox()
#         for handler in feed_handlers:
#             arguments = {
#                 "inbox": inbox,
#                 "account": account,
#                 "session": session,
#             }

#             # if the handler is async, await it, otherwise call directly
#             if asyncio.iscoroutinefunction(handler):
#                 await handler(arguments)
#             else:
#                 handler(arguments)

#         await asyncio.sleep(10 + random.randint(0, 2))


def feed_loop(account, session, scraper):
    """
    Main feed loop. This function checks for new tweets and passes them to all registered feed handlers.

    Parameters:
        account (twitter.account.Account): The account object to be used for the feed operations.
        session (httpx.Client): The httpx session to be used for the feed operations.
        scraper (twitter.scraper.Scraper): The Scraper object to be used for the feed operations.
    """
    last_responded_notification = None
    global params
    global first
    cursor = None

    while True:
        if first == True:
            params["count"] = 10
            del params["requestContext"]
            first = False
            time.sleep(7)
            continue
        # Parse the JSON response
        notifications = account.notifications()
        globalObjects = notifications.get("globalObjects", {})
        object_notifications = globalObjects.get("notifications", {})
        instructions = notifications["timeline"]["instructions"]
        new_entries = []
        for x in instructions:
            addEntries = x.get("addEntries")
            if addEntries:
                entries = addEntries["entries"]
                new_entries.append(entries)
                for x in entries:
                    entryId = x["entryId"]
                    find_cursor_top = entryId.find("cursor-top")
                    if find_cursor_top != -1:
                        content = x["content"]
                        operation = content.get("operation")
                        if operation:
                            cursor = operation["cursor"]["value"]
                            if cursor:
                                params["cursor"] = cursor

        # Extract all tweet notifications from the response
        tweet_notifications = [
            notification
            for notification in object_notifications.values()
            if "text" in notification["message"]
        ]

        # Sort notifications by timestamp (newest first)
        tweet_notifications.sort(key=lambda x: x["timestampMs"], reverse=True)
        tweet_id = None
        for notification in tweet_notifications:
            # if print(notification["message"]["text"]) includes "There was a login", continue
            if (
                "There was a login" in notification["message"]["text"]
                or "liked a Tweet you" in notification["message"]["text"]
            ):
                continue

            # Skip notifications we've already responded to
            if (
                last_responded_notification is not None
                and notification["timestampMs"] <= last_responded_notification
            ):
                continue

            targetObjects = (
                notification.get("template", {})
                .get("aggregateUserActionsV1", {})
                .get("targetObjects", [{}])
            )
            if len(targetObjects) > 0:
                tweet_id = targetObjects[0].get("tweet", {}).get("id")

            tweet_details = scraper.tweets_details([tweet_id])

            # get the tweet

            arguments = {
                "tweet_id": tweet_id,
                "notification": notification,
                "tweet": tweet_details[0],
                "account": account,
                "session": session,
            }

            # call response handlers here with the notification as the argument
            for handler in feed_handlers:
                # if the handler is async, await it, otherwise call directly
                if asyncio.iscoroutinefunction(handler):
                    asyncio.run(handler(arguments))
                else:
                    handler(arguments)

            # Update the latest responded notification timestamp
            last_responded_notification = notification["timestampMs"]

        time.sleep(10 + random.randint(0, 2))


def start_twitter(
    email=None,
    username=None,
    password=None,
    session_storage_path="twitter.cookies",
    start_loop=True,
):
    """
    Starts the Twitter connector. Initializes the global account object and starts the feed loop in a new thread.

    Parameters:
        email (str, optional): The email address to be used for the Twitter account. If not provided, will be loaded from environment variables.
        username (str, optional): The username to be used for the Twitter account. If not provided, will be loaded from environment variables.
        password (str, optional): The password to be used for the Twitter account. If not provided, will be loaded from environment variables.
        session_storage_path (str, optional): The path where session data should be stored. Defaults to "twitter.cookies".
        start_loop (bool, optional): Whether the feed loop should be started immediately. Defaults to True.

    Returns:
        threading.Thread: The thread where the feed loop is running.
    """
    global account
    # get the environment variables
    if email is None:
        email = os.getenv("TWITTER_EMAIL")
    if username is None:
        username = os.getenv("TWITTER_USERNAME")
    if password is None:
        password = os.getenv("TWITTER_PASSWORD")

    session_file = Path(session_storage_path)
    session = None

    if session_file.exists():
        cookies = orjson.loads(session_file.read_bytes())
        session = Client(cookies=cookies)
        account = Account(session=session)
        scraper = Scraper(session=session)
    else:
        session = init_session()
        account = Account(email=email, username=username, password=password)
        scraper = Scraper(session=session)
        cookies = {
            k: v
            for k, v in account.session.cookies.items()
            if k in {"ct0", "auth_token"}
        }
        session_file.write_bytes(orjson.dumps(cookies))

    if start_loop:
        thread = threading.Thread(target=feed_loop, args=(account, session, scraper))
        thread.start()
        return thread


def start_connector():
    """
    Convenience function to start the Twitter connector. This function calls start_twitter with the default arguments.
    """
    start_twitter()
