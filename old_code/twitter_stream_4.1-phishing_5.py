import tweepy
import json
import time
import MySQLdb as mdb
import dateutil.parser
import sys
import urllib
import httplib
import datetime

with open('config.json') as data_file:    
	config = json.load(data_file)

def getTS():
  return ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
#cur = con.cursor()

tweet_text_global = ""

def extractData(decoded, retweet):
	cur = con.cursor()

	sys.stdout.write('.')
	sys.stdout.flush()
	url_text = ""
	urls = []
	#t_co_urls = []

	for i in decoded['entities']['urls']:
		url = i['expanded_url']
		t_co_url = i['url']
		#url = i['expanded_url'][:75] #removed on 16-Feb-2017 as causing error
		if url:
			url_text += url + ","
			urls.append((url, t_co_url))
			#t_co_urls.append(t_co_url)


	tweet_id = decoded['id']

	date_tweeted_ = dateutil.parser.parse(decoded['created_at'])
	date_tweeted = date_tweeted_.strftime('%Y-%m-%d %H:%M:%S')

	account_created_ = dateutil.parser.parse(decoded['user']['created_at'])
	account_created = account_created_.strftime('%Y-%m-%d %H:%M:%S')

	tweet_text = decoded['text'].encode('ascii', 'ignore')
	tweet_text_global = tweet_text
	friends_count = decoded['user']['friends_count']
	followers_count = decoded['user']['followers_count']
	username = decoded['user']['screen_name']
	user_default_profile = decoded['user']['default_profile']
	user_num_tweets = decoded['user']['statuses_count']
	if decoded['user']['description']:
		user_description = decoded['user']['description'].encode('ascii', 'ignore')
	else:
		user_description = ""

	user_favourites_count = decoded['user']['favourites_count']
	user_listed_count = decoded['user']['listed_count']
	
	account_age = str(int((date_tweeted_-account_created_).total_seconds()))
	num_at_tags = tweet_text.count('@')
	num_hash_tags = tweet_text.count('#')

	favourite_count = decoded['favorite_count']
	retweet_count = decoded['retweet_count']

	# get list of hashtags if it exists
	hashtags = decoded['entities']['hashtags']
	hashtags_string = ""
	hashtags_indices_string = ""
	if len(hashtags) > 0:
		for h in hashtags:
			hashtags_indices_string += str(h['indices'][0]) + ':' + str(h['indices'][1]) +  ', '
			hashtags_string += h['text'] + ','
	hashtags_string =  hashtags_string.encode('ascii',errors='ignore')

	if friends_count > 0:
		tff_ratio = float(followers_count)/float(friends_count)
	else:
		tff_ratio = followers_count

	if retweet:
		retweet_value = 1
	else:
		retweet_value = 0

	if url_text:
		sql = "INSERT INTO tweets_5(tweet_text, urls, username, date_tweeted, account_created, friends, followers, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags, hashtags_indices, user_num_tweets, retweet, tweet_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		cur.execute(sql, (tweet_text[:200], url_text[:1000], username, date_tweeted, account_created, friends_count, followers_count, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags_string, hashtags_indices_string, user_num_tweets, retweet_value, tweet_id ))
		last_id = cur.lastrowid

		# insert URLs
		for url in urls:
			#if len(url) > 1000:
			#	from send_email import sendAdminAlert
			#	sendAdminAlert("tweeted URL > 1000", "A URL has been added to tweet_urls_5 that's longer than 1000 chars.\n\nURL Len: "+str(len(url))+"\nURL: "+url+"\nShortened URL: "+url[:1000]+"\n\nIf this keeps happening maybe alter url length in db.\n\nThis is coming from line 93 (ish) of twitter_Stream_4.1-phishing_5")

			sql = "INSERT INTO tweet_urls_5b(tweet_id, url, t_co_url) VALUES(%s, %s, %s)"
			cur.execute(sql, (last_id, url[0][:1000], url[1][:1000]))
			
			sys.stdout.write('!')
			sys.stdout.flush()			

		sys.stdout.write('+')
		sys.stdout.flush()
		#counter += 1 
	'''else:
		url_text = str(len(decoded['entities']['urls'])) + url_text
		sql = "INSERT INTO tweets_3_no_urls(tweet_text, urls, username, date_tweeted, account_created, friends, followers, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags, hashtags_indices, user_num_tweets) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		cur.execute(sql, (tweet_text, url_text, username, date_tweeted, account_created, friends_count, followers_count, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags_string, hashtags_indices_string, user_num_tweets ))
		last_id = cur.lastrowid
	'''
	cur.close()
	return True


# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):

	def on_data(self, data):
		
		#try:
			# Twitter returns data in JSON format - we need to decode it first
			decoded = json.loads(data)
			#counter = 0

			if "retweeted_status" in decoded:
				sys.stdout.write('#')
				extractData(decoded['retweeted_status'], True)
			if "user" and "entities" and "created_at" in decoded:
				extractData(decoded, False)
			#else:
				#return False
		#except:
		#	print "We have an error:", sys.exc_info()[1]
		#	print "waiting 90 seconds"
		#	time.sleep(90)
			#print "?"
			#time.sleep(1)

	def on_error(self, status):
		if status == 420:
			print "HTTP 420 error: rate limit\nWaiting 60 minutes..."
			print time.strftime("%Y-%m-%d %H:%M")
			time.sleep(120)
			stream.disconnect()
			return False
		else:
			print "Status: ",status
			time.sleep(30)

	#def __init__(self):
		#self.counter = 0

if __name__ == '__main__':
  while True:
	try:
		
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8')
		con.autocommit(True)

		l = StdOutListener()
		auth = tweepy.OAuthHandler(config['twitter-api']['consumer_key'], config['twitter-api']['consumer_secret'])
		auth.set_access_token(config['twitter-api']['access_token'], config['twitter-api']['access_token_secret'])

		print "Streaming tweets..."

		stream = tweepy.Stream(auth, l)
		#stream.sample()
		#stream.filter(track=['t co'])
		stream.filter(track=['http,https'])

		con.close()
		time.sleep(10)
	except tweepy.TweepError as e:
		print e.message[0]['code']  # prints 34
		print e.args[0][0]['code']  # prints 34
		print getTS()
		#print "Exception: %s" % e
		#print e
		time.sleep(10)
	except httplib.IncompleteRead:
		# Oh well, reconnect and keep trucking
		print "There was a httplib.IncompleteRead. Ignoring..."
		print getTS()
		continue
	except KeyboardInterrupt:
		# Or however you want to exit this loop
		stream.disconnect()
		break
	except TypeError as e:
		print "Type error: ",e
		print getTS()
		time.sleep(90)
	except mdb.Error, e:
		print "We have an error:", sys.exc_info()[1]
		import os
		import sys
		import traceback
		from send_email import sendAdminAlert
		script_file_name = os.path.basename(__file__)
		error_string = ""
		for frame in traceback.extract_tb(sys.exc_info()[2]):
			fname,lineno,fn,text = frame
			error_string += "\nError in %s on line %d" % (fname, lineno)
		print error_string
		sendAdminAlert("MySQL error in main twitter stream (i.e URL filter)", 
		"Python script: "+script_file_name+"\nError reported: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string))
		print "Will try to reconnect to MySQL server in 90 seconds..."
		print getTS()
		time.sleep(90)

		#con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		#cursor = con.cursor()
		#con.autocommit(True)

	except:
		print "We have an error:", sys.exc_info()[1]
		import os
		import sys
		import traceback
		from send_email import sendAdminAlert
		script_file_name = os.path.basename(__file__)
		error_string = ""
		for frame in traceback.extract_tb(sys.exc_info()[2]):
			fname,lineno,fn,text = frame
			error_string += "\nError in %s on line %d" % (fname, lineno)
		#sendAdminAlert("Error in "+script_file_name,
		#"Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string) + "\ntweet_text: "+tweet_text_global)

		cur = con.cursor()
		#sql = "INSERT INTO twitter_stream_error_log(twitter_stream, error_reported, notes) VALUES(%s, %s)"
		#cur.execute(sql, (1, ""+str(sys.exc_info()[1]), "Error in "+script_file_name+", Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string) + "\ntweet_text: "+tweet_text_global))
		sql = "INSERT INTO twitter_stream_error_log(twitter_stream, error_reported, notes) VALUES(%s, %s, %s)"
		cur.execute(sql, (1, str(sys.exc_info()[1]), "Error in "+script_file_name+", Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string) + "\ntweet_text: "+tweet_text_global))

		print "waiting 90 seconds"
		print getTS()
		time.sleep(90)
		continue
