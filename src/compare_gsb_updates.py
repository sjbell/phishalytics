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


gsb_dicts_list = []

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

# begin main while loop
while True:

	con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8')
	con.autocommit(True)
	cur = con.cursor()

	mainStart = time.time()
	
	
	#update GSB dataset
	#start = time.time()
	try:


		from gglsbl4 import SafeBrowsingList
		sbl4 = SafeBrowsingList(config['gsb-api']['key'])
		#print "Importing gsb..."
		gsb4 = importGSBHashPrefixes(sbl4)
		#print "Converting gsb to dict..."
		gsb_dict4 = convertGSBToDict(gsb4)
		gsb_count_str4 = "gglsbl 4: {:,}".format(len(gsb_dict4))
		#timestamp_str = "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())



		from gglsbl3 import SafeBrowsingList
		sbl3 = SafeBrowsingList(config['gsb-api']['key'])
		#print "Importing gsb..."
		gsb3 = importGSBHashPrefixes(sbl3)
		#print "Converting gsb to dict..."
		gsb_dict3 = convertGSBToDict(gsb3)
		gsb_count_str3 = "gglsbl 3: {:,}".format(len(gsb_dict3))



		
		timestamp_str = "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
		print timestamp_str + "\n"+gsb_count_str3+"\n"+ gsb_count_str4+"\n"

		#print type(len(gsb_dict3))

		# insert timestamps into db
		sql = "INSERT INTO gsb_update_log_5(num_urls_gglsbl3, num_urls_gglsbl4) VALUES(%s, %s)"
		cur.execute(sql, (len(gsb_dict3), len(gsb_dict4)))
		#gsb_dicts_list.append(gsb_dict)

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
	#print "time taken to complete whole script: {0:.2f}".format(mainEnd-mainStart)+" seconds ({0:.2f}".format((mainEnd-mainStart)/60)+" minutes)"
	runTime = (mainEnd-mainStart)
	
	# this bit ensures code runs every x seconds even if script takes y seconds to run
	repeat_every_seconds = 600
	if runTime < repeat_every_seconds:
		#print runTime
		#print "waiting {0:.2f}".format((repeat_every_seconds-runTime))+" seconds..."
		#print datetime.datetime.now()
		time.sleep(repeat_every_seconds-runTime)
	#else:
		#print "waiting 0 minutes..."

	#print "waiting 5 minutes"
	#time.sleep(300)

