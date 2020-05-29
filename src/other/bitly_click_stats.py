from __future__ import division
import bitly_api
import sys
import numpy as np
import matplotlib as mpl 
#mpl.use('Agg')
from matplotlib import pyplot as plt
#from mpl_toolkits.axes_grid1 import host_subplot
#import mpl_toolkits.axisartist as AA
from matplotlib.ticker import FuncFormatter
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
import matplotlib.dates as mdates
import matplotlib.ticker as tkr
import MySQLdb as mdb
import MySQLdb.cursors
import sqlite3
import time
import datetime
import random
import math
import json
import collections
from collections import OrderedDict
from urlparse import urlparse
from collections import OrderedDict
from gglsbl.protocol import URL
import tldextract


with open('config.json') as data_file:    
	config = json.load(data_file)

con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
con.autocommit(True)
cursor = con.cursor()

# Define your API information
b = bitly_api.Connection(access_token=config['bitly']['access_token'])


def formatURL(url, permutation=False):
	url = url.encode('utf8')
	#url = url.rstrip('/')
	#url = url.encode('utf8')
	#url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
	#url = urlparse(url)[1]
	url_class = URL(url)
	con_url = url_class.canonical
	return con_url

def extractDomain(url):
	ext = tldextract.extract(url)
	return ext.domain +"."+ ext.suffix

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
	twitter_urls_list = []
	printCounter=0
	counter = 0
	while row is not None:
		#url = row[0].rstrip('/')
		formatted_url = formatURL(row[0])
		date = row[1]
		#twitter_urls_dict[formatted_url] = None

		twitter_urls_list.append(formatted_url)
		if formatted_url in twitter_urls_dict:
			twitter_urls_dict[formatted_url].append(date)
		else:
			twitter_urls_dict[formatted_url] = [date,]
			
		row = cur.fetchone()	

	cur.close()
	return twitter_urls_dict,twitter_urls_list

def getBitlyClickStats(urls):

	urls_to_check_in_bitly = {}
	total_num_bitly_urls = 0
	total_bitly_clicks = 0
	ctr = 0

	for url in urls:
		#print url
		domain = extractDomain(url)
		#print domain
		if domain == "Bit.ly" or domain == "bit.ly" or domain == "bitly.com":
			#print domain
			total_num_bitly_urls +=1 
			if url not in urls_to_check_in_bitly:
				urls_to_check_in_bitly[url] = None

	for bitly_url in urls_to_check_in_bitly:
		
		bitly_clicks = 0
		ctr += 1

		path = urlparse(bitly_url).path
		bitly_hash =  path[1:]
		print "bitly hash:", bitly_hash

		try:
			'''
			# all clicks stats:
			response = b.clicks(bitly_hash)
			bitly_clicks = response[0]['global_clicks']
			print "clicks:", bitly_clicks
			'''

			#'''
			# just t.co referrer stats:
			response = b.referrers(bitly_hash)
			for r in response:
				if 'referrer' in r:
					if r['referrer'] == 'https://t.co/':
						bitly_clicks = r['clicks']
						print "t.co referrer clicks:", bitly_clicks
				else:
					print "no fererrer info"
			#'''				
		except KeyboardInterrupt:
			exit()
		except bitly_api.bitly_api.BitlyError as e:
			print "Bitly API error:", e
		

		total_bitly_clicks += bitly_clicks
		print str(ctr) +" of "+ str(len(urls_to_check_in_bitly))

	print "bitly click stats:"
	print "total num urls:", len(urls)
	print "total num bitly urls:", total_num_bitly_urls
	print "num unique bitly urls:", len(urls_to_check_in_bitly)
	print "total bitly clicks:", total_bitly_clicks





mainStart = time.time()

#t_co_filtered_urls = importTCoFilteredDateRange('2018-11-01', '2018-11-30') # Nov t.co
t_co_filtered_urls = importTCoFilteredDateRange('2018-12-01', '2018-12-02') # Dec t.co
getBitlyClickStats(t_co_filtered_urls[1])

mainEnd = time.time()
print "time taken to complete whole script: {0:.0f}".format(mainEnd-mainStart)+"secs ({0:.0f}".format((mainEnd-mainStart)/60)+"mins)"
		
