import os
import pdb
import asyncio
from pathlib import Path
import random
import threading
import time
from httpx import Client
from twitter.account import Account
from twitter.scraper import Scraper
from twitter.search import Search
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
search = None

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


def fetch_data(query, limit, retries):
    """
    Fetches data based on the provided search query.

    Args:
    - query (str): The search query.
    - limit (int): Maximum number of results to return.
    - retries (int): Number of times to retry the search in case of failure.

    Returns:
    - list[dict]: List of search results.
    """
    queries = [
        {
            'category': 'Latest',
            'query': query
        },
        {
            'category': 'Top',
            'query': query
        }
    ]
    results = search.run(limit=limit, retries=retries, queries=queries)
    results = [data for result in results for data in result]
    return results

def search_tweets(topic, min_results=30, max_retries=5, **filters):
    """
    Searches for tweets based on provided criteria and returns a filtered list.

    Parameters:
        topic (str): The primary search term or phrase.
        min_results (int, optional): Minimum desired number of results. Default is 30.
        max_retries (int, optional): Maximum number of retries in case of search failures. Default is 5.
        filters (dict, optional): Additional parameters to filter the search results. 

    Returns:
        list: A list of tweets that match the search criteria.

    TODO:
    - Enhance query structure:
        - Support advanced query operations (e.g., AND, OR).
        - Implement exact phrase matching and exclusion of terms.
    - Integrate time-based filters for refined search.
    - Incorporate Twitter Spaces transcriptions for deeper content insights.
    - Develop logic for handling retweets and associated content nuances.
    """

    # Extracting and constructing search filters
    min_faves = filters.get('min_faves', 0)
    min_retweets = filters.get('min_retweets', 0)
    min_replies = filters.get('min_replies', 0)
    verified_only = filters.get('verified_only', False)

    # TODO direct mapping for now.    
    # TODO Generate queries from topic similar to above.
    query = topic
    # Appending filters to the base query
    if min_faves:
        query += f" min_faves:{min_faves}"
    if min_retweets:
        query += f" min_retweets:{min_retweets}"
    if min_replies:
        query += f" min_replies:{min_replies}"
    if verified_only:
        query += " filter:verified"

    results = fetch_data(query, min_results, max_retries)
    # concatenation hack
    return results


def get_authors(tweets_data, **filters):
    """
    Extracts a list of authors from the provided tweet data based on specified filters.

    Parameters:
        tweets_data (list[dict]): A list of dictionaries representing tweet data.
        filters (dict): Optional filters to refine the list of authors, including 'follower_count_min', 'search_keywords', and 'verified_only'.

    Returns:
        dict: A dictionary mapping screen names to author data.
    """

    def calculate_impact_factor(tweet_impact_data):
        """Compute the impact factor based on various tweet metrics."""
        return sum([
            tweet_impact_data.get(metric, 0)
            for metric in ['bookmark_count', 'favorite_count', 'reply_count', 'retweet_count']
        ])

    # Extract filters
    follower_count_min = filters.get('follower_count_min', 0)
    verified_only = filters.get('verified_only', False)

    authors = {}

    for tweet_data in tweets_data:
        # Extract relevant data points
        pdb.set_trace()
        tweet_result = tweet_data.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
        user_data_core = tweet_result.get('core', {}).get('user_results', {}).get('result', {})
        user_data = user_data_core.get('legacy', {})
        tweet_impact_data = tweet_result.get('legacy', {})
        tweet_impact_data['views'] = tweet_result.get('views', {})

        # Checks
        if "tweet" not in tweet_data.get('entryId', '') or not user_data or not tweet_impact_data:
            continue
        if verified_only and not user_data_core.get('is_blue_verified', False):
            continue
        if user_data.get('followers_count', 0) < follower_count_min:
            continue

        # Calculate impact factor
        impact_factor = calculate_impact_factor(tweet_impact_data)

        # Extract and accumulate author data
        author_info = {
            'id': user_data.get('id'),
            'name': user_data.get('name'),
            'screen_name': user_data.get('screen_name'),
            'followers_count': user_data.get('followers_count'),
            'description': user_data.get('description'),
            'favourites_count': user_data.get('favourites_count'),
            'friends_count': user_data.get('friends_count'),
            'normal_follower_count': user_data.get('normal_followers_count'),
            'views': int(tweet_impact_data.get('views', {}).get('count', 0)),
            'impact_factor': impact_factor,
        }
        author_url = author_info['screen_name']
        if author_url not in authors:
            authors[author_url] = author_info
        else:
            # pdb.set_trace()
            authors[author_url]['views'] += int(author_info['views'])
            authors[author_url]['impact_factor'] += author_info['impact_factor']

    # TODO Further enhancements: Normalize impact factor, consider tweet age/time, etc.
    return authors


    """
    CHATGPT PROMPT:
    I want to search tweets to rank authors who write about a particular topic, you are my `research and media assistant`. Given a topic, give me relevant queries I should search for on twitter. The queries should be ranked based on usage.

    topic:
    AI Existential Risk
    queries:

    REPLY:
    For the topic "AI Existential Risk," here's a list of potential queries ranked based on usage and relevance:

    1. "AI Existential Risk"
    2. "Artificial Intelligence existential threat"
    3. "AI and global catastrophic risks"
    4. "Dangers of superintelligent AI"
    5. "Risks of advanced AI"
    6. "Long-term AI safety concerns"
    7. "Unintended consequences of AI"
    8. "AI and end of humanity concerns"
    9. "Machine learning existential threats"
    10. "Ethical concerns of powerful AI"

    These queries encapsulate various ways people might discuss the existential risks of AI on Twitter. They range from the direct ("AI Existential Risk") to the more nuanced or indirect ("Ethical concerns of powerful AI").
    """
    # TODO Generate queries from topic similar to above.

def extract_document_from_tweet(tweet_data):
    """
    Extracts relevant information from a tweet to construct a document.

    Args:
    - tweet_data (dict): The raw tweet data.

    Returns:
    - str: A formatted document containing relevant information from the tweet.
    """
    tweet_result = tweet_data.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
    user_data = tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
    
    return (f"author_name: {user_data.get('name')}\n"
            f"screen_name: {user_data.get('screen_name')}\n"
            f"full_text: {tweet_result.get('legacy', {}).get('full_text', '')}\n"
            f"created_at: {tweet_result.get('legacy', {}).get('created_at', '')}\n\n\n")


def get_relevant_tweets_from_author_timeline(topic, author, min_results=30, max_retries=5, **filters):
    """
    Fetches and processes tweets related to a given topic from a specific author's timeline.

    Args:
    - topic (str): The main topic or keyword for which tweets are to be fetched.
    - author (str): The screen name of the Twitter user.
    - min_results (int): Minimum number of results to return per query.
    - max_retries (int): Number of times to retry the search in case of failure.

    Returns:
    - dict: A dictionary where the key is the conversation_id and the value is a document constructed from all relevant tweets.
    """
    query = topic + f" (from:{author})"
    tweets_data = fetch_data(query, min_results, max_retries)

    documents = {}
    
    for tweet_data in tweets_data:
        pdb.set_trace()
        tweet_result = tweet_data.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
        conversation_id = tweet_result['legacy']['conversation_id_str']
        
        if conversation_id in documents:
            continue
        pdb.set_trace()
        quote_tweet_id = int(tweet_result.get('legacy', {}).get('quoted_status_id_str', 0))
        conversation_data = fetch_data(f"(conversation_id:{conversation_id})", min_results, max_retries)
        try:
            origin_tweet_data = [scraper.tweets_details([int(conversation_id)])[0]['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries'][0]]
            # TODO handle case where origin_tweet has quote_tweet
            # use origin_tweet_data to update quote_tweet_id from 0 to x.
            quote_tweet_data = [scraper.tweets_details([quote_tweet_id])[0]['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries'][0]] if quote_tweet_id else []
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Error: Error scraping for origin_tweet_data and quote_tweet_data")
            origin_tweet_data = []
            quote_tweet_data = []
        all_tweets_in_conversation = origin_tweet_data + quote_tweet_data + conversation_data
        documents[conversation_id] = ''.join([extract_document_from_tweet(data) for data in all_tweets_in_conversation])    
    
    return documents

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


def feed_loop(account, session):
    """
    Main feed loop. This function checks for new tweets and passes them to all registered feed handlers.

    Parameters:
        account (twitter.account.Account): The account object to be used for the feed operations.
        session (httpx.Client): The httpx session to be used for the feed operations.
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
    loop_dict=None,
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
    global search
    global scraper
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
    
    search = Search(email=email, username=username, password=password, save=True, debug=1)

    if start_loop:
        thread = threading.Thread(target=feed_loop, args=(account, session, scraper))
        thread.start()
        return thread


def start_connector(
    loop_dict=None, # dict of information for stopping the loop, etc
    email=None,
    username=None,
    password=None,
    session_storage_path="twitter.cookies",
    start_loop=True,
):
    """
    Convenience function to start the Twitter connector. This function calls start_twitter with the default arguments.
    """
    start_twitter(
        email=None,
        username=None,
        password=None,
        session_storage_path="twitter.cookies",
        start_loop=True,
        loop_dict=None,
    )
