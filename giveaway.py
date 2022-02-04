import requests
import json
import random

# Fill this in
BEARER_TOKEN = ""
LIKE_PATH = "https://api.twitter.com/2/tweets/{0}/liking_users"
RT_PATH = "https://api.twitter.com/2/tweets/{0}/retweeted_by"
FOLLOWERS_PATH = "https://api.twitter.com/2/users/{0}/followers"
TWEET_DATA = "https://api.twitter.com/2/tweets/{0}"
USER_DATA_PATH = 'https://api.twitter.com/2/users/{0}'
SEARCH_TWEET =  'https://api.twitter.com/2/tweets/search/recent?query=conversation_id:{0}&tweet.fields=author_id&expansions=entities.mentions.username&user.fields=username'

# Add TWEET_IDS and USER_IDS here
TWEET_IDS = []
USER_IDS = []
HEADER = {"Authorization": "Bearer " + BEARER_TOKEN }

likes = []
followers = []
retweets = []
valid_entries = []

def get_data(path, header, list):
    params = {}
    while(True):
        r = requests.get(path, headers=header, params=params)
        jsonData = r.json()
        if jsonData['meta']['result_count'] == 0: 
            break

        for entry in jsonData['data']:
            list.append(entry['username'])
        
        if "next_token" in jsonData['meta']:
            params['pagination_token'] = jsonData['meta']['next_token']
        else:
            break

def add_additional_entries():
    tweet_data_params = {"tweet.fields": "conversation_id"}
    search_tweet_params = {'max_results': 100}

    # Get the tweet data because we need the conversation_id to be able to get all the replies
    tweet_data_request = requests.get(TWEET_DATA.format(TWEET_IDS[0]), headers=HEADER, params=tweet_data_params)
    tweet_data = tweet_data_request.json()
    conversation_id = tweet_data['data']['conversation_id']

    # Replies are returned in pages of 100 results, loop until the response doesnt contain a pagination token (ie next_token) in the meta field
    while True:
        search_tweet_request = requests.get(SEARCH_TWEET.format(conversation_id), headers=HEADER, params=search_tweet_params)
        search_data = search_tweet_request.json()

        replies = search_data['data']
        for reply in replies:
            author_id = reply['author_id']
            if 'entities' in reply:
                number_of_mentions = len(reply['entities']['mentions']) - 1 # remove the author from the mentions
                # Since we only have the user id we need to convert it to a username
                user_data_request = requests.get(USER_DATA_PATH.format(author_id), headers=HEADER)
                user_data = user_data_request.json()
                username = user_data['data']['username']
                # All valid entries were required to like, retweet and follow
                if username in likes and username in retweets and username in followers:
                    for i in range(number_of_mentions):
                        valid_entries.append(username)
        
        if "next_token" in search_data['meta']:
                search_tweet_params['pagination_token'] = search_data['meta']['next_token']
        else:
            break


# Get all the users that liked and retweeted the tweet id in TWEET_IDS
for id in TWEET_IDS:
    get_data(LIKE_PATH.format(id), HEADER, likes)
    get_data(RT_PATH.format(id), HEADER, retweets)

# Get all the followers of each user_id in USER_IDS
for user_id in USER_IDS:
    get_data(FOLLOWERS_PATH.format(user_id), HEADER, followers)

# add 1 additional entry for each person tagged
add_additional_entries()

# Since a requirement was to follow the accounts, we can loop through the followers and check if they RTd and Liked
for person in followers:
    if person in likes and person in retweets:
        valid_entries.append(person)

# Shuffle the valid entries so that the names are randomly distributed (since additional entries would otherwise be consecutive)
random.shuffle(valid_entries)

winner_index = random.randint(0, len(valid_entries) - 1)
winner = valid_entries[winner_index]

# Some metrics
print("TOTAL LIKES: {0} | TOTAL RTS: {1} | TOTAL FOLLOWERS: {2} | TOTAL VALID ENTRIES: {3}".format(len(likes), len(retweets), len(followers), len(valid_entries)))
print("The 1st winner of the giveaway is: {0} at index: {1}".format(winner, winner_index))
