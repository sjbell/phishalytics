import time
import sys
import urllib
import urllib2
import hashlib
import MySQLdb as mdb
import MySQLdb.cursors
import sqlite3
import traceback
import datetime
import math
import json
from socket import error as SocketError
import errno
from include_stuff import progress_bar # used to display progress bar on terminal

from sqlite3 import IntegrityError
from gglsbl import SafeBrowsingList
from gglsbl.protocol import URL

with open('config.json') as data_file:    
	config = json.load(data_file)

sbl = SafeBrowsingList(config['gsb-api']['key'])

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
	url = url.replace("*.", "")
	url = url.replace("?.", "")
	#url = url.rstrip('/')
	#url = url.encode('utf8')
	#url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
	#url = urlparse(url)[1]
	url_class = URL(url)
	#print url
	con_url = url_class.canonical
	return con_url

def URLPermutations(url):
	url_class = URL(url)
	urls = []
	for url_variant in url_class.url_permutations(url):
		urls.append(url_variant)
		#print url_variant
	return urls

# count number of twitter URLs
def countTwitterURLs():
	cur = con.cursor()
	cur.execute("SELECT count(*) FROM tweet_urls_5")
	row = cur.fetchone()
	while row is not None:
		twitter_urls_count = row[0]
		row = cur.fetchone()
	cur.close()
	return twitter_urls_count

# count number of tweets
def countTweets():
	cur = con.cursor()
	cur.execute("SELECT count(*) FROM tweets_4")
	row = cur.fetchone()
	while row is not None:
		tweets_count = row[0]
		row = cur.fetchone()
	cur.close()
	return tweets_count

# import URLs into dict + list from MySQL db: + also import redirection chain URLs
def importSuspiciousCertStreamURLs():
	cur = con.cursor()
	#cur.execute('SELECT url FROM tweet_urls LIMIT 500000')
	#cur.execute("SELECT url,tweet_id FROM tweet_urls_4 LIMIT "+str(start)+", "+str(batch_size)+" ")
	cur.execute("SELECT domain, id FROM certstream_suspicious_5 WHERE in_gsb IS NULL")
	row = cur.fetchone()
	domains = []
	while row is not None:
		#if row[0] !="":
		formatted_domain = formatURL("http://"+row[0])
		domains.append((formatted_domain,row[1]))
		row = cur.fetchone()
	cur.close()
	return domains

# import URLs into dict + list from MySQL db: + also import redirection chain URLs
def importCertStreamURLs(limit):
	counter = 0
	printCounter = 0
	cur = con.cursor()
	#cur.execute('SELECT url FROM tweet_urls LIMIT 500000')
	#cur.execute("SELECT url,tweet_id FROM tweet_urls_4 LIMIT "+str(start)+", "+str(batch_size)+" ")
	#cur.execute("SELECT domain, id FROM certstream_domains_5 ORDER BY id DESC LIMIT "+str(limit))
	cur.execute("SELECT domain FROM certstream_domains_5 ORDER BY id DESC LIMIT "+str(limit))
	row = cur.fetchone()
	domains = []
	while row is not None:
		#if row[0] !="":
		formatted_domain = formatURL("http://"+row[0])
		#domains.append((formatted_domain,row[1]))
		domains.append(formatted_domain)

		counter += 1
		printCounter += 1
		if (printCounter == 1000):
			progress_bar(counter, limit, '%s of %s' % (counter, limit))
			printCounter = 0
		row = cur.fetchone()
	cur.close()
	return domains

def lookup_gsb_full_hash(full_hash):
	cur = con.cursor()
	cur.execute("SELECT * FROM gsb_full_hash_log_CT_5 WHERE full_hash = %s", (full_hash, ))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone()
	return result==None
		
def computeURLHashes(domains):
	twitter_urls_hashes_dict = {}
	num_urls = len(domains)
	counter = 0
	printCounter = 0
	for url in domains:
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
			gsb_urls_dict[url_hash] = url_hash

	#if url_hash not in twitter_url_hash_prefixes_dict:
	#    url = twitter_url_hash_prefixes_dict[url_hash]
	return gsb_urls_dict

def URLLookup_v2(domain_hashes, gsb_urls):
	# twitter_urls = (hash_list)
	# twitter_urls_dict = (tweet_ids)
	phish_count = 0
	malware_count = 0
	phishing_matches = {}
	counter = 0
	hash_prefix_counter = 0
	printCounter = 0
	num_urls = len(domain_hashes)
	malware_domains = []
	phishing_domains = []
	for url in domain_hashes:
		#print url
		url_hashes = domain_hashes[url]
		for url_hash in url_hashes:
			#print url_hash
			hash_prefix = sqlite3.Binary(url_hash[0:4])
			hash_prefix = str(hash_prefix).encode('hex')
			if hash_prefix in gsb_urls:

				if(lookup_gsb_full_hash(sqlite3.Binary(url_hash))):

					hash_prefix_counter += 1
					database_lock = True
					while database_lock:
						try:
							print "url hash prefix match!"
							#gsblookup = sbl.lookup_hash(url_hash)
							gsblookup = sbl.lookup_url(url)
							if gsblookup:

								cur = con.cursor()
								sql = "INSERT INTO gsb_full_hash_log_certstream_5(url, hash_prefix, full_hash) VALUES(%s, %s, %s)"
								cur.execute(sql, (url[0:500], sqlite3.Binary(url_hash[0:4]), sqlite3.Binary(url_hash)))

								print "url full hash match!"
								for i in gsblookup:
									print i
									if str(i) == "MALWARE/ANY_PLATFORM/URL":
										cur.execute("UPDATE gsb_full_hash_log_certstream_5 SET malware = '1' WHERE full_hash = %s",(url_hash,))
										con.commit()
										print "malware"
										malware_count +=1 
										#sys.stdout.write('\r-')
										#sys.stdout.flush()
										#malware_domains.append()
									if str(i) == "SOCIAL_ENGINEERING/ANY_PLATFORM/URL":
										cur.execute("UPDATE gsb_full_hash_log_certstream_5 SET social_engineering = '1' WHERE full_hash = %s",(url_hash,))
										con.commit()
										print "phishing "#,url_data[0]
										phish_count += 1
										#logPhishingURL(url, 3, twitter_urls_dict[url], redirection_chain_url_lookup)
										#markTweetsPhishy(url, twitter_urls_dict[url])
										phishing_matches[url] = (url_hash)

							else: # url hash prefix match but full hash not in GSB i.e. different URL. Mark in db so doesn't get checked again
								cur = con.cursor()
								sql = "INSERT INTO gsb_full_hash_log_certstream_5(hash_prefix, full_hash, not_in_gsb) VALUES(%s, %s, %s)"
								cur.execute(sql, (sqlite3.Binary(url_hash[0:4]), sqlite3.Binary(url_hash), 1))

							database_lock = False
						except (RuntimeError, IntegrityError, urllib2.HTTPError, urllib2.URLError, SocketError) as e:
							print e
							print url
							log("tpl_v3.2-output.txt", "error: "+str(e.message)+"\nURL: "+url+"\n")
							print "waiting 5 seconds..."
							time.sleep(5)
							database_lock = False
						except sqlite3.OperationalError:
							print("database locked, waiting 5 seconds...")
							log("tpl_v3.2-output.txt", "gglsbl3 database is locked")
							time.sleep(5)
							database_lock = False
						except KeyError:
							# 18 Jun 2018, disabling error: 'exceptions.KeyError'>, KeyError('matches',)
							# as appearing every minute or so
							print "Looks like a key error:", sys.exc_info()[1]
							log("certstream-url-checker-v2-phishing_5.txt", "Looks like a key error: "+str(sys.exc_info()[1]))
							print "URL:", url
							time.sleep(5)
							database_lock = False
						except:
							print "We have an error:", sys.exc_info()[1]
							print sys.exc_info()
							import os
							import traceback
							from send_email import sendAdminAlert
							script_file_name = os.path.basename(__file__)
							error_string = ""
							for frame in traceback.extract_tb(sys.exc_info()[2]):
								fname,lineno,fn,text = frame
								error_string += "\nError in %s on line %d" % (fname, lineno)
							print error_string
							sendAdminAlert("Error (within URLLookup_v2 loop) in "+script_file_name, 
							"Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string))
							print "waiting 90 seconds"
							time.sleep(90)
							database_lock = False

				else:
					print "URL already in gsb_full_hash_lookup"
				#j+=1
		counter += 1
		printCounter += 1
		if (printCounter == 10):
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
		cur.execute("UPDATE tweets_5 SET phishing = '1' WHERE id = '"+str(tweet_id)+"'")
		con.commit()
		
		cur.execute("UPDATE tweets_5 SET date_first_marked_phishing = NOW() WHERE id = '"+str(tweet_id)+"' AND date_first_marked_phishing is NULL")
		con.commit()
		
		#cur.execute("UPDATE tweet_urls_3 SET social_engineering = 1 WHERE tweet_id = '"+str(tweet_id)+"' AND social_engineering is NULL")
		#con.commit()
	cur.close()
		
# mark each tweet as malicious in tweets_2
def markTweetsMalware(url, tweets):
	cur = con.cursor()
	for tweet_id in tweets:
		#print "marking tweet id as phishing: ",tweet_id
		cur.execute("UPDATE tweets_5 SET malware = '1' WHERE id = '"+str(tweet_id)+"'")
		con.commit()

		cur.execute("UPDATE tweets_5 SET date_first_marked_malicious = NOW() WHERE id = '"+str(tweet_id)+"' AND date_first_marked_phishing is NULL")
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
	cur.close()
	return result

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
		spam_url_id = cur.lastrowid
	else:
		sql = "INSERT spam_urls_timestamp_5(spam_url_id) VALUES(%s)"
		cur.execute(sql, (spam_url_id,))
		spam_url_id = cur.lastrowid
		
	spam_url_id = checkSpamURLExists(url)
	for tweet_id in tweets:
		exists = checkSpamURLTweetIDExists(tweet_id, spam_url_id)
		if not exists:
			sql = "INSERT INTO spam_urls_tweet_ids_5(spam_url_id, tweet_id) VALUES(%s, %s)"
			cur.execute(sql, (spam_url_id, tweet_id))	

	cur.close()

def logMalwareURL(url, source, tweets, redirection_chain):
	cur = con.cursor()
	url = url[0:500]

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
		
	spam_url_id = checkSpamURLExists(url)
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


def lookupGSBTimestamp(url):
	url_hashes = sbl.get_hash(url)
	timestamp_matches_dict = {}
	timestamp_matches_list = []
	print url
	for url_hash in url_hashes:
		hash_prefix = sqlite3.Binary(url_hash[0:4])
		print hash_prefix
		full_url_hash = sqlite3.Binary(url_hash)
		#hash_prefix = str(hash_prefix).encode('hex')
		timestamps = lookupURLHashPrefix(hash_prefix)
		for t in timestamps:
			print t
			timestamp_matches_dict[t] = True
			timestamp_matches_list.append(t)
	if len(timestamp_matches_dict) == 1:
		if len(timestamps) == 1:
			print "GSB url lookup success"
			return timestamp_matches_list[0]


def lookupURLHashPrefix(url_hash_prefix):
	c.execute("SELECT timestamp FROM hash_prefix WHERE value = ?", (url_hash_prefix,))
	rows = c.fetchall()
	results = []
	for row in rows:
		results.append(row[0])
	return results

def lookup_gsb_full_hash(full_hash):
	cur = con.cursor()
	cur.execute("SELECT * FROM gsb_full_hash_log_certstream_5 WHERE full_hash = %s", (full_hash, ))
	row = cur.fetchone()
	result = None
	while row is not None:
		result = row[0]
		row = cur.fetchone()
	return result==None	



conn = sqlite3.connect("/tmp/gsb_v3b.db")
c = conn.cursor()


# begin main while loop
while True:
	mainStart = time.time()
	print "### starting loop\n",datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	mainStart = time.time()		
	counter = 0
	printCounter = 0

	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
		con.autocommit(True)

		print "importing certstream URLs from db...";
		domains = importCertStreamURLs(3000000)
		#domains.append("http://www.ir9831.com/space-uid-38985.html") # for testing, can remove
		print "num domains to check:", len(domains)

		print"computing domain hashes"
		domain_hashes = computeURLHashes(domains)

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

		print "looking up URLs in gsb..."
		start = time.time()
		result = URLLookup_v2(domain_hashes, gsb_hashes_dict)
		print "num phish:",result[0]
		print "num malware:",result[1]
		end = time.time()
		print "time taken to lookup URLs in GSB: {0:.0f}".format(end-start)+"secs ({0:.0f}".format((end-start)/60)+"mins)"

		mainEnd = time.time()
		print "script time: {0:.0f}".format(mainEnd-mainStart)+" secs ({0:.0f}".format((mainEnd-mainStart)/60)+" mins)"
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
		#sendAdminAlert("Error in "+script_file_name, 
		#"Python script: "+script_file_name+"\nError reprted: "+ str(sys.exc_info()[1])+"\nLine:" + str(error_string))

		print "waiting 90 seconds"
		time.sleep(90)
	#end = time.time()
	mainEnd = time.time()
	#print "time taken to complete whole script: {0:.0f}".format(mainEnd-mainStart)+" seconds ({0:.0f}".format((mainEnd-mainStart)/60)+" minutes)"
	runTime = (mainEnd-mainStart)
	
	# this bit ensures code runs every x seconds even if script takes y seconds to run
	repeat_every_seconds = 600
	if runTime < repeat_every_seconds:
		print "runtime: {0:.0f}".format(runTime)+"secs"
		print "\x1b[0;35mwaiting {0:.0f}".format((repeat_every_seconds-runTime))+" secs...\x1b[0m"
		print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		time.sleep(repeat_every_seconds-runTime)
