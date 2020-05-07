import sys
import tweepy
import time
import MySQLdb as mdb
import MySQLdb.cursors
import json
from include_stuff import progress_bar # used to display progress bar on terminal
import traceback

from datetime import datetime, timedelta
from dateutil import tz
#import datetime

with open('config.json') as data_file:    
	config = json.load(data_file)


def tweepyError(e, location, search_term=None):
	print e
	if search_term:
		print "search term:", search_term

	if "code" in e.message[0]:
		error_code = e.message[0]['code']
		if isinstance(error_code, ( int, long ) ):
			if error_code == 88:
				print time.strftime("%c")+" Rate limit (in "+location+")\nWait 90 secs..."
				time.sleep(90)
			elif e.message[0]['code'] == 130:
				print time.strftime("%c")+" Twitter over capacity (in "+location+"). Wait 90 secs..."
				time.sleep(90)
			else:
				from send_email import sendAdminAlert
				import os
				script_file_name = os.path.basename(__file__)
				error_message = "Unrecognised (as in not set in conditional) error code in functon tweepyError(). Error code: "+str(error_code)
				sendAdminAlert("Error in "+script_file_name,
					"Python script: "+script_file_name+"\nError reported: "+ str(error_message))
				exit()
		else:
			from send_email import sendAdminAlert
			import os
			script_file_name = os.path.basename(__file__)
			error_message = 'Conditional fail: isinstance(error_code, ( int, long ) )'
			sendAdminAlert("Error in "+script_file_name,
				"Python script: "+script_file_name+"\nError reported: "+ str(error_message))
			exit()

# get spam urls less than 10 days old
def getSpamURLs():
	cur = con.cursor()
	print "importing spam urls from db less than 10 days old, newest first... "
	# for testing, just use spam_urls detected today. For real system select spam_urls from past 10 days
	#cursor.execute("SELECT url,id,date_added FROM spam_urls_test WHERE date_added >= DATE(NOW()) - INTERVAL 10 DAY AND date_first_tweeted IS NULL")
	cur.execute("SELECT url,id,date_added FROM spam_urls_5 WHERE date_added >= DATE_SUB(NOW(),INTERVAL 10 DAY) AND date_first_tweeted IS NULL ORDER BY id DESC")
	#cursor.execute("SELECT url,id,date_added FROM spam_urls_test WHERE DATE(date_added) >= DATE(NOW()) AND date_first_tweeted IS NULL")
	
	row = cur.fetchone()
	result = []
	while row is not None:
		result.append(row)
		row = cur.fetchone() 
	return result
	cur.close()

def twitterSearch(search_term):
	search_term = search_term[0:100] # if URL is too long
	match = False
	loop = True
	while loop:
		try:
			finished = False
			final_loop = False
			date_var = datetime.today() + timedelta(days=1)
			counter = 0
			while not finished:
				search_results = api.search(q=search_term, result_type="recent", count=100, until=date_var.strftime("%Y-%m-%d"))
				print "using date:",date_var.strftime("%Y-%m-%d")
				num_results = len(search_results)
				print "counter:",counter
				
				if final_loop:
					finished = True
				else:
					if num_results == 100:
						date_var = date_var - timedelta(days=1)
						counter += 1
					elif (num_results == 0) and (counter > 0):
						print "condition met"
						date_var = date_var + timedelta(days=1)
						final_loop = True
					else:
						finished = True
				print "num results:",num_results
			
			# if match, ser result variable
			if len(search_results) > 0:
				from_zone = tz.gettz('UTC')
				to_zone = tz.gettz('Europe/London')
				utc_date = search_results[-1].created_at
				#utc = datetime.strptime(utc_date, '%Y-%m-%d %H:%M:%S')
				utc = utc_date.replace(tzinfo=from_zone)
				lon_time = utc.astimezone(to_zone)
				result = lon_time.replace(tzinfo=None) # return results in local timezone
				#result = utc_date # return results in original timezone

				# check url was in tweet
				for e in search_results[-1].entities['urls']:
					if search_term.strip("/") == e['expanded_url'].strip("/"):
						match = True
				if not match:
					print "Domain mismatch"
					print search_term
					for s in search_results:
						for e in s.entities['urls']:
							print s.text
							print s.created_at
							print e['expanded_url']
							print ""
					print search_results[-1].entities['urls']
					#exit()
				else:
					print "URL match"

			# no search results matched query, so set result variable to false
			else:
				result = False
			loop = False
		except tweepy.TweepError as e:
			tweepyError(e, "twitterSearch", search_term)
		except:
			print "Error:", sys.exc_info()[1]
			print "wait 90 secs"
			time.sleep(90)

	print twitterRateLimitStatus()
	return (result, match)

def twitterRateLimitStatus():
	loop = True
	while loop:
		try:
			rate_limit = api.rate_limit_status()
			print rate_limit
			loop = False
		except tweepy.TweepError as e:
			print "error here..."
			tweepyError(e, "twitterRateLimitStatus")

	return "Twitter search API rate limit: "+str(rate_limit['resources']['search']['/search/tweets']['limit']-rate_limit['resources']['search']['/search/tweets']['remaining'])+"/"+str(rate_limit['resources']['search']['/search/tweets']['limit'])+" (per 15 min)"

def updateSpamURL(url, date):
	cur = con.cursor()
	print "Adding to spam_urls_5:",date
	cur.execute("UPDATE spam_urls_5 SET date_first_tweeted = %s WHERE url = %s AND date_first_tweeted IS NULL", (date, url))
	cur.close()

run = True
while run:
	try:

		auth = tweepy.OAuthHandler(config['twitter-api']['consumer_key'], config['twitter-api']['consumer_secret'])
		auth.set_access_token(config['twitter-api']['access_token'], config['twitter-api']['access_token_secret'])
		api = tweepy.API(auth)

		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		#cursor = con.cursor()
		con.autocommit(True)

		print "\n\nstarting new loop..."
		time.sleep(10)

		print twitterRateLimitStatus()

		spam_urls = getSpamURLs()

		print "num URLs to check: ",len(spam_urls)

		match_counter = 0
		for data in spam_urls:
			url = data[0]
			print url
			tweet_data = twitterSearch(url)
			if tweet_data[0]:
				match_counter += 1
				updateSpamURL(url, tweet_data[0])

		print "search complete"
		print "found "+str(match_counter)+" of "+str(len(spam_urls))
		print datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		con.close()
	except:

		print "traceback:"
		traceback.print_exc()

		print "Error:", sys.exc_info()[1]
		import os
		import sys
		import traceback
		from send_email import sendAdminAlert
		script_file_name = os.path.basename(__file__)
		error_string = ""
		for frame in traceback.extract_tb(sys.exc_info()[2]):
			fname,lineno,fn,text = frame
			error_string += "\nError in %s on line %d" % (fname, lineno)
		sendAdminAlert("Error in "+script_file_name, 
		"Python script: "+script_file_name+"\nError reported: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string))

		print "wait 90 secs"
		time.sleep(90)
