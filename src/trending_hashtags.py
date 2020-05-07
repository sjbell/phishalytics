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


def checkHashTagExists(hashtag):
	cursor = con.cursor()
	cursor.execute("SELECT count(*) FROM trending_hashtags_5 WHERE name = %s", (hashtag,))
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
		sql = "INSERT INTO trending_hashtags_5(name, tweet_volume, promoted) VALUES( %s, %s, %s)"
		cur.execute(sql, (hashtag, tweet_volume, promoted))
		cur.close()
		return True
	else:
		cur.close()
		return False

while True:
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		con.autocommit(True)
		saved_counter = 0
		auth = tweepy.OAuthHandler(config['twitter-api']['consumer_key'], config['twitter-api']['consumer_secret'])
		auth.set_access_token(config['twitter-api']['access_token'], config['twitter-api']['access_token_secret'])
		api = tweepy.API(auth)

		trends_list = []
		trends_place = api.trends_place(1)
		trends = trends_place[0]['trends']
		for trend in reversed(trends):
			if trend['name'].startswith('#'):
				trends_list.append(trend['name'])
				print trend['name'].encode('ascii', 'ignore')
				#saveHashTag(trend['name'], w['woeid'], w['name'], w['country'], w['countryCode'], trend['tweet_volume'], trend['promoted_content'])
				if saveHashTag(trend['name'], trend['tweet_volume'], trend['promoted_content']):
					saved_counter += 1 
		
		print "\nnum hashtags:",len(trends_list)
		print "num saved:",saved_counter
		rate_limit = api.rate_limit_status()
		#print rate_limit
		print "rate limit:",str(rate_limit['resources']['trends']['/trends/place']['limit']-rate_limit['resources']['trends']['/trends/place']['remaining'])+"/"+str(rate_limit['resources']['trends']['/trends/place']['limit'])+" (per 15 min)"
		print "waiting 60 secs..."
		con.close()
		time.sleep(60)

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
		print "Error:", sys.exc_info()[1]
		print "waiting 90 secs"
		time.sleep(90)
#except:
#	print "Unknown error...", sys.exc_info()[0]

# code below will look up all available trending woeid's then perform a lookup
# of all trending hashtags for each woeid. Rate limit of 75 per 15 minutes on
# trending hastags per woeid makes this impossible
'''
	trends_list = []
	trends_dict = {}



	rate_limit = api.rate_limit_status()
	#print rate_limit
	print rate_limit['resources']['trends']
	trends_available = api.trends_available()
	
	#for l in trends_available:
		#print l
		#print l['name']
		#print l['woeid']
	print len(trends_available)
	time.sleep(10)
	exit()
	
	for w in trends_available:
		trends_place = api.trends_place(w['woeid'])
		trends = trends_place[0]['trends']
		for trend in trends:
			if trend['name'].startswith('#'):
				trends_list.append(trend['name'])
				trends_dict[trend['name']] = 0
				saveHashTag(trend['name'], w['woeid'], w['name'], w['country'], w['countryCode'], trend['tweet_volume'], trend['promoted_content'])
		time.sleep(100)
		print "yes"
		#for i in reversed(trends_list):
		#	print i
	print len(trends_list)
	print len(trends_dict)
	'''


