import sys
import csv
import MySQLdb.cursors
import json
import requests
import time
import httplib, sys
import numpy as np 
import MySQLdb as mdb
from collections import Counter
from urlparse import urlparse
from threading import Thread
from Queue import Queue
import requests
import eventlet
import robotparser
eventlet.monkey_patch()
from include_stuff import progress_bar # used to display progress bar on terminal

with open('config.json') as data_file:    
	config = json.load(data_file)


concurrent = 100
redirection_chain = {}

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

# get the latest tweets
def getLatestTweets():
	cursor = con.cursor()
	limit = 1000
	cursor.execute("SELECT id, urls, hashtags FROM tweets_5 WHERE pt_processing = 0 ORDER BY id DESC LIMIT "+ str(limit))
	row = cursor.fetchone()
	counter = 0
	printCounter = 0
	results = []
	hashtags = {}
	while row is not None:
		results.append(row)
		hashtags[row[0]] = row[2].lower().split(',')[:-1]
		'''printCounter += 1
		counter += 1
		if (printCounter == 10):
			progress_bar(counter, limit, '%s of %s' % (counter, limit))
			printCounter = 0'''
		row = cursor.fetchone()	
	cursor.close()
	return (results, hashtags)

# get the latest tweets
def getTrendingHashtags():
	cursor = con.cursor()
	cursor.execute("SELECT name FROM trending_hashtags_5 ")
	row = cursor.fetchone()
	counter = 0
	printCounter = 0
	hashtags= {}
	while row is not None:
		hashtags[row[0].lower()[1:]] = 0
		row = cursor.fetchone()	
	cursor.close()
	return (hashtags)

def doWork():
	while True:
		data = q.get()
		url = data[0]
		tweet_id = data[1]
		rdc = getRedirectionChain(url, tweet_id)
		cond_redirect = condRedirect(url)
		if rdc:
			redirection_chain[url] = (rdc, cond_redirect)
		q.task_done()

# produce redirection chain
def getRedirectionChain(url, tweet_id):
	user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/601.6.17 (KHTML, like Gecko) Version/9.1.1 Safari/601.6.17'
	#user_agent = 'Googlebot'
	#user_agent = 'bingbot'
	set_headers = {
		'User-Agent': user_agent
	}
	with eventlet.Timeout(10):

		try:
			r = requests.head(url, headers=set_headers, timeout=(3.05,6), allow_redirects=True)
			#r = requests.head(url, headers=set_headers, timeout=(0.5,0.6), allow_redirects=True)
			if len(r.history) > 0:
				chain = []
				code = r.history[0].status_code
				final_url = r.url
				for resp in r.history:
					chain.append(resp.url)
				r.close()
				return (str(code), str(len(r.history)), chain, final_url, tweet_id)
			else:
				r.close()
				return (str(r.status_code), 0, [],url, tweet_id)
			
		except:
			error = 1
			#print "We have an error:", sys.exc_info()[1]
			#print "URL:",url
	return 0

# check for conditional redirect. Returns true if present
def condRedirect(url):
	user_agent_a = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/601.6.17 (KHTML, like Gecko) Version/9.1.1 Safari/601.6.17'
	user_agent_b = 'Googlebot'
	#user_agent = 'bingbot'
	set_headers_a = {
		'User-Agent': user_agent_a
	}
	set_headers_b = {
		'User-Agent': user_agent_b
	}
	with eventlet.Timeout(10):
		try:
			r1 = requests.head(url, headers=set_headers_a, timeout=(3.05,6), allow_redirects=True)
			r2 = requests.head(url, headers=set_headers_b, timeout=(3.05,6), allow_redirects=True)
			final_url_a = r1.url
			final_url_b = r2.url
			#return final_url_a != final_url_b
			if final_url_a != final_url_b:
				print final_url_a +" : "+final_url_b
				return True

		except:
			return False
			#print "We have an error:", sys.exc_info()[1]
			#print "URL:",url
	return False

'''
# check for conditional redirect via robots.txt. Returns true if present
def robotsCondRedirect(url):
	try:
		urlp = urlparse(url)
		robot = urlp.scheme +"://"+ urlp.netloc+"/robots.txt"
 		#print robot
 	
		request = requests.head(robot, timeout=(3.05,6), allow_redirects=False)
		if request.status_code == 200:
			rp = robotparser.RobotFileParser()
			rp.set_url(robot)
			rp.read()
			if not rp.can_fetch("*", url):
				print robot
				return True
			else:
				return False
	except:
		return False'''



# calculate levenshtein distance for 2 string
def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

counter = 0
threads = []
start_time = time.time()

q = Queue(concurrent * 2)
for i in range(concurrent):
	t = Thread(target=doWork)
	t.daemon = True
	t.start()
	threads.append(t)

while True:
	redirection_chain = {}
	start_time = time.time()
	print "\nimporting latest tweets..."
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='latin1',cursorclass = mdb.cursors.SSCursor)
		con.autocommit(True)
		cur = con.cursor()
		tweets = getLatestTweets()[0]
	except:
		print "We have an error:", sys.exc_info()[1]
		print "waiting 90 seconds"
		time.sleep(90)
	print "crawling URLs..."

	try:
		for tweet in tweets:
			#print tweet
			urls = tweet[1]
			tweet_id = tweet[0]
			split_urls = urls.split(",")
			first_url = split_urls[0]
			q.put((first_url.strip(),tweet_id))

		q.join()

	except KeyboardInterrupt:
		sys.exit(1)

	alive_counter = 0
	dead_counter = 0
	cond_red_counter = 0

	try:
		for thread in threads:
			if thread.is_alive():
				alive_counter += 1
			else:
				dead_counter += 1
		print "total alive:",alive_counter
		print "total dead:",dead_counter

		print "all done"
		for url, data in reversed(redirection_chain.items()):
			red_chain = data[0]
			cond_red = data[1]
			if cond_red:
				cond_red_counter += 1
				#print url

			num_hops = str(red_chain[1])
			land_page = str(red_chain[3].encode('utf-8').strip())
			tweet_id = str(red_chain[4])
			chain_string = ""
			for c_url in red_chain[2]:
				chain_string += c_url + " -> "
			chain_string += land_page
			#print str(tweet_id) + ", " + str(num_hops)+ ", " + chain_string

			url_chain = red_chain[2]
			if len(url_chain) > 0:
				levenshtein_distance = levenshteinDistance(red_chain[2][0], land_page)
			else:
				levenshtein_distance = 0
			#print "lev distance:", levenshtein_distance

			cur.execute("UPDATE tweets_5 SET num_redirects = '"+str(num_hops)+"', redirection_chain = %s, lev_distance = %s, cond_redirect = %s, pt_processing = '1' WHERE id = '"+str(tweet_id)+"'", (chain_string, levenshtein_distance, cond_red))
			con.commit()


		print "\nnum urls processed: "+str(len(redirection_chain)) + " / " + str(len(tweets))
		print "num cond reds:",cond_red_counter

		end_time = time.time()
		print "time taken to complete: {0:.2f}".format(end_time-start_time)+" seconds ({0:.2f}".format((end_time-start_time)/60)+" minutes)"


		# compute trending hashtags:
		print "looking up trending hashtags..."
		trending_hashtags = getTrendingHashtags()
		hashtags_dict = getLatestTweets()[1]
		
		counter = 0
		printCounter = 0
		total_trending_counter = 0
		tweets_using_trending_hashtags_counter = 0

		for tweet,hashtags in hashtags_dict.items():
			trending_flag = False
			for h in hashtags:
				if h in trending_hashtags:
					total_trending_counter += 1
					trending_flag = True
			if trending_flag:
				tweets_using_trending_hashtags_counter += 1
				cur.execute("UPDATE tweets_5 SET trending_hashtags = '1' WHERE id = '"+str(tweet)+"'", ())
				con.commit()

			# display progress bar:
			'''printCounter += 1
			counter += 1
			if (printCounter == 100):
				progress_bar(counter, len(hashtags_dict), '%s of %s' % (counter, len(hashtags_dict)))
				printCounter = 0'''


		print "total trending matches:", total_trending_counter
		print "tweets containing trending #s:", tweets_using_trending_hashtags_counter
		print "sleeping for 30 secs..."
		time.sleep(30)
		con.close()
	except:
		print "We have an error:", sys.exc_info()[1]
		print "waiting 90 seconds"
		time.sleep(90)

