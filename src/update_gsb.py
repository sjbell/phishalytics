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
from gglsbl import SafeBrowsingList

with open('config.json') as data_file:    
	config = json.load(data_file)

# begin main while loop
while True:

	mainStart = time.time()

	
	#update GSB dataset
	start = time.time()
	print "Updating local GSB dataset..."
	print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	try:

		sbl = SafeBrowsingList(config['gsb-api']['key'])	

		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'], charset='utf8')
		con.autocommit(True)
		cur = con.cursor()

		sbl.update_hash_prefix_cache()
		#hash_prefixes = sbl.get_all_hash_prefixes() #from my modified version
		
		gglsbl_db = "/tmp/gsb_v4.db"
		sql_db = sqlite3.connect(gglsbl_db)
		cursor = sql_db.cursor()
		cursor.execute('''SELECT HEX(value) from hash_prefix''') #get all hash prefixes
		#cursor.execute('''SELECT value from full_hash''') #get all full hashes
		all_rows = cursor.fetchall()
		
		gsb_url_hash_prefix_dict = {}
		for url_hash_prefix in all_rows:
			gsb_url_hash_prefix_dict[url_hash_prefix] = True
		
		sql = "INSERT INTO gsb_update_log_5(num_urls_gglsbl4, num_unique_urls_gglsbl4) VALUES(%s, %s)"
		cur.execute(sql, (len(all_rows), len(gsb_url_hash_prefix_dict)))
		
		print "len: {:,}".format(len(all_rows))
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

	end = time.time()
	print "time taken to update GSB: {0:.0f}".format(end-start)+"secs ({0:.0f}".format((end-start)/60)+"mins)"

	mainEnd = time.time()
	#print "time taken to complete whole script: {0:.0f}".format(mainEnd-mainStart)+"secs ({0:.0f}".format((mainEnd-mainStart)/60)+"mins)"
	
	runTime = (mainEnd-mainStart)
	#seconds_to_run = 1800 #30 minutes
	#seconds_to_run = 600 #10 minutes
	#seconds_to_run = 900 #15 minutes # tried this on Wed 4 Oct 2017 and just took 30 minute to update
	seconds_to_run = 300 #5 minutes, ready to put live after adjusting discard_fair_use_policy to true
	# 28 Mar 2018 13:33: tried setting 5 minutes intervals but script took 27 minutes to complete
	# thinkg the fair_usage_policy is kicking in from GSB's end. Putting it back to 30 minutes

	#seconds_to_run = 5 #5 for testing
	if runTime < seconds_to_run:
		#log("waiting "+str((3600-runTime)/60)+" minutes............................................")
		print "waiting {0:.0f}".format((seconds_to_run-runTime)/60)+"mins..."
		print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		time.sleep(seconds_to_run-runTime)
	else:
		#log("waiting 0 minutes............................................")
		print "waiting 0 minutes..."


