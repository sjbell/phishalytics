import tweepy
import json
import time
import MySQLdb as mdb
import MySQLdb.cursors
import dateutil.parser
import sys
import urllib
import httplib

with open('config.json') as data_file:    
	config = json.load(data_file)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def checkHashTagExists(hashtag):
	cursor = con.cursor()
	cursor.execute("SELECT count(*) FROM phishing_v2.trending_hashtags WHERE name = %s", (hashtag,))
	row = cursor.fetchone()
	while row is not None:
		result = row[0]
		row = cursor.fetchone()
	cursor.close()
	return result>0

#def saveHashTag(hashtag, woeid, loc_name, country, country_code, tweet_volume, promoted):
def saveHashTag(hashtag, tweet_volume, promoted):
	cur = con.cursor()
	if not checkHashTagExists(hashtag):
		
		#sql = "INSERT INTO trending_hashtags(name, woeid, loc_name, country, country_code, tweet_volume, promoted) VALUES(%s, %s, %s, %s, %s, %s, %s)"
		#cur.execute(sql, (hashtag, woeid, loc_name, country, country_code, tweet_volume, promoted))
		sql = "INSERT INTO trending_hashtags(name, tweet_volume, promoted) VALUES( %s, %s, %s)"
		cur.execute(sql, (hashtag, tweet_volume, promoted))
		cur.close()
		return True
	else:
		cur.close()
		return False

while True:
	try:
		#con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		#con.autocommit(True)
		#saved_counter = 0
		auth = tweepy.OAuthHandler(config['twitter-api']['consumer_key'], config['twitter-api']['consumer_secret'])
		auth.set_access_token(config['twitter-api']['access_token'], config['twitter-api']['access_token_secret'])
		api = tweepy.API(auth)

		counter = 0
		trends_len = 0
		trends_list = []
		trends_place = api.trends_place(44418)
		trends = trends_place[0]['trends']
		for trend in reversed(trends):
			if trend['name'].startswith('#'):
				trends_list.append(trend['name'])
				trends_len += 1
		for h in trends_list:
			print str(trends_len-counter)+": "+h
			time.sleep(1)
			counter += 1
				#saveHashTag(trend['name'], w['woeid'], w['name'], w['country'], w['countryCode'], trend['tweet_volume'], trend['promoted_content'])
				#if saveHashTag(trend['name'], trend['tweet_volume'], trend['promoted_content']):
				#	saved_counter += 1 
		
		#print "\nnumber of hashtags:",len(trends_list)
		#print "number saved:",saved_counter
		#rate_limit = api.rate_limit_status()
		#print rate_limit
		#print "rate limit:",str(rate_limit['resources']['trends']['/trends/place']['limit']-rate_limit['resources']['trends']['/trends/place']['remaining'])+"/"+str(rate_limit['resources']['trends']['/trends/place']['limit'])+" (per 15 min)"
		#print "waiting 5 minutes until next update..."
		#con.close()
		#print bcolors.WARNING + "Warning: No active frommets remain. Continue?" + bcolors.ENDC
		time.sleep(30)

	except tweepy.TweepError as e:
		#print e.message[0]['code']  # prints 34
		#print e.args[0][0]['code']  # prints 34
		print "Exception: %s" % e
		#print e
		time.sleep(90)
	except httplib.IncompleteRead:
		# Oh well, reconnect and keep trucking
		print "There was a httplib.IncompleteRead. Ignoring..."
		time.sleep(90)
	except TypeError as e:
		print "Type error: ",e
		time.sleep(90)
	except:
		print "We have an error:", sys.exc_info()[1]
		print "waiting 90 seconds"
		time.sleep(90)
