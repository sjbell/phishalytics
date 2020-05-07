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
from include_stuff import progress_bar # used to display progress bar on terminal

from socket import error as SocketError
from sqlite3 import IntegrityError
from gglsbl3.protocol import URL

with open('config.json') as data_file:    
	config = json.load(data_file)



def importSpamURLs():
	cur = con.cursor()
	cur.execute("SELECT url FROM spam_urls_5 WHERE gglsbl_timestamp IS NULL #AND date_added >= DATE_SUB(NOW(),INTERVAL 7 DAY)")
	row = cur.fetchone()
	spam_urls = []
	while row is not None:
		spam_urls.append(row[0])
		row = cur.fetchone()
	
	cur.close()
	return spam_urls

def lookupURLHashPrefix(url_hash_prefix):
	c.execute("SELECT timestamp FROM hash_prefix WHERE value = ?", (url_hash_prefix,))
	rows = c.fetchall()
	results = []
	for row in rows:
		results.append(row[0])
	return results

def lookupURLFullHash(url_full_hash):
	c.execute("SELECT downloaded_at FROM full_hash WHERE value = ?", (url_full_hash,))
	rows = c.fetchall()
	results = []
	for row in rows:
		results.append(row[0])
	return results



# begin main while loop
while True:
	
	mainStart = time.time()
	print "### starting loop ",datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8')
		con.autocommit(True)
		cur = con.cursor()
		#gglsbl3 = /tmp/gsb_v3.db
		#gglsbl4 = /tmp/gsb_v3b.db
		conn = sqlite3.connect("/tmp/gsb_v3b.db")
		c = conn.cursor()
		from gglsbl3 import SafeBrowsingList
		sbl = SafeBrowsingList(config['gsb-api']['key'])

		spam_urls = importSpamURLs()
		success_counter = 0
		zero_match_counter = 0
		multiple_counter = 0
		printCounter=0
		counter = 0

		for url in spam_urls:
			#print url
			url_hashes = sbl.get_hash(url)
			timestamp_matches_dict = {}
			timestamp_matches_list = []
			for url_hash in url_hashes:
				hash_prefix = sqlite3.Binary(url_hash[0:4])
				full_url_hash = sqlite3.Binary(url_hash)
				#hash_prefix = str(hash_prefix).encode('hex')
				timestamps = lookupURLHashPrefix(hash_prefix)
				for t in timestamps:
					timestamp_matches_dict[t] = True
					timestamp_matches_list.append(t)
			if len(timestamp_matches_dict) == 1:
				if len(timestamps) > 1:
					print "more than one timestamp returned. Might be multiple matching URL hash prefixes..."
					
					# send email alert 
					from send_email import sendAdminAlert
					message = "url: "+str(url)+"\ntimetamps: "
					for t in timestamps:
						message += str(t) +"\n"
					message += "\nhashes:"
					for url_hash in url_hashes:
						hash_prefix = sqlite3.Binary(url_hash[0:4])
						full_url_hash = sqlite3.Binary(url_hash)
						message += "full hash: "+str(full_url_hash)+" (prefix: "+str(hash_prefix)+")\n"
					script_file_name = os.path.basename(__file__)
					message += "\nIn "+script_file_name
					sendAdminAlert("hash collision", message)

				success_counter += 1
				#print url
				#print timestamp_matches_list[0]
				#print lookupURLFullHash(full_url_hash)
				cur.execute("UPDATE spam_urls_5 SET gglsbl_timestamp = %s WHERE url = %s AND gglsbl_timestamp IS NULL", (timestamp_matches_list[0], url))
				con.commit()
			elif len(timestamp_matches_dict) > 1:
				multiple_counter += 1
			elif len(timestamp_matches_dict) == 0:
				zero_match_counter += 1

			counter += 1
			printCounter += 1
			if (printCounter == 10):
				progress_bar(counter, len(spam_urls), '%s of %s' % (counter, len(spam_urls)))
				printCounter = 0

		print "\nURLs checked:", len(spam_urls)
		print "success:", success_counter
		print "zero matches:", zero_match_counter
		print "multi TSs:", multiple_counter

		conn.close()

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
	#else:
		#print "waiting 0 minutes..."

	#print "waiting 5 minutes"
	#time.sleep(300)

