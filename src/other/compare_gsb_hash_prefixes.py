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

with open('config.json') as data_file:    
	config = json.load(data_file)

con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_4'],charset='utf8')
con.autocommit(True)
cur = con.cursor()

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

def importGSBHashPrefixes(sbl):
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
			gsb_urls_dict[url_hash] = True

	#if url_hash not in twitter_url_hash_prefixes_dict:
	#    url = twitter_url_hash_prefixes_dict[url_hash]
	return gsb_urls_dict


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

# pull stats ditect from sqlite dbs:
conn = sqlite3.connect("/tmp/gsb_v3b.db")
c = conn.cursor()
c.execute("SELECT * FROM hash_prefix  ")
rows_a = c.fetchall()
print "/tmp/gsb_v3b.db:",len(rows_a)

conn = sqlite3.connect("/tmp/gsb_v3c.db")
c = conn.cursor()
c.execute("SELECT * FROM hash_prefix  ")
rows_a = c.fetchall()
print "/tmp/gsb_v3c.db:",len(rows_a)

conn = sqlite3.connect("/tmp/gsb_v4.db")
c = conn.cursor()
c.execute("SELECT * FROM hash_prefix  ")
rows_a = c.fetchall()
print "/tmp/gsb_v4.db:",len(rows_a)

exit()
# pull stats ditect from sqlite dbs:
conn = sqlite3.connect("/tmp/gsb_v4.db")
c = conn.cursor()

c.execute("SELECT * FROM hash_prefix WHERE threat_type = 'SOCIAL_ENGINEERING' ")
rows_a = c.fetchall()
print "GSBv total SOCIAL_ENGINEERING threat_type:",len(rows_a)
rows_a_dict = convertGSBToDict(rows_a)
print "uniques:",len(rows_a_dict)

###

conn = sqlite3.connect("/tmp/gsb_v3b.db")
c = conn.cursor()

c.execute("SELECT *  FROM hash_prefix WHERE list_name = 'googpub-phish-shavar' ")
rows_b = c.fetchall()
print "GSBv3 total googpub-phish-shavar list_name:",len(rows_b)
rows_b_dict = convertGSBToDict(rows_b)
print "uniques:",len(rows_b_dict)


shared_items = set(rows_a_dict.items()) & set(rows_b_dict.items())
print "shared items:",len(shared_items)

