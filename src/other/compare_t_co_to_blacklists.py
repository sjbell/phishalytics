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
from gglsbl.protocol import URL

from collections import OrderedDict

with open('config.json') as data_file:    
	config = json.load(data_file)

def formatURL(url, permutation=False):
	url = url.encode('utf8')
	#url = url.rstrip('/')
	#url = url.encode('utf8')
	#url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
	#url = urlparse(url)[1]
	url_class = URL(url)
	con_url = url_class.canonical
	return con_url

def importRecentGSBMatches(limit):
	cur = con.cursor()
	cur.execute('SELECT url FROM gsb_full_hash_log_5 WHERE not_in_gsb = 0 ORDER BY id DESC  LIMIT '+str(limit))
	#cursor.execute("SELECT url,tweet_id FROM tweet_urls_3 WHERE DATE(date_added) = '2017-03-20'  ")
	#cursor.execute("SELECT url,tweet_id FROM tweet_urls_3 LIMIT "+str(start)+", "+str(batch_size)+" ")
	row = cur.fetchone()
	twitter_urls_dict = {}
	#twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		#url = row[0].rstrip('/')
		formatted_url = formatURL(row[0])
		twitter_urls_dict[formatted_url] = None
		counter += 1
		printCounter += 1
		if (printCounter == 100):
			progress_bar(counter, limit, '%s of %s' % (counter, limit))
			printCounter = 0
		row = cur.fetchone()	

	#print "twitter_urls_list len: ",len(twitter_urls_list)
	#print "num recent GSB urls: ",len(twitter_urls_dict)
	cur.close()
	return twitter_urls_dict

def importRecentTCoFiltered(limit):
	cur = con.cursor()
	cur.execute('SELECT full_url FROM t_co_all_urls_experiment ORDER BY id DESC  LIMIT '+str(limit))
	#cursor.execute("SELECT url,tweet_id FROM tweet_urls_3 WHERE DATE(date_added) = '2017-03-20'  ")
	#cursor.execute("SELECT url,tweet_id FROM tweet_urls_3 LIMIT "+str(start)+", "+str(batch_size)+" ")
	row = cur.fetchone()
	twitter_urls_dict = {}
	#twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		#url = row[0].rstrip('/')
		formatted_url = formatURL(row[0])
		twitter_urls_dict[formatted_url] = None
		counter += 1
		printCounter += 1
		if (printCounter == 100):
			progress_bar(counter, limit, '%s of %s' % (counter, limit))
			printCounter = 0
		row = cur.fetchone()	

	#print "twitter_urls_list len: ",len(twitter_urls_list)
	#print "num recent t.co urls: ",len(twitter_urls_dict)
	cur.close()
	return twitter_urls_dict

def importGSBMatchesDateRange(from_date, to_date):
	cur = con.cursor()
	cur.execute("""
		SELECT url, lookup_date 
		FROM gsb_full_hash_log_5
		WHERE not_in_gsb = 0
		AND lookup_date
			BETWEEN CAST('"""+from_date+"""' AS DATE)
			AND CAST('"""+to_date+"""' AS DATE)
		""")
	row = cur.fetchone()
	twitter_urls_dict = OrderedDict()
	#twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		#url = row[0].rstrip('/')
		formatted_url = formatURL(row[0])
		date = row[1]
		if formatted_url in twitter_urls_dict:
			twitter_urls_dict[formatted_url].append(date)
		else:
			twitter_urls_dict[formatted_url] = [date,]
		#counter += 1
		#printCounter += 1
		#if (printCounter == 100):
		#	progress_bar(counter, limit, '%s of %s' % (counter, limit))
		#	printCounter = 0
		row = cur.fetchone()	

	#print "twitter_urls_list len: ",len(twitter_urls_list)
	#print "num recent GSB urls: ",len(twitter_urls_dict)
	cur.close()
	return twitter_urls_dict

def importTCoFilteredDateRange(from_date, to_date):
	cur = con.cursor()
	cur.execute("""
		SELECT full_url, date
		FROM t_co_all_urls_experiment
		WHERE DATE(date)
			BETWEEN CAST('"""+from_date+"""' AS DATE)
			AND CAST('"""+to_date+"""' AS DATE)
	""")
	row = cur.fetchone()
	twitter_urls_dict = {}
	#twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		#url = row[0].rstrip('/')
		formatted_url = formatURL(row[0])
		date = row[1]
		#twitter_urls_dict[formatted_url] = None

		if formatted_url in twitter_urls_dict:
			twitter_urls_dict[formatted_url].append(date)
		else:
			twitter_urls_dict[formatted_url] = [date,]
			
		row = cur.fetchone()	

	cur.close()
	return twitter_urls_dict


def importPhishTankURLs():
	cursor = con.cursor()
	#cursor.execute("SELECT url FROM phish_tank_urls LIMIT "+str(start)+", "+str(batch_size)+" ")
	cursor.execute("SELECT url,id FROM phish_tank_urls_5 ")
	row = cursor.fetchone()
	pt_urls_dict = {}
	printCounter=0
	counter = 0
	while row is not None:
		url = row[0]
		formatted_url = formatURL(url)
		pt_urls_dict[formatted_url] = row[1]
		
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
   

con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
#cursor = con.cursor()
con.autocommit(True)


#gsb db stuff:
gglsbl_db = "/home/simon/gsb_v4-18_jan_2019_backup.db"
sql_db = sqlite3.connect(gglsbl_db)
cursor = sql_db.cursor()

#sbl = SafeBrowsingList(config['gsb-api']['key'])


#gsb_matches = importRecentGSBMatches(5000) # 889 total (887 unique) results as of Fri 18 Jan 2019
#t_co_filtered = importRecentTCoFiltered(200000) # 104,610 total (17,713 unique) results as of Fri 18 Jan 2019

gsb_matches = importGSBMatchesDateRange('2018-11-01', '2018-11-30') # Nov gsb
t_co_filtered = importTCoFilteredDateRange('2018-11-01', '2018-11-30') # Nov t.co
#gsb_matches = importGSBMatchesDateRange('2018-12-01', '2018-12-31') # Dec GSB
#t_co_filtered = importTCoFilteredDateRange('2018-12-01', '2018-12-31') # Dec t.co

#gsb_matches[formatURL('http://nastygirls.xyz')] = None
#t_co_filtered['http://nastygirls.xyz'] = None

op_urls = importOpenPhishURLs()
pt_urls = importPhishTankURLs()


found_ctr = 0
for key in gsb_matches:
	#print key
	if key in t_co_filtered:
		print key

		print "GSB (gglsbl) timestamps:"
		url = key
		url_hashes = URL(url).hashes
		hash_list = []

		for h in url_hashes:
			hash_list.append(h)

		for url_hash in hash_list:
			hash_prefix = sqlite3.Binary(url_hash[0:4])
			#hash_prefix = str(hash_prefix).encode('hex')
			#print hash_prefix

			cursor.execute("""
				SELECT timestamp, threat_type, platform_type, threat_entry_type
				FROM hash_prefix
				WHERE value = ?
			""", (hash_prefix,)) #get all hash prefixes
			results = cursor.fetchall()
			if len(results) > 0:
				for r in results:
					print r[0] + "("+ r[1] +","+ r[2] +","+ r[3] +")"


		print "GSB timestamps:"
		for t in gsb_matches[key]:
			print t

		print "t.co blocked timestamps:"
		for t in t_co_filtered[key]:
			print t


		#print "match"
		found_ctr += 1
		print "\n"

op_match_ctr = 0
for key in op_urls:
	if key in t_co_filtered:
		op_match_ctr += 1
		print key

pt_match_ctr = 0
for key in pt_urls:
	if key in t_co_filtered:
		pt_match_ctr += 1
		print key
		print pt_urls[key]

print "gsb_matches: ",len(gsb_matches)
print "total num t_co filtered: ",len(t_co_filtered)
print "total num OP urls: ",len(op_urls)
print "total num PT urls: ",len(pt_urls)
print "total t.co-GSB intersection matches:", found_ctr
print "total t.co-OP intersection matches:", op_match_ctr
print "total t.co-PT intersection matches:", pt_match_ctr

print "\n"

