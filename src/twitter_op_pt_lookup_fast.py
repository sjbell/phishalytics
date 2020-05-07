import sys
import time
import json
import urllib
from urlparse import urlparse;
import MySQLdb as mdb
import MySQLdb.cursors
from gglsbl4 import SafeBrowsingList
from gglsbl4.protocol import URL
from difflib import SequenceMatcher
from include_stuff import progress_bar # used to display progress bar on terminal

with open('config.json') as data_file:    
	config = json.load(data_file)

def formatURL(url, permusation=False):
	url = url.encode('utf8')
	#url = url.rstrip('/')
	#url = url.encode('utf8')
	#url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
	#url = urlparse(url)[1]
	url_class = URL(url)
	con_url = url_class.canonical
	return con_url

def URLPermutations(url):
	url_class = URL(url)
	urls = []
	for url_variant in url_class.url_permutations(url):
		urls.append(url_variant)
		#print url_variant
	return urls

def importRecentTwitterURLs(limit):
	cursor = con.cursor()
	print "importing most recently tweeted urls..."
	cursor.execute("SELECT url,tweet_id FROM tweet_urls_5 ORDER BY id DESC limit "+str(limit))
	row = cursor.fetchone()
	printCounter=0
	counter = 0
	twitter_urls_dict = {}
	while row is not None:
		formatted_url = formatURL(row[0])
		tweet_id = row[1]
		tweet_ids = {}
		if formatted_url not in twitter_urls_dict:
			#twitter_urls_dict[url] = [str(tweet_id),]
			tweet_ids[tweet_id] = None
			twitter_urls_dict[formatted_url] = tweet_ids
			#twitter_urls_dict[url] = url
			#print "not in dict: ", twitter_urls_dict[url]
			#print type(twitter_urls_dict[url])
		elif formatted_url in twitter_urls_dict:
			#print "in dict: url: "+url+", ",twitter_urls_dict[url]
			#print type(twitter_urls_dict[url])
			tweet_ids = twitter_urls_dict[formatted_url]
			if tweet_id not in tweet_ids:
				tweet_ids[tweet_id] = None
				twitter_urls_dict[formatted_url] = tweet_ids
			#print tweet_ids
		else:
			print "UNKNOWN: ",formatted_url
			exit()
			
		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, limit, '%s of %s' % (counter, limit))
			printCounter = 0
		row = cursor.fetchone()	

	cursor.close()
	print "num unique urls: ",len(twitter_urls_dict)
	return twitter_urls_dict
	
def importRedirectionChain(limit):
	cursor = con.cursor()
	#print "starting at "+str(start)+", batch size "+str(batch_size)
	print "importing redirection chain from most recent tweets..."
	#cursor.execute("SELECT redirection_chain,id FROM tweets_3 LIMIT "+str(start)+", "+str(batch_size)+" ")
	cursor.execute("SELECT redirection_chain,id FROM tweets_5 ORDER BY id DESC limit "+str(limit))
	row = cursor.fetchone()
	printCounter=0
	counter = 0
	twitter_urls_dict = {}
	while row is not None:
		tweet_id = row[1]
		if row[0] is not None:
			urls = row[0].split(" -> ")
			for url in urls:
				formatted_url = formatURL(url)
				
				tweet_ids = {}
				if formatted_url not in twitter_urls_dict:
					#twitter_urls_dict[url] = [str(tweet_id),]
					tweet_ids[tweet_id] = None
					twitter_urls_dict[formatted_url] = tweet_ids
					#twitter_urls_dict[url] = url
					#print "not in dict: ", twitter_urls_dict[url]
					#print type(twitter_urls_dict[url])
				elif formatted_url in twitter_urls_dict:
					#print "in dict: url: "+url+", ",twitter_urls_dict[url]
					#print type(twitter_urls_dict[url])
					tweet_ids = twitter_urls_dict[formatted_url]
					if tweet_id not in tweet_ids:
						tweet_ids[tweet_id] = None
						twitter_urls_dict[formatted_url] = tweet_ids
					#print tweet_ids
				else:
					print "UNKNOWN: ",formatted_url
					exit()
			
		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, limit, '%s of %s' % (counter, limit))
			printCounter = 0
		row = cursor.fetchone()	

	cursor.close()
	print "num unique urls: ",len(twitter_urls_dict)
	return twitter_urls_dict

def importPhishTankURLs():
	cursor = con.cursor()
	#cursor.execute("SELECT url FROM phish_tank_urls LIMIT "+str(start)+", "+str(batch_size)+" ")
	cursor.execute("SELECT url FROM phish_tank_urls_5 ")
	row = cursor.fetchone()
	pt_urls_dict = {}
	printCounter=0
	counter = 0
	while row is not None:
		url = row[0]
		formatted_url = formatURL(url)
		pt_urls_dict[formatted_url] = None
		
		counter += 1
		printCounter += 1
		'''if (printCounter == 1000):
			progress_bar(counter, num_pt_urls, '%s of %s' % (counter, num_pt_urls))
			printCounter = 0'''
		row = cursor.fetchone()	

	cursor.close()
	print "pt_urls_dict len: ",len(pt_urls_dict)
	return pt_urls_dict

def importOpenPhishURLs():
	cursor = con.cursor()
	#cursor.execute("SELECT url FROM phish_tank_urls LIMIT "+str(start)+", "+str(batch_size)+" ")
	cursor.execute("SELECT url FROM open_phish_urls_5 ")
	row = cursor.fetchone()
	op_urls_dict = {}
	printCounter=0
	counter = 0
	while row is not None:
		url = row[0]
		formatted_url = formatURL(url)
		op_urls_dict[formatted_url] = None
		
		counter += 1
		printCounter += 1
		'''if (printCounter == 1000):
			progress_bar(counter, num_pt_urls, '%s of %s' % (counter, num_pt_urls))
			printCounter = 0'''
		row = cursor.fetchone()	

	cursor.close()
	print "op_urls_dict len: ",len(op_urls_dict)
	return op_urls_dict
   
def URLLookup(twitter_urls, phishing_urls, blacklist):
	counter = 0
	match_counter = 0
	netloc_counter = 0
	printCounter = 0
	num_urls = len(twitter_urls)
	for url in twitter_urls:
		if url in phishing_urls:
			match_counter += 1
			print url
			logPhishingURL(url, 5, twitter_urls[url], blacklist)
			markTweetsPhishy(url, twitter_urls[url])
		url_permutations = URLPermutations(url)
		for url_p in url_permutations:
			if url_p in phishing_urls:
				match_counter += 1
				print url_p
				logPhishingURL(url, 5, twitter_urls[url_p], blacklist)
				markTweetsPhishy(url, twitter_urls[url])
			#if saveNetLoc(url):
			#	netloc_counter += 1;
		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, num_urls, '%s of %s ' % (counter, num_urls))
			printCounter = 0

	return (match_counter,netloc_counter)

# mark each tweet as phishing in tweets_2
def markTweetsPhishy(url, tweets):
	cur = con.cursor()
	#print "marking as phishing: ", url
	#print tweets
	for tweet_id in tweets:
		#print "marking tweet id as phishing: ",tweet_id
		cur.execute("UPDATE tweets_5 SET phishing = '1' WHERE id = '"+str(tweet_id)+"'")
		con.commit()

		cur.execute("UPDATE tweets_5 SET date_first_marked_phishing = NOW() WHERE id = '"+str(tweet_id)+"' AND date_first_marked_phishing is NULL")
		con.commit()

		#cursor.execute("UPDATE tweet_urls_3 SET social_engineering = 1 WHERE tweet_id = '"+str(tweet_id)+"' AND social_engineering is NULL")
		#con.commit()
	cur.close()
	
def checkSpamURLExists(url):
	cur = con.cursor()
	url = url[0:1000] #limit string to 1,000 characters as per database
	cur.execute("SELECT id,url FROM spam_urls_5 WHERE url = %s", (url, ))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone()
	return result
	cur.close()

def checkSpamURLTweetIDExists(tweet_id, spam_url_id):
	cur = con.cursor()
	cur.execute("SELECT id FROM spam_urls_tweet_ids_5 WHERE tweet_id = %s AND spam_url_id = %s", (tweet_id, spam_url_id))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone()
	return result
	cur.close()

def logPhishingURL(url,source,tweets, blacklist):
	cur = con.cursor()
	url = url[0:500]

	cur = con.cursor()
	sql = "INSERT INTO twitter_gsb_phishing_url_matches_5(url,blacklist_source) VALUES(%s, %s)"
	cur.execute(sql, (url,source))

	spam_url_id = checkSpamURLExists(url)
	if not spam_url_id:
		sql = "INSERT IGNORE INTO spam_urls_5(url,"+blacklist+") VALUES(%s, %s)"
		cur.execute(sql, (url,1))
		#spam_url_id = cur.lastrowid
	else:
		sql = "INSERT spam_urls_timestamp_5(spam_url_id) VALUES(%s)"
		cur.execute(sql, (spam_url_id,))
		
	spam_url_id = checkSpamURLExists(url)
	for tweet_id in tweets:
		exists = checkSpamURLTweetIDExists(tweet_id, spam_url_id)
		if not exists:
			sql = "INSERT INTO spam_urls_tweet_ids_5(spam_url_id, tweet_id) VALUES(%s, %s)"
			cur.execute(sql, (spam_url_id, tweet_id))		
	
	cur.close()	


#process in batches of size batch_size

while True:
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)

		mainStart = time.time()

		'''countTwitterStartTime = time.time()
		print "Counting total number of tweets in db..."
		num_twitter_urls = countTweets()
		num_twitter_urls = 190175152
		print "Twitter URLs: {:,}".format(num_twitter_urls)
		countTwitterEndTime = time.time()
		print "time taken to count twitter URLs: {0:.0f}".format(countTwitterEndTime-countTwitterEndTime)+" secs ({0:.0f}".format((countTwitterStartTime-countTwitterEndTime)/60)+" mins)"
		'''
		total_phishing = 0
		total_netloc = 0

		pt_urls = importPhishTankURLs()
		op_urls = importOpenPhishURLs()

		lookupStartTime = time.time()
		print "starting lookup..."
		urls1 = importRedirectionChain(3000000)
		urls2 = importRecentTwitterURLs(3000000)

		#urls = urls1 + urls2
		#urls = dict(urls1.items() + urls2.items())
		#print "total urls to check:",len(urls)

		#pt_results = URLSimilarLookup(urls, pt_urls)
		#op_results = URLSimilarLookup(urls, op_urls)

		pt_results = URLLookup(urls1, pt_urls, "PT")
		pt_results = URLLookup(urls2, pt_urls, "PT")

		op_results = URLLookup(urls2, op_urls, "OP")
		op_results = URLLookup(urls2, op_urls, "OP")

		total_phishing += pt_results[0]
		total_phishing += op_results[0]

		lookupEnd = time.time()
		print "time taken to complete batch: {0:.0f}".format(lookupEnd-lookupStartTime)+" secs ({0:.0f}".format((lookupEnd-lookupStartTime)/60)+" mins)"

		mainEnd = time.time()
		print "time taken to complete whole script: {0:.0f}".format(mainEnd-mainStart)+" secs ({0:.0f}".format((mainEnd-mainStart)/60)+" mins)"
		print "total matches:",total_phishing

		con.close()
		print "main loop complete, starting again in 90 secs..."
		time.sleep(90)
		#for url in urls:
		#	print url
	
	except:
		print "We have an error:", sys.exc_info()[1]
		print "waiting 90 secs"
		time.sleep(90)
