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
#con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_4'],charset='utf8')

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):

	def on_data(self, data):
		
		#try:
			cur = con.cursor()
			# Twitter returns data in JSON format - we need to decode it first
			decoded = json.loads(data)
			
			if "retweeted_status" in decoded:
				sys.stdout.write('#')
			#counter = 0
			if "user" and "entities" and "created_at" in decoded:
				sys.stdout.write('.')
				sys.stdout.flush()
				url_text = ""
				urls = []
				for i in decoded['entities']['urls']:
					url = i['expanded_url']
					#url = i['expanded_url'][:75] #removed on 16-Feb-2017 as causing error
					if url:
						url_text += url + ","
						urls.append(url)
				
				date_tweeted_ = dateutil.parser.parse(decoded['created_at'])
				date_tweeted = date_tweeted_.strftime('%Y-%m-%d %H:%M:%S')

				account_created_ = dateutil.parser.parse(decoded['user']['created_at'])
				account_created = account_created_.strftime('%Y-%m-%d %H:%M:%S')

				tweet_text = decoded['text'].encode('ascii', 'ignore')
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
				#hashtags_string.encode('unicode_escape')
				#hashtags_string.encode('utf8')
				hashtags_string = hashtags_string.encode('ascii', 'ignore')
				
				if friends_count > 0:
					tff_ratio = float(followers_count)/float(friends_count)
				else:
					tff_ratio = followers_count

				#if url_text:
				sql = "INSERT INTO tweets_sample_stream_5(tweet_text, urls, username, date_tweeted, account_created, friends, followers, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags, hashtags_indices, user_num_tweets) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
				cur.execute(sql, (tweet_text, url_text[:1000], username, date_tweeted, account_created, friends_count, followers_count, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags_string, hashtags_indices_string, user_num_tweets ))
				last_id = cur.lastrowid

				# insert URLs
				for url in urls:
					sys.stdout.write('!')
					sys.stdout.flush()
					#sql = "INSERT INTO tweet_urls_3(tweet_id,url) VALUES(%s, %s)"
					#cur.execute(sql, (last_id,url))
				
				sys.stdout.write('+')
				sys.stdout.flush()
				
				#counter += 1 
				'''else:
					url_text = str(len(decoded['entities']['urls'])) + url_text
					sql = "INSERT INTO tweets_3_no_urls(tweet_text, urls, username, date_tweeted, account_created, friends, followers, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags, hashtags_indices, user_num_tweets) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
					cur.execute(sql, (tweet_text, url_text, username, date_tweeted, account_created, friends_count, followers_count, tff_ratio, account_age, num_at_tags, num_hash_tags, favourite_count, retweet_count, user_default_profile, user_description, user_favourites_count, user_listed_count, hashtags_string, hashtags_indices_string, user_num_tweets ))
					last_id = cur.lastrowid
				'''

				return True
			#else:
				#return False
		#except:
		#	print "We have an error:", sys.exc_info()[1]
		#	print "Waiting 90 secs.."
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

		print "Streaming sample tweets..."

		stream = tweepy.Stream(auth, l)
		stream.sample()
		#stream.filter(track=['t co'])
		#stream.filter(track=['http,https'])

		con.close()
		time.sleep(10)
	except tweepy.TweepError as e:
		print e.message[0]['code']  # prints 34
		print e.args[0][0]['code']  # prints 34
		#print "Exception: %s" % e
		#print e
		print getTS()
		time.sleep(30)
	except httplib.IncompleteRead:
		# Oh well, reconnect and keep trucking
		print "There was a httplib.IncompleteRead. Ignoring..."
		print getTS()
		time.sleep(30)
		continue
	except KeyboardInterrupt:
		# Or however you want to exit this loop
		stream.disconnect()
		break
	except TypeError as e:
		print "Type error: ",e
		print getTS()
		time.sleep(30)
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
		sendAdminAlert("MySQL error in twitter stream sample", 
		"Python script: "+script_file_name+"\nError reported: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string)+"\n\n"+(str(getTS())))
		print "Will try to reconnect to MySQL server in 90 seconds..."
		print getTS()
		time.sleep(90)

		#con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		#cursor = con.cursor()
		#con.autocommit(True)
	except:
		print "Unknown error...", sys.exc_info()[0]
		print getTS()

		cur = con.cursor()
		sql = "INSERT INTO twitter_stream_error_log(twitter_sample_stream, error_reported, notes) VALUES(%s, %s, %s)"
		cur.execute(sql, (1, str(sys.exc_info()[1]), "Error: "+str(sys.exc_info()[0])))

		time.sleep(30)
		continue
