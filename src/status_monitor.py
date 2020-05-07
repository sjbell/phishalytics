import time
import sys
import os
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

#from sqlite3 import IntegrityError
#from gglsbl3.protocol import URL

with open('config.json') as data_file:    
	config = json.load(data_file)


def checkTwitterStreamFilter():
	filename = "twitter_stream_4.1-phishing_5.py"
	cur.execute("SELECT date_added from tweets_5 ORDER BY id DESC LIMIT 1")
	rows = cur.fetchall()
	result = 0;
	for row in rows:
		result = row[0];
	test = result > (datetime.datetime.now() - datetime.timedelta(seconds=30))
	
	if not test:
		reportError(filename, "No entry into table tweets_5 in last 30 seconds. Should be a constant stream")
	return test

# if no tweets in over 10 minutes then send me an email every 10 minutes until it's fixed
def checkTwitterStreamFilterMajor():
	filename = "twitter_stream_4.1-phishing_5.py"
	cur.execute("SELECT date_added from tweets_5 ORDER BY id DESC LIMIT 1")
	rows = cur.fetchall()
	result = 0;
	for row in rows:
		result = row[0];
	test = result > (datetime.datetime.now() - datetime.timedelta(seconds=600))
	
	if not test:
		reportMajorError(filename, "No entry into table tweets_5 in last 10 Minutes. Should be a constant stream")
	return test

def checkTwitterStreamSample():
	filename = "twitter_stream_sample-phishing_5.py"
	cur.execute("SELECT date_added from tweets_sample_stream_5 ORDER BY id DESC LIMIT 1")
	rows = cur.fetchall()
	result = 0;
	for row in rows:
		result = row[0];
	test =  result > (datetime.datetime.now() - datetime.timedelta(seconds=30))

	if not test:
		reportError(filename, "No entry into table tweets_sample_stream_5 in last 30 seconds. Should be a constant stream")
	return test

def checkCompareGSBUpdates():
	filename = "compare_gsb_updates-phishing_5.py"
	
	# check gsb_update_log_5 updated in last 10 minutes
	cur.execute("SELECT date from gsb_update_log_5 ORDER BY id DESC LIMIT 1")
	rows = cur.fetchall()
	result = 0;
	for row in rows:
		result = row[0];
	gsb_update_logged = result > (datetime.datetime.now() - datetime.timedelta(minutes=10))

	# check last 4 updates aren't the same (should be updated every 30 minutes)
	cur.execute("SELECT num_urls_gglsbl4 from gsb_update_log_5 ORDER BY id DESC LIMIT 4")
	rows = cur.fetchall()
	results = [];
	for row in rows:
		results.append(row[0]);
	gsb_updating = not all(x==results[0] for x in results) # check all items in results list aren't the same. Logic here is that if gsb gets updated every 30 minutes then 4 rows (with each row updated every 10 minuets) should not return the same figure for num_urls_gglsbl[3/4]

	if not gsb_update_logged:
		reportError(filename, "No entry in db for more than 10 minues. Should be updating every 10 minutes")
	if not gsb_updating:
		reportError(filename, "Last 4 entries in gsb_update_log_5 are all the same. Should change on every fourth update (updated every 10 minutes, gsb updated every 30 minutes. fourth update = 40 minutes")

	return gsb_update_logged & gsb_updating

def checkUpdateGSB():
	filename = "update_gsb.py"
	file = "/tmp/gsb_v4.db"
	c_time = datetime.datetime.strptime(time.ctime(os.path.getctime(file)), "%a %b %d %H:%M:%S %Y")
	test = c_time >= (datetime.datetime.now() - datetime.timedelta(minutes=10))

	if not test:
		reportError(filename, "file /tmp/gsb_v4.db not updated mroe than 10 minutes ago. Should be being updated every 10 minutes by update_gsb.py")
	return test & checkCompareGSBUpdates()


def checkUpdatePhishTankOpenPhish():
	filename = "update_phishtank_and_openphish-phishing_5.py"

	file = "openphish-latest.json"
	op_c_time = datetime.datetime.strptime(time.ctime(os.path.getctime(file)), "%a %b %d %H:%M:%S %Y")
	
	file2 = "phishtank-latest.json"
	pt_c_time = datetime.datetime.strptime(time.ctime(os.path.getctime(file2)), "%a %b %d %H:%M:%S %Y")
	
	test = ((pt_c_time >= (datetime.datetime.now() - datetime.timedelta(minutes=60))) & (op_c_time >= (datetime.datetime.now() - datetime.timedelta(minutes=60))))
	
	if not test:
		reportError(filename, "Either "+file+" or "+file2+" hasn't downloaded succesfully in over 60 minutes. Should be every hour")
	return test



def reportError(file, description):

	email_sent = 0

	# check when last email was sent:
	cur.execute("SELECT COUNT(*) as num from error_reports_5 WHERE file = %s AND date_reported > DATE_SUB(NOW(), INTERVAL 6 HOUR)", (file,))
	rows = cur.fetchall()
	result = 0;
	for row in rows:
		result = int(row[0]);

	# send email as error reported more than 6 hours ago:
	if result == 0: 
		from send_email import sendAdminAlert
		script_file_name = os.path.basename(__file__)
		sendAdminAlert("Problem with script: "+file, 
		"There's been an issue...\n\nProblem with script: "+file+"\nDescription of problem: "+description+"\n\nDetected by "+script_file_name)
		email_sent = 1
		
	# report error in db:
	sql = "INSERT INTO error_reports_5(file, description, email_sent) VALUES(%s, %s, %s)"
	cur.execute(sql, (file, description, email_sent))
	con.commit()

# send email regardless of when last error email sent:
def reportMajorError(file, description):
	from send_email import sendAdminAlert
	script_file_name = os.path.basename(__file__)
	sendAdminAlert("Problem with script: (major error) "+file, 
	"There's been an issue...\n\nProblem with script: "+file+"\nDescription of problem: "+description+"\n\nDetected by "+script_file_name)
	email_sent = 1
		
	# report error in db:
	sql = "INSERT INTO error_reports_5(file, description, email_sent) VALUES(%s, %s, %s)"
	cur.execute(sql, (file, description, email_sent))
	con.commit()

def parseResult(result):
	if result:
		return "\x1b[0;32mOK\x1b[0m"
	else:
		return "\x1b[0;31mX\x1b[0m"

# begin main while loop
while True:


	mainStart = time.time()
	print "###start\n"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8')
		con.autocommit(True)
		cur = con.cursor()

		print parseResult(checkTwitterStreamFilter()) + " Twitter Stream"
		print parseResult(checkTwitterStreamSample()) + " Twitter Sample"
		print parseResult(checkUpdateGSB()) + " Update GSB"
		print parseResult(checkUpdatePhishTankOpenPhish()) + " Update PT+OP"
		#print parseResult(checkCompareGSBUpdates()) + " Log GSB Updates"
		checkTwitterStreamFilterMajor()

	except:
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
		#print "runtime: {0:.0f}".format(runTime)+"secs"
		#print "\x1b[0;35mwait {0:.0f}".format((repeat_every_seconds-runTime))+" secs...\x1b[0m"
		print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		time.sleep(repeat_every_seconds-runTime)
