import asyncio
import os
import json
from agentcomms.twitter import (
    start_twitter,
    like_tweet,
    reply_to_tweet,
    tweet,
    search_tweets,
    get_authors,
    get_relevant_tweets_from_author_timeline,
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


def test_search_tweets(topic=None, limit=None, **kwargs):
    setup_function()
    if limit is None:
        limit = 10
    res = search_tweets(topic, limit, retries=5, **kwargs)
    return res


def test_get_authors(tweets_data, **kwargs):
    setup_function()
    authors = get_authors(tweets_data)
    return authors


def test_get_relevant_tweets_from_author_timeline(topic, author):
    setup_function()
    documents = get_relevant_tweets_from_author_timeline(topic, author)
    return documents


def test_register_and_unregister_feed_handler():
    setup_function()
    handler = lambda x: print(x)
    register_feed_handler(handler)
    # Here you can add logic to verify the handler was registered, such as checking the feed_handlers list
    unregister_feed_handler(handler)
    

if __name__=='__main__':
    topic = "Attention"
    tweets_data = test_search_tweets(f'{topic}', 5)
    authors = test_get_authors(tweets_data)
    authors = dict(sorted(authors.items(), key=lambda x: x[1]['impact_factor'], reverse=True))

    with open(f'{topic}_data.json', 'w') as file:
        json.dump(tweets_data, file, indent=4)

    with open(f'{topic}_authors.json', 'w') as file:
        json.dump(authors, file, indent=4)

    author = "GenZSiv"
    documents = test_get_relevant_tweets_from_author_timeline(topic, author)

    with open(f'documents_{author}_authors.json', 'w') as file:
        json.dump(documents, file, indent=4)
    
    
