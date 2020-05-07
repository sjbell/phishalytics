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
import errno
import gc
from include_stuff import progress_bar # used to display progress bar on terminal

from socket import error as SocketError
from sqlite3 import IntegrityError
from gglsbl import SafeBrowsingList
from gglsbl.protocol import URL

with open('config.json') as data_file:    
	config = json.load(data_file)

# convert bytes to MB, GB etc
def convertSize(size):
   if (size == 0):
	   return '0B'
   size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = round(size/p,2)
   return '%s %s' % (s,size_name[i])

def formatURL(url, permutation=False):
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

'''# count number of twitter URLs
def countTwitterURLs():
	cur = con.cursor()
	cur.execute("SELECT count(*) FROM tweet_urls_4 ")
	 
	row = cur.fetchone()
	while row is not None:
		twitter_urls_count = row[0]
		row = cur.fetchone()
	return twitter_urls_count
	cur.close()'''

def getLatestTweetURLid():
	cur = con.cursor()
	tweet_url_id = None
	cur.execute('SELECT id,url,tweet_id FROM tweet_urls_5b ORDER BY id DESC LIMIT 1')
	row = cur.fetchone()
	while row is not None:
		tweet_url_id = row[0]
		row = cur.fetchone()
	cur.close()
	return tweet_url_id

# import URLs into dict + list from MySQL db:
def importRecentTwitterURLs(limit, from_id=None, to_id=None):
	cur = con.cursor()
	if from_id is not None and to_id is not None:
		print "importing by range ("+str(from_id)+" to "+str(to_id)+")"
		cur.execute('SELECT url,tweet_id FROM tweet_urls_5b WHERE id >= '+str(from_id)+' AND id <= '+str(to_id))
	else:
		print "importing recent by limit ("+str(limit)+")"
		cur.execute('SELECT url,tweet_id FROM tweet_urls_5b ORDER BY id DESC  LIMIT '+str(limit))

	row = cur.fetchone()
	twitter_urls_dict = {}
	#twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		#url = row[0].rstrip('/')
		formatted_url = formatURL(row[0])
		#url = row[0]
		#url = url.encode('utf8')
		#url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
		tweet_id = row[1]
		#print url
		#print tweet_id
		#twitter_urls_list.append(url)
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
		row = cur.fetchone()	

	#print "twitter_urls_list len: ",len(twitter_urls_list)
	print "twitter_urls_dict len: ",len(twitter_urls_dict)
	cur.close()
	return twitter_urls_dict

def importRedirectionChainURLs(limit):
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
			for url in urls[1:]: # remove first url in this chain as it will have already been checked by importRecentTwitterURLs
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

# produce dictionary of URL permutations from dictionary of URL permutations
def produceURLPermutations(url_dict):
	print "producing URL permutations..."
	url_permutations_dict = {}
	counter = 0
	printCounter = 0
	for url in url_dict:
		#print url
		url_permutations = URLPermutations(url)
		for url_p in url_permutations:
			#print url_p
			url_permutations_dict[url_p] = False

		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, len(url_dict), '%s of %s' % (counter, len(url_dict)))
			printCounter = 0
	return url_permutations_dict

# produce dictionary of all URLs and their list of hash prefixes
def computeURLHashes(twitter_urls):
	twitter_urls_hashes_dict = {}
	num_urls = len(twitter_urls_dict)
	counter = 0
	printCounter = 0
	for url in twitter_urls:
		if url not in twitter_urls_hashes_dict:
			#url = url.encode('utf8')
			#url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
			#url_hashes = sbl.get_hash(url)
			url_hashes = URL(url).hashes
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
			gsb_urls_dict[url_hash] = 1
		else:
			gsb_urls_dict[url_hash] = gsb_urls_dict[url_hash]+1

	#if url_hash not in twitter_url_hash_prefixes_dict:
	#    url = twitter_url_hash_prefixes_dict[url_hash]
	return gsb_urls_dict

def lookup_gsb_full_hash(full_hash):
	cur = con.cursor()
	cur.execute("SELECT * FROM gsb_full_hash_log_5 WHERE full_hash = %s", (full_hash, ))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone()
	return result==None

def URLLookup_v2(twitter_urls, gsb_url_hash_prefixes, twitter_urls_dict, redirection_chain_url_lookup):
	# twitter_urls = (hash_list)
	# twitter_urls_dict = (tweet_ids)
	counter = 0
	hash_prefix_counter = 0
	hash_prefix_no_collision_counter = 0
	printCounter = 0
	num_urls = len(twitter_urls)
	malware_count = 0
	phish_count = 0
	url_already_checked_ctr = 0
	url_matches_in_gsb = 0
	gsb_lookup_counter = 0
	malware_matches = {}
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
			if hash_prefix in gsb_url_hash_prefixes:
				#print "num hash prefixes:",gsb_url_hash_prefixes[hash_prefix]
				if gsb_url_hash_prefixes[hash_prefix] == 6:
					hash_prefix_no_collision_counter += 1
					
					if(lookup_gsb_full_hash(sqlite3.Binary(url_hash))):
						
						database_lock = True
						while database_lock:
							try:
								gsb_lookup_counter += 1
								gsblookup = sbl.lookup_url(url)
								#gsblookup = sbl.lookup_hash(url_hash)
								#gsblookup = sbl._lookup_hashes(url_hashes)
								if gsblookup:
									url_matches_in_gsb += 1
									cur = con.cursor()
									sql = "INSERT INTO gsb_full_hash_log_5(url, hash_prefix, full_hash) VALUES(%s, %s, %s)"
									cur.execute(sql, (url[0:500], sqlite3.Binary(url_hash[0:4]), sqlite3.Binary(url_hash)))

									for i in gsblookup:
										#print str(i)
										#print type(i)
										#if i == "goog-malware-shavar":
										if str(i) == "MALWARE/ANY_PLATFORM/URL":

											print url
											cur.execute("UPDATE gsb_full_hash_log_5 SET malware = '1' WHERE full_hash = %s",(url_hash,))
											con.commit()
											#print "malware",url
											#sys.stdout.write('\r-')
											#sys.stdout.flush()
											malware_count += 1
											malware_matches[url] = (url_hash)
											logMalwareURL(url, 4, twitter_urls_dict[url], redirection_chain_url_lookup)
											#markTweetsMalware(url, twitter_urls_dict[url])
										#if i == "googpub-phish-shavar":
										if str(i) == "SOCIAL_ENGINEERING/ANY_PLATFORM/URL":
											print url	
											cur.execute("UPDATE gsb_full_hash_log_5 SET social_engineering = '1' WHERE full_hash = %s",(url_hash,))
											con.commit()
											#print "phishing ",url
											phish_count += 1
											logPhishingURL(url, 4, twitter_urls_dict[url], redirection_chain_url_lookup)
											#markTweetsPhishy(url, twitter_urls_dict[url])
											phishing_matches[url] = (url_hash)
								else: # url hash prefix match but full hash not in GSB i.e. different URL. Mark in db so doesn't get checked again
									cur = con.cursor()
									sql = "INSERT INTO gsb_full_hash_log_5(hash_prefix, full_hash, not_in_gsb) VALUES(%s, %s, %s)"
									cur.execute(sql, (sqlite3.Binary(url_hash[0:4]), sqlite3.Binary(url_hash), 1))


								database_lock = False

							except KeyError:
								# 18 Jun 2018, disabling error: 'exceptions.KeyError'>, KeyError('matches',)
								# as appearing every minute or so
								print "Looks like a key error:", sys.exc_info()[1]
								log("certstream-url-checker-v2-phishing_5.txt", "Looks like a key error: "+str(sys.exc_info()[1]))
								print "URL:", url
								time.sleep(5)
								database_lock = False
							except (RuntimeError, IntegrityError, urllib2.HTTPError, urllib2.URLError, SocketError, sqlite3.OperationalError) as e:
								print e
								print url
								log("tpl_fast_v2-output.txt", "error: "+str(e.message)+"\nURL: "+url+"\n")
								print "waiting 5 seconds..."
								time.sleep(5)
								database_lock = False
							except sqlite3.OperationalError:
								print("database locked, waiting 5 seconds...")
								log("tpl_v3.2-output.txt", "gglsbl3 database is locked")
								time.sleep(5)

					else:
						#print "URL already in gsb_full_hash_lookup"
						url_already_checked_ctr += 1
				#else: #hash prefix not unique
					#still log URL anyway, but mark that it's not only URL


				hash_prefix_counter += 1


				#gglsbl_db = "/tmp/gsb_v4.db"
				#sql_db = sqlite3.connect(gglsbl_db)
				#cursor = sql_db.cursor()
				#cursor.execute("SELECT threat_type, platform_type, threat_entry_type from hash_prefix WHERE value = ?",(sqlite3.Binary(url_hash[0:4]),) ) #get all hash prefixes
				#cursor.execute('''SELECT value from full_hash''') #get all full hashes
				#results = cursor.fetchall()
				#for r in results:
				#	print r[0]+" "+r[1]+" "+r[2]
				

				# database_lock = True
				# while database_lock:
				# 	try:
				# 		gsblookup = sbl.lookup_hash(url_hash)
				# 		#gsblookup = sbl._lookup_hashes(url_hashes)
				# 		if gsblookup:
				# 			for i in gsblookup:
				# 				#print str(i)
				# 				#print type(i)
				# 				if i == "goog-malware-shavar":
				# 				#if str(i) == "MALWARE/ANY_PLATFORM/URL":
				# 					#print "malware",url
				# 					#sys.stdout.write('\r-')
				# 					#sys.stdout.flush()
				# 					malware_count += 1
				# 					malware_matches[url] = (url_hash)
				# 					logMalwareURL(url, 4, twitter_urls_dict[url], redirection_chain_url_lookup)
				# 					markTweetsMalware(url, twitter_urls_dict[url])
				# 				if i == "googpub-phish-shavar":
				# 				#if str(i) == "SOCIAL_ENGINEERING/ANY_PLATFORM/URL":
				# 					#print "phishing ",url
				# 					phish_count += 1
				# 					logPhishingURL(url, 4, twitter_urls_dict[url], redirection_chain_url_lookup)
				# 					markTweetsPhishy(url, twitter_urls_dict[url])
				# 					phishing_matches[url] = (url_hash)
				# 		database_lock = False
				# 	except (RuntimeError, IntegrityError, urllib2.HTTPError, urllib2.URLError, SocketError, sqlite3.OperationalError) as e:
				# 		print e
				# 		print url
				# 		log("tpl_fast_v2-output.txt", "error: "+str(e.message)+"\nURL: "+url+"\n")
				# 		print "waiting 5 seconds..."
				# 		time.sleep(5)
				# 		database_lock = False
				# 	except sqlite3.OperationalError:
				# 		print("database locked, waiting 5 seconds...")
				# 		log("tpl_v3.2-output.txt", "gglsbl3 database is locked")
				# 		time.sleep(5)
			j+=1
		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			#progress_bar(counter, num_urls, '%s of %s (hash_prefix_counter: %s)' % (counter, num_urls, hash_prefix_counter))
			progress_bar(counter, num_urls, '%s of %s' % (counter, num_urls))
			printCounter = 0
		#print "num hash prefix matches: ", hash_prefix_counter
	return (phish_count, malware_count, phishing_matches, malware_matches, hash_prefix_counter, hash_prefix_no_collision_counter, url_already_checked_ctr, url_matches_in_gsb, gsb_lookup_counter)

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

# mark each tweet as malicious in tweets_2
def markTweetsMalware(url, tweets):
	cur = con.cursor()
	for tweet_id in tweets:
		#print "marking tweet id as phishing: ",tweet_id
		cur.execute("UPDATE tweets_5 SET malware = '1' WHERE id = '"+str(tweet_id)+"'")
		con.commit()

		cur.execute("UPDATE tweets_5 SET date_first_marked_malicious = NOW() WHERE id = '"+str(tweet_id)+"' AND date_first_marked_malicious is NULL")
		con.commit()
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

def logPhishingURL(url, source, tweets, redirection_chain):
	cur = con.cursor()
	url = url[0:500]

	if redirection_chain: # convert boolean to tinyint for MySQL
		redirection_chain = 1
	else:
		redirection_chain = 0

	cur = con.cursor()
	sql = "INSERT INTO twitter_gsb_phishing_url_matches_5(url, blacklist_source, redirection_chain) VALUES(%s, %s, %s)"
	cur.execute(sql, (url, source, redirection_chain))
	twitter_gsb_phishing_url_matches_5_id = cur.lastrowid

	for tweet_id in tweets:
		sql = "INSERT INTO twitter_gsb_phishing_url_tweet_ids_5(twitter_gsb_phishing_url_id, tweet_id) VALUES(%s, %s)"
		cur.execute(sql, (twitter_gsb_phishing_url_matches_5_id, tweet_id))
		con.commit()

	spam_url_id = checkSpamURLExists(url)
	if not spam_url_id:
		sql = "INSERT IGNORE INTO spam_urls_5(url, GSB_phish, redirection_chain) VALUES(%s, %s, %s)"
		cur.execute(sql, (url, 1, redirection_chain))
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

def logMalwareURL(url, source, tweets, redirection_chain):
	cur = con.cursor()
	url = url[0:1000]

	if redirection_chain: # convert boolean to tinyint for MySQL
		redirection_chain = 1
	else:
		redirection_chain = 0
	
	sql = "INSERT INTO twitter_gsb_malware_url_matches_5(url, blacklist_source, redirection_chain) VALUES(%s, %s, %s)"
	cur.execute(sql, (url, source, redirection_chain))
	twitter_gsb_malware_url_matches_5_id = cur.lastrowid

	for tweet_id in tweets:
		sql = "INSERT INTO twitter_gsb_malware_url_tweet_ids_5(twitter_gsb_malware_url_id, tweet_id) VALUES(%s, %s)"
		cur.execute(sql, (twitter_gsb_malware_url_matches_5_id, tweet_id))
		con.commit()

	spam_url_id = checkSpamURLExists(url)
	if not spam_url_id:
		sql = "INSERT IGNORE INTO spam_urls_5(url, GSB_malware, redirection_chain) VALUES(%s, %s, %s)"
		cur.execute(sql, (url, 1, redirection_chain))
		spam_url_id = cur.lastrowid
	else:
		sql = "INSERT spam_urls_timestamp_5(spam_url_id) VALUES(%s)"
		cur.execute(sql, (spam_url_id,))
		
	for tweet_id in tweets:
		exists = checkSpamURLTweetIDExists(tweet_id, spam_url_id)
		if not exists:
			sql = "INSERT INTO spam_urls_tweet_ids_5(spam_url_id, tweet_id) VALUES(%s, %s)"
			cur.execute(sql, (spam_url_id, tweet_id))

	cur.close()

def getTS():
  return ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))

def log(file, text):
	with open(file, "a") as logfile:
 		logfile.write(str(getTS())+"\n"+text+"\n")

# begin main while loop
while True:
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		#cursor = con.cursor()
		con.autocommit(True)

		sbl = SafeBrowsingList(config['gsb-api']['key'])

		# start timer
		mainStart = time.time()
		num_urls_to_import = 3000000

		# count total number of twitter urls + print
		#print "Counting total number of Twitter URLs in db..."
		#num_twitter_urls = countTwitterURLs()
		#num_twitter_urls = 2000000
		#print "Twitter URLs: {:,}".format(num_twitter_urls)

		total_phishing = 0
		total_malware = 0

		# import twitter urls
		print "import Twitter URLs"
		print "num to import:", num_urls_to_import
		start = time.time()
		latest_tweet_url_id = getLatestTweetURLid()
		from_tweet_urls = latest_tweet_url_id - (3000000*7)
		to_tweet_urls = latest_tweet_url_id - (3000000*6)

		#twitter_urls_dict = importRecentTwitterURLs(num_urls_to_import) # old, removed Thu 7 Feb 2019
		twitter_urls_dict = importRecentTwitterURLs(num_urls_to_import, from_tweet_urls, to_tweet_urls)
		#twitter_urls__permutations_dict = produceURLPermutations(twitter_urls_dict)
		###twitter_urls_redirection_chain_dict = importRedirectionChainURLs(num_urls_to_import)
		#twitter_urls_redirection_chain_permutations_dict = produceURLPermutations(twitter_urls_redirection_chain_dict)

		
		print "Size of twitter URLs dictionary (num): ", len(twitter_urls_dict)
		print "Size of twitter URLs dictionary (bytes): ", convertSize(sys.getsizeof(twitter_urls_dict))
		###print "Size of twitter URLs redirection chain dictionary (num): ", len(twitter_urls_redirection_chain_dict)
		###print "Size of twitter URLs redirection chain dictionary (bytes): ", convertSize(sys.getsizeof(twitter_urls_redirection_chain_dict))
		end = time.time()
		print "time taken to import Twitter URLs: {0:.0f}".format(end-start)+"sec ({0:.0f}".format((end-start)/60)+"mins)"

		# compute URL hashes
		print "\ncomputing URL hashes"
		start = time.time()
		twitter_urls_hashes_dict = computeURLHashes(twitter_urls_dict)
		#twitter_urls_permutations_hashes_dict = computeURLHashes(twitter_urls__permutations_dict)
		###twitter_urls_redirection_chain_hashes_dict = computeURLHashes(twitter_urls_redirection_chain_dict)
		#twitter_urls_redirection_chain_permutations_hashes_dict = computeURLHashes(twitter_urls_redirection_chain_permutations_dict)
		end = time.time()
		print "time taken to compute URL hashes: {0:.0f}".format(end-start)+"secs ({0:.0f}".format((end-start)/60)+"mins)"

		# import GSB urls + convert to dict
		print "\nimporting GSB hash prefixes + converting to dict"
		start = time.time()
		#gsb_hashes_list = importGSBHashes()
		#gsb_hashes_list = importGSBHashPrefixes()
		gglsbl_db = "/tmp/gsb_v4.db"
		sql_db = sqlite3.connect(gglsbl_db)
		cursor = sql_db.cursor()
		cursor.execute('''SELECT value from hash_prefix''') #get all hash prefixes
		#cursor.execute('''SELECT value from full_hash''') #get all full hashes
		gsb_hashes_list = cursor.fetchall()
		#print "len:",len(all_rows)

		#print gsb_hashes_list
		#print "total num GSB hashes: ",len(gsb_hashes_list)
		print "total num GSB hashes: ",len(gsb_hashes_list)
		gsb_hashes_dict = convertGSBToDict(gsb_hashes_list)
		print "gsb_urls_dict length (unique GSB hashes): ",len(gsb_hashes_dict)
		end = time.time()
		print "time taken to import GSB URLs: {0:.0f}".format(end-start)+"secs ({0:.0f}".format((end-start)/60)+"mins)"




		# GSB lookup_v2 twitter URLs
		print "\nlooking up Twitter URLs in GSB..."
		start = time.time()
		url_lookup = URLLookup_v2(twitter_urls_hashes_dict, gsb_hashes_dict, twitter_urls_dict, False)
		end = time.time()
		print "time taken to lookup GSB URLs (dict): {0:.0f}".format(end-start)+"secs ({0:.0f}".format((end-start)/60)+"mins)"
		print "pishing matches: ",url_lookup[0]
		total_phishing += url_lookup[0]
		print "malware matches: ",url_lookup[1]
		total_malware += url_lookup[1]
		print "unique phishing matches: ", len(url_lookup[2])
		print "unique malware matches: ", len(url_lookup[3])
		print "phishing matches:"
		for url in url_lookup[2]:
			print url
		print "malware matches:"
		for url in url_lookup[3]:
			print url
		print "url hash prefix matches:", url_lookup[4]
		print "url hash prefix non-collision matches:", url_lookup[5]
		print "num hash prefix matches but urls already checked before:", url_lookup[6]
		print "num url gsb matches:", url_lookup[7]
		print "num url gsb lookups:", url_lookup[8]
		#print "num new urls checked :", len(twitter_urls_hashes_dict)-url_lookup[6]
		#print "out of total urls :", len(twitter_urls_hashes_dict)

		# GSB lookup_v2 twitter URL permutations
		'''print "\nlooking up Twitter URL permutations in GSB..."
		start = time.time()
		url_lookup = URLLookup_v2(twitter_urls_permutations_hashes_dict, gsb_hashes_dict, twitter_urls__permutations_dict, False, True)
		end = time.time()
		print "time taken to lookup GSB URLs (dict): {0:.0f}".format(end-start)+" seconds ({0:.0f}".format((end-start)/60)+" minutes)"
		print "pishing matches: ",url_lookup[0]
		total_phishing += url_lookup[0]
		print "malware matches: ",url_lookup[1]
		total_malware += url_lookup[1]
		print "unique phishing matches: ", len(url_lookup[2])
		print "unique malware matches: ", len(url_lookup[3])
		for url in url_lookup[2]:
			print url'''

		'''# GSB lookup_v2 twitter redirection chain URLs
		print "\nlooking up Twitter redirection chain URLs in GSB..."
		start = time.time()
		url_lookup = URLLookup_v2(twitter_urls_redirection_chain_hashes_dict, gsb_hashes_dict, twitter_urls_redirection_chain_dict, True)
		end = time.time()
		print "time taken to lookup GSB URLs (dict): {0:.0f}".format(end-start)+"secs ({0:.0f}".format((end-start)/60)+"mins)"
		print "pishing matches: ",url_lookup[0]
		total_phishing += url_lookup[0]
		print "malware matches: ",url_lookup[1]
		total_malware += url_lookup[1]
		print "unique phishing matches: ", len(url_lookup[2])
		print "unique malware matches: ", len(url_lookup[3])
		print "phishing matches:"
		for url in url_lookup[2]:
			print url
		print "malware matches:"
		for url in url_lookup[3]:
			print url
		print "url hash prefix matches:", url_lookup[4]
		print "url hash prefix non-collision matches:", url_lookup[5]
		print ""'''

		# GSB lookup_v2 twitter redirection chain permutation URLs
		'''print "\nlooking up Twitter redirection chain permutation URLs in GSB..."
		start = time.time()
		url_lookup = URLLookup_v2(twitter_urls_redirection_chain_permutations_hashes_dict, gsb_hashes_dict, twitter_urls_redirection_chain_permutations_dict, True, True)
		end = time.time()
		print "time taken to lookup GSB URLs (dict): {0:.0f}".format(end-start)+" seconds ({0:.0f}".format((end-start)/60)+" minutes)"
		print "pishing matches: ",url_lookup[0]
		total_phishing += url_lookup[0]
		print "malware matches: ",url_lookup[1]
		total_malware += url_lookup[1]
		print "unique phishing matches: ", len(url_lookup[2])
		print "unique malware matches: ", len(url_lookup[3])
		for url in url_lookup[2]:
			print url'''




		#batchEnd = time.time()
		#print "time taken to complete batch: {0:.0f}".format(batchEnd-batchStartTime)+" seconds ({0:.0f}".format((batchEnd-batchStartTime)/60)+" minutes)"

		mainEnd = time.time()
		print "time taken to complete whole script: {0:.0f}".format(mainEnd-mainStart)+"secs ({0:.0f}".format((mainEnd-mainStart)/60)+"mins)"
		print "num SE URLs: {0:.0f}".format(total_phishing)
		print "num MW URLs: {0:.0f}".format(total_malware)
		'''log("tpl_fast_v2-output.txt",
			"number of twitter URLs: {0:.0f}".format(len(twitter_urls_dict))
			+ "\nnumber of twitter redirection chain URLs: {0:.0f}".format(len(twitter_urls_redirection_chain_dict))
			+ '\ntime taken to complete whole script: ({0:.0f}'.format((mainEnd-mainStart)/60)+'mins)'
		      "\nnum SE URLs: {0:.0f}".format(total_phishing)
			+ "\nnum malware URLs: {0:.0f}".format(total_malware)
			+ '\n----------\n\n'
		)'''

		con.close()
		twitter_urls_dict.clear()
		#twitter_urls_redirection_chain_dict.clear()
		gc.collect() # clear carbage
		
		runTime = (mainEnd-mainStart)
		seconds_to_run = 600
		if runTime < seconds_to_run:
			#log("waiting "+str((3600-runTime)/60)+" minutes............................................")
			print "waiting {0:.0f}".format((seconds_to_run-runTime)/60)+"mins"
			print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			time.sleep(seconds_to_run-runTime)
		else:
			#log("waiting 0 minutes............................................")
			print "waiting 0mins..."
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
		print error_string
		sendAdminAlert("Error in "+script_file_name, 
		"Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string))

		print "waiting 90 seconds"
		time.sleep(90)




