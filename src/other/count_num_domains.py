import requests
import json
import MySQLdb as mdb
import MySQLdb.cursors
import time
import datetime
import time
import math
from sqlite3 import IntegrityError
from socket import error as SocketError
import urllib
import urllib2
from urlparse import urlparse
from collections import Counter
from collections import defaultdict
import collections
import operator

import tldextract

with open('config.json') as data_file:    
	config = json.load(data_file)

con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
cursor = con.cursor()

def getTweetURLs():
	print "importing tweet URLs"
	cursor.execute("SELECT url FROM tweet_urls_3 WHERE date(date_added) = '2017-04-20' AND social_engineering = 1 ")
	row = cursor.fetchone()
	results = []
	while row is not None:
		ext = tldextract.extract(row[0])
		results.append(ext.domain+"."+ext.suffix)
		row = cursor.fetchone()	
	return results

tweet_urls = getTweetURLs()


d = defaultdict(int)
for obj in tweet_urls:
    d[obj] += 1

od = sorted(d.items(), key=operator.itemgetter(1))
#od.reverse()
print "ordered"

for domain in od:
	print str(domain[1]) + ": " + domain[0]

print len(tweet_urls)
print len(od)
