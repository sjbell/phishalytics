import time
import sys
import urllib
import urllib2
import hashlib
import MySQLdb as mdb
import MySQLdb.cursors
import sqlite3
import datetime
import math
import json
from socket import error as SocketError
import errno

from sqlite3 import IntegrityError
from gglsbl3 import SafeBrowsingList

with open('config.json') as data_file:    
	config = json.load(data_file)

# used to display progress bar on terminal
def progress_bar(count, total, suffix=''):
	bar_len = 10
	filled_len = int(round(bar_len * count / float(total)))

	percents = round(100.0 * count / float(total), 1)
	bar = '#' * filled_len + '-' * (bar_len - filled_len)

	sys.stdout.write('\r[%s] %s%s (%s)' % (bar, percents, '%', suffix))
	sys.stdout.flush()
	if percents == 100:
		print ""

# convert bytes to MB, GB etc
def convertSize(size):
   if (size == 0):
	   return '0B'
   size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = round(size/p,2)
   return '%s %s' % (s,size_name[i])

# count number of twitter URLs
def countTwitterURLs():
	cur = con.cursor()
	cur.execute("SELECT count(*) FROM tweet_urls_4")
	row = cur.fetchone()
	while row is not None:
		twitter_urls_count = row[0]
		row = cur.fetchone()
	cur.close()
	return twitter_urls_count

# import URLs into dict + list from MySQL db:
def importTwitterURLs(start, batch_size):
	print "batch start: "+str(start)+" size: "+str(batch_size)
	cur = con.cursor()
	#cur.execute('SELECT url FROM tweet_urls LIMIT 500000')
	cur.execute("SELECT url,tweet_id FROM tweet_urls_4 LIMIT "+str(start)+", "+str(batch_size)+" ")
	row = cur.fetchone()
	twitter_urls_dict = {}
	twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		url = row[0].rstrip('/')
		url = row[0]
		url = url.encode('utf8')
		url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
		tweet_id = row[1]
		#print url
		#print tweet_id
		twitter_urls_list.append(url)
		tweet_ids = {}
		if url not in twitter_urls_dict:
			#twitter_urls_dict[url] = [str(tweet_id),]
			tweet_ids[tweet_id] = None
			twitter_urls_dict[url] = tweet_ids
			#twitter_urls_dict[url] = url
			#print "not in dict: ", twitter_urls_dict[url]
			#print type(twitter_urls_dict[url])
		elif url in twitter_urls_dict:
			#print "in dict: url: "+url+", ",twitter_urls_dict[url]
			#print type(twitter_urls_dict[url])
			tweet_ids = twitter_urls_dict[url]
			if tweet_id not in tweet_ids:
				tweet_ids[tweet_id] = None
				twitter_urls_dict[url] = tweet_ids
			#print tweet_ids
		else:
			print "UNKNOWN: ",url
			exit()

		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, batch_size, '%s of %s' % (counter, batch_size))
			printCounter = 0
		row = cur.fetchone()
	cur.close()

	#print "twitter_urls_list len: ",len(twitter_urls_list)
	print "twitter_urls_dict len: ",len(twitter_urls_dict)
	print "twitter_urls_list len: ",len(twitter_urls_list)
	return twitter_urls_dict

# produce dictionary of all URLs and their list of hash prefixes
def computeURLHashes(twitter_urls):
	twitter_urls_hashes_dict = {}
	num_urls = len(twitter_urls_dict)
	counter = 0
	printCounter = 0
	for url in twitter_urls:
		if url not in twitter_urls_hashes_dict:
			url = url.encode('utf8')
			url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
			url_hashes = sbl.get_hash(url)
			hash_list = []
			#hash_prefix_list = []
			for h in url_hashes:
				#hash_prefix = sqlite3.Binary(h[0:4])
				#hash_prefix = str(hash_prefix).encode('hex')
				hash_list.append(h)
				#hash_prefix_list.append(hash_prefix)
				
			#twitter_urls_hashes_dict[url] = (url,hash_list,hash_prefix_list)	
			twitter_urls_hashes_dict[url] = (hash_list)
		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, num_urls, '%s of %s' % (counter, num_urls))
			printCounter = 0
	return twitter_urls_hashes_dict
		
def importGSBHashPrefixes():
	gsb_hash_prefixes = sbl.get_all_hash_prefixes()
	return gsb_hash_prefixes

def convertGSBToDict(gsb_urls):
	gsb_urls_dict = {}
	for url_hash in gsb_urls:
		#url_hash = sqlite3.Binary(url_hash[0])
		#url_hash = bytes(url_hash[0])
		url_hash = str(url_hash[0]).encode('hex')
		#print url_hash
		#for url_prefix in twitter_url_hash_prefixes_list:
		#    if url_prefix == url_hash:
		#        print "match!"
		if url_hash not in gsb_urls_dict:
			gsb_urls_dict[url_hash] = url_hash

	#if url_hash not in twitter_url_hash_prefixes_dict:
	#    url = twitter_url_hash_prefixes_dict[url_hash]
	return gsb_urls_dict

def URLLookup_v2(twitter_urls, gsb_urls, twitter_urls_dict):
	# twitter_urls = (hash_list)
	# twitter_urls_dict = (tweet_ids)
	counter = 0
	hash_prefix_counter = 0
	printCounter = 0
	num_urls = len(twitter_urls)
	malware_count = 0
	phish_count = 0
	phishing_matches = {}
	for url in twitter_urls:
		j = 0
		url_hashes = twitter_urls[url]
		#url_hash_prefixes = url_data[2]
		#url_hashes = url_data[2]
		#for hash_prefix in url_hash_prefixes:
		for url_hash in url_hashes:
			hash_prefix = sqlite3.Binary(url_hash[0:4])
			hash_prefix = str(hash_prefix).encode('hex')
			if hash_prefix in gsb_urls:
				hash_prefix_counter += 1
				try:
					#print "match!"
					gsblookup = sbl.lookup_hash(url_hash)
					#gsblookup = sbl.lookup_url(url)
					if gsblookup:
						for i in gsblookup:
							#print i
							if i == "goog-malware-shavar":
								#print "malware"
								#sys.stdout.write('\r-')
								#sys.stdout.flush()
								malware_count += 1
								logMalwareURL(url, 3, twitter_urls_dict[url])
								markTweetsMalware(url, twitter_urls_dict[url])
							if i == "googpub-phish-shavar":
								#print "phishing ",url_data[0]
								phish_count += 1
								logPhishingURL(url, 3, twitter_urls_dict[url])
								markTweetsPhishy(url, twitter_urls_dict[url])
								phishing_matches[url] = (url_hash)
				except (RuntimeError, IntegrityError, urllib2.HTTPError, urllib2.URLError, SocketError) as e:
					print e
					print url
					log("error: "+str(e.message)+"\nURL: "+url+"\n")
			j+=1
		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			#progress_bar(counter, num_urls, '%s of %s (hash_prefix_counter: %s)' % (counter, num_urls, hash_prefix_counter))
			progress_bar(counter, num_urls, '%s of %s' % (counter, num_urls))
			printCounter = 0

	return (phish_count, malware_count, phishing_matches)

# mark each tweet as phishing in tweets_2
def markTweetsPhishy(url, tweets):
	cur = con.cursor()
	#print "marking as phishing: ", url
	#print tweets
	for tweet_id in tweets:
		#print "marking tweet id as phishing: ",tweet_id
		cur.execute("UPDATE tweets_4 SET phishing = '1' WHERE id = '"+str(tweet_id)+"'")
		con.commit()
		
		cur.execute("UPDATE tweets_4 SET date_first_marked_phishing = NOW() WHERE id = '"+str(tweet_id)+"' AND date_first_marked_phishing is NULL")
		con.commit()
		
		#cur.execute("UPDATE tweet_urls_3 SET social_engineering = 1 WHERE tweet_id = '"+str(tweet_id)+"' AND social_engineering is NULL")
		#con.commit()
	cur.close()
		
# mark each tweet as malicious in tweets_2
def markTweetsMalware(url, tweets):
	cur = con.cursor()
	for tweet_id in tweets:
		#print "marking tweet id as phishing: ",tweet_id
		cur.execute("UPDATE tweets_4 SET malware = '1' WHERE id = '"+str(tweet_id)+"'")
		con.commit()

		cur.execute("UPDATE tweets_4 SET date_first_marked_malicious = NOW() WHERE id = '"+str(tweet_id)+"' AND date_first_marked_phishing is NULL")
		con.commit()

	cur.close()

def checkSpamURLExists(url):
	cur = con.cursor()
	url = url[0:1000] #limit string to 1,000 characters as per database
	cur.execute("SELECT id,url FROM spam_urls_4 WHERE url = %s", (url, ))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone() 
	cur.close()
	return result

def checkSpamURLTweetIDExists(tweet_id, spam_url_id):
	cur = con.cursor()
	cur.execute("SELECT id FROM spam_urls_tweet_ids_4 WHERE tweet_id = %s AND spam_url_id = %s", (tweet_id, spam_url_id))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone()
	return result
	cur.close()

def logPhishingURL(url,source,tweets):
	cur = con.cursor()
	url = url[0:500]
	sql = "INSERT INTO twitter_gsb_phishing_url_matches_4(url,blacklist_source) VALUES(%s, %s)"
	cur.execute(sql, (url,source))
	twitter_gsb_phishing_url_matches_4_id = cur.lastrowid

	for tweet_id in tweets:
		sql = "INSERT INTO twitter_gsb_phishing_url_tweet_ids_4(twitter_gsb_phishing_url_id, tweet_id) VALUES(%s, %s)"
		cur.execute(sql, (twitter_gsb_phishing_url_matches_4_id, tweet_id))
		con.commit()
		
	spam_url_id = checkSpamURLExists(url)
	if not spam_url_id:
		sql = "INSERT IGNORE INTO spam_urls_4(url,GSB_phish) VALUES(%s, %s)"
		cur.execute(sql, (url,1))
		spam_url_id = cur.lastrowid
	else:
		sql = "INSERT spam_urls_timestamp_4(spam_url_id) VALUES(%s)"
		cur.execute(sql, (spam_url_id,))
		spam_url_id = cur.lastrowid
		
	spam_url_id = checkSpamURLExists(url)
	for tweet_id in tweets:
		exists = checkSpamURLTweetIDExists(tweet_id, spam_url_id)
		if not exists:
			sql = "INSERT INTO spam_urls_tweet_ids_4(spam_url_id, tweet_id) VALUES(%s, %s)"
			cur.execute(sql, (spam_url_id, tweet_id))	

	cur.close()

def logMalwareURL(url,source,tweets):
	cur = con.cursor()
	sql = "INSERT INTO twitter_gsb_malware_url_matches_4(url,blacklist_source) VALUES(%s, %s)"
	cur.execute(sql, (url,source))
	twitter_gsb_malware_url_matches_4_id = cur.lastrowid

	for tweet_id in tweets:
		sql = "INSERT INTO twitter_gsb_malware_url_tweet_ids_4(twitter_gsb_malware_url_id, tweet_id) VALUES(%s, %s)"
		cur.execute(sql, (twitter_gsb_malware_url_matches_4_id, tweet_id))
		con.commit()

	spam_url_id = checkSpamURLExists(url)
	if not spam_url_id:
		sql = "INSERT IGNORE INTO spam_urls_4(url,GSB_malware) VALUES(%s, %s)"
		cur.execute(sql, (url,1))
		spam_url_id = cur.lastrowid
	else:
		sql = "INSERT spam_urls_timestamp_4(spam_url_id) VALUES(%s)"
		cur.execute(sql, (spam_url_id,))
		
	spam_url_id = checkSpamURLExists(url)
	for tweet_id in tweets:
		exists = checkSpamURLTweetIDExists(tweet_id, spam_url_id)
		if not exists:
			sql = "INSERT INTO spam_urls_tweet_ids_4(spam_url_id, tweet_id) VALUES(%s, %s)"
			cur.execute(sql, (spam_url_id, tweet_id))

	cur.close()

def getTS():
  return ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))

def log(text):
	with open("tpl_output", "a") as logfile:
 		logfile.write(str(getTS())+": "+text)

# begin main while loop
while True:
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_4'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		con.autocommit(True)

		mainStart = time.time()		

		#update GSB dataset
		print "Updating local GSB dataset..."

		try:
			sbl.update_hash_prefix_cache()
		except (RuntimeError, IntegrityError, urllib2.HTTPError, urllib2.URLError, SocketError) as e:
			print e
			log("error: "+str(e.message)+"\nTrying to update GSB sbl.update_hash_prefix_cache()\n")
			print "waiting 90 seconds..."
			time.sleep(90)
		
		# count total number of twitter urls + print
		print "Counting total number of Twitter URLs in db..."
		num_twitter_urls = countTwitterURLs()
		print "Twitter URLs: {:,}".format(num_twitter_urls)


		#process in batches of size batch_size
		batch_size = 1000000
		batch_start = 0
		num_of_batches = int(math.ceil(float(num_twitter_urls)/float(batch_size)))
		total_phishing = 0
		total_malware = 0

		print "number of batches to run: ", num_of_batches

		for batch_number in xrange(num_of_batches):
			batchStartTime = time.time()
			print "batch " + str(batch_number) + " of " + str(num_of_batches)

			# import twitter urls
			print "\nimporting Twitter URLs..."
			start = time.time()
			twitter_urls_dict = importTwitterURLs(batch_start, batch_size)
			num_unique_twitter_urls = len(twitter_urls_dict)
			print "Size of twitter dictionary (bytes): ", convertSize(sys.getsizeof(twitter_urls_dict))
			end = time.time()
			print "time taken to import Twitter URLs: {0:.2f}".format(end-start)+" seconds ({0:.2f}".format((end-start)/60)+" minutes)"
			#print twitter_urls_dict.popitem()
			batch_start += batch_size


			# compute URL hashes
			print "\ncomputing URL hashes..."
			start = time.time()
			twitter_urls_hashes_dict = computeURLHashes(twitter_urls_dict)
			end = time.time()
			print "time taken to compute URL hashes: {0:.2f}".format(end-start)+" seconds ({0:.2f}".format((end-start)/60)+" minutes)"


			# import GSB urls + convert to dict
			print "\nimporting GSB hash prefixes + converting to dict"
			start = time.time()
			#gsb_hashes_list = importGSBHashes()
			gsb_hashes_list = importGSBHashPrefixes()
			print "GSB urls: ",len(gsb_hashes_list)
			gsb_hashes_dict = convertGSBToDict(gsb_hashes_list)
			print "gsb_urls_dict length (unique GSB): ",len(gsb_hashes_dict)
			end = time.time()
			print "time taken to import GSB URLs: {0:.2f}".format(end-start)+" seconds ({0:.2f}".format((end-start)/60)+" minutes)"

			#quit()

			# GSB lookup_v2
			print "\nlooking up Twitter URLs in GSB..."
			start = time.time()
			url_lookup = URLLookup_v2(twitter_urls_hashes_dict, gsb_hashes_dict, twitter_urls_dict)
			end = time.time()
			print "time taken to lookup GSB URLs (dict): {0:.2f}".format(end-start)+" seconds ({0:.2f}".format((end-start)/60)+" minutes)"
			print "pishing matches: ",url_lookup[0]
			total_phishing += url_lookup[0]
			print "malware matches: ",url_lookup[1]
			total_malware += url_lookup[1]
			print "unique phishing matches: ", len(url_lookup[2])

			batchEnd = time.time()
			print "time taken to complete batch: {0:.2f}".format(batchEnd-batchStartTime)+" seconds ({0:.2f}".format((batchEnd-batchStartTime)/60)+" minutes)"

		mainEnd = time.time()
		print "time taken to complete whole script: {0:.2f}".format(mainEnd-mainStart)+" seconds ({0:.2f}".format((mainEnd-mainStart)/60)+" minutes)"
		log(
			'number of twitter URLs:' + str(num_twitter_urls)
			+ '\nnumber of batches: ' + str(num_of_batches)
			+ '\ntime taken to complete whole script: ({0:.2f}'.format((mainEnd-mainStart)/60)+' minutes)'
			+ '\nnumber of social_engineering URLs: ' + str(total_phishing)
			+ '\nnumber of malware URLs: ' + str(total_malware)
			+ '\n----------\n\n'
		)

		runTime = (mainEnd-mainStart)
		if runTime < 3600:
			#log("waiting "+str((3600-runTime)/60)+" minutes............................................")
			print "waiting {0:.2f}".format((3600-runTime)/60)+" minutes..."
			print datetime.datetime.now()
			time.sleep(3600-runTime)
		else:
			#log("waiting 0 minutes............................................")
			print "waiting 0 minutes..."
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
		sendAdminAlert("Error in "+script_file_name, 
		"Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string))

		print "waiting 90 seconds"
		time.sleep(90)

