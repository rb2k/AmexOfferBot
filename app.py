import tweepy
import re
import json
import time


class AmexOfferBot(object):
    
    FILENAME_CONFIGURATION = "config.json"
    FILENAME_HASHTAG_MEMORY = "hashtag_memory.json"

    def __init__(self):
        self.configuration = self.load_configuration()
        self.tweeted_hashtags = self.load_hashtag_memory()
        self.api = self.authenticate_api()

    def load_configuration(self):
        try:
            with open(AmexOfferBot.FILENAME_CONFIGURATION, "r") as configuration_file:
                configuration = json.load(configuration_file)
                print 'Loaded Configuration.'
                missing_keys = set(["consumer_key", "consumer_secret", "access_token", "access_token_secret"]) - set(configuration.viewkeys())
                if missing_keys:
                    print "Missing configuration items: " + str(list(missing_keys))
                    exit(1)
                return configuration
        except (IOError, ValueError) as e:
            print "Problem loading the configuration file. Exiting." + str(e)
            exit(1)

    def authenticate_api(self):
        auth = tweepy.OAuthHandler(self.configuration['consumer_key'], self.configuration['consumer_secret'])
        auth.set_access_token(self.configuration['access_token'], self.configuration['access_token_secret'])
        api = tweepy.API(auth)
        return api

    def post_and_remove_offer(self, hashtag):
        print 'Registering'
        tweet_text = "@amexoffers " + hashtag
        current_tweet = self.api.update_status(status=tweet_text)
        print 'Sleeping for a minute so Amex notices'
        time.sleep(60)
        print 'Removing tweet again'
        self.api.destroy_status(current_tweet.id)

    def save_hashtag_memory(self, tweeted_hashtags):
        with open(AmexOfferBot.FILENAME_HASHTAG_MEMORY, "w+") as memory_file:
            json.dump(tweeted_hashtags, memory_file)

    def load_hashtag_memory(self):
        try:
            with open(AmexOfferBot.FILENAME_HASHTAG_MEMORY, "r") as memory_file:
                tweeted_hashtags = json.load(memory_file)
                print 'Loaded hashtag memory. (Total items found: ' + str(len(tweeted_hashtags)) + ')'
        except (IOError, ValueError) as e:
            print "Problem loading the memory file. First start? Running with empty hashtag memory."
            tweeted_hashtags = []
        return tweeted_hashtags


    def run(self):
        print "Starting processing."
        current_run_counter = 0
        favs = self.api.favorites('AmericanExpress')
        for fav in favs:
            text = fav.text
            hashtag = re.search('(#\w+)', text).group(1)
            if hashtag in self.tweeted_hashtags:
                # Already processed, skipping
                continue
            else:
                print "Found a new offer! Processing " + hashtag
                offer_text = re.search('get (.*) w/', text).group(1)
                print 'Offer text: ' + offer_text
                self.post_and_remove_offer(hashtag)
                current_run_counter += 1
                self.tweeted_hashtags.append(hashtag)

        print "Finished processing."
        print "Items processed during this run: " + str(current_run_counter)
        print "Number of offers ever processed: " + str(len(self.tweeted_hashtags))
        self.save_hashtag_memory(self.tweeted_hashtags)

bot = AmexOfferBot()
while True:
    try:
        bot.run()
        time.sleep(15)
    except KeyboardInterrupt as e:
        print "Bye!"
        exit(0)