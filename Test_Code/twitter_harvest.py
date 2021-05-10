import twitter_miner
import time
from copy import deepcopy
import json

# read configuration from the config json file
with open('config.json') as file:
    config = json.load(file)

# set up miner to harvest tweets
account_info = config['account_info']
miner = twitter_miner.TwitterMiner(account_info, 60)

# set up city list and geo code to search
city_list = config['city_list']
city_name_list = []
city_geocode_dict = {}
location_list = []
for city in city_list:
    city_name_list.append(city['city_name'])
    city_geocode_dict[city['city_name']] = city['geo_code']
    location_list = location_list + city['location']

# set up the corresponding database log in info
login_info = config['couchdb_info']['login_url']
database_name = config['couchdb_info']['database_name']

# complement food list to a full list, here we test with pizza and burger
food_keyword = ['pizza', 'burger']


# get the original twitters
search_tweets_list = []
for food_name in food_keyword:
    for city_name in city_name_list:
        search_tweets_list = search_tweets_list + miner.mineSearchTweets(food_name, city_geocode_dict[city_name])


# get the original twitters' author and deduplicate
author_id_list = []
for twitter in search_tweets_list:
    author_id_list.append(twitter['user_id'])
author_id_list = list(set(author_id_list))
search_id_list = deepcopy(author_id_list)


# start tweets harvest using timeline and author's followers
harvest_round = 1
max_harvest_round = 1
# final max round should be 2
while harvest_round <= max_harvest_round:
    followers_harvest_list = []
    follower_index = 0
    while follower_index < len(search_id_list):
        mined_followers_list = miner.mineUserFollowers(search_id_list[follower_index])
        follower_index += 1
        followers_harvest_list = followers_harvest_list + mined_followers_list
        if (follower_index % 15) == 0:
            time.sleep(900)

    # deduplicate
    followers_harvest_list = list(set(followers_harvest_list))
    for searched_account in followers_harvest_list:
        if searched_account in author_id_list:
            search_id_list.remove(searched_account)

    # check user location
    follower_search_count = 0
    for follower_id in followers_harvest_list:
        location = miner.getUserProfile(follower_id)
        follower_search_count += 1
        if location is None or location not in location_list:
            followers_harvest_list.remove(follower_id)
        if follower_search_count % 900 == 0:
            time.sleep(900)

    search_id_list = deepcopy(followers_harvest_list)
    author_id_list = author_id_list + followers_harvest_list

    timeline_search_index = 0
    timeline_tweets = []
    while timeline_search_index < len(followers_harvest_list):
        mined_timeline_tweets = miner.mineUserTimeline(followers_harvest_list[timeline_search_index], 5)
        timeline_tweets = timeline_tweets + mined_timeline_tweets
        timeline_search_index += 1
        if timeline_search_index % 1500 == 0:
            # send the timeline tweets to the couchdb
            time.sleep(900)

    # send the remaining tweets to the couchdb


    # test code store the mined tweets
    jsonStr = json.dumps(timeline_tweets)
    with open('tweets_mined') as output:
        json.dump(jsonStr, output)
    # test code store the mined tweets

    harvest_round += 1

