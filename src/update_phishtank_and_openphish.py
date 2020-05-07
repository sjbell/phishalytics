import urllib
import requests 
import shutil
import json
import time
import datetime
import dateutil.parser
import MySQLdb as mdb
import sys

with open('config.json') as data_file:    
	config = json.load(data_file)


def formatURL(url):
	new_url =  url.rstrip('//').lower()[0:1000]

	return new_url

def updatePT():
	cur = con.cursor()
	# download latest version of PhishTank json file
	print "downloading latest version of PhishTank json file... (phishtank-latest.json)"
	url = "http://data.phishtank.com/data/config['phishtank-api']['key']/online-valid.json"

	# these 2 lines will follow 302 redirects as script was dying here (bug fixed on 24 Aug 2017)
	page = urllib.urlopen(url)
	url = page.geturl() 

	testfile = urllib.URLopener()
	testfile.retrieve(url, "phishtank-latest.json")
	
	# save URLs to db
	print ("saving new URLs to DB...")
	with open('phishtank-latest.json') as data_file:    
	    json_data = json.load(data_file)

	new_urls_counter = 0
	existing_urls_counter = 0
	url_dict = {}

	print "length of json file: ",len(json_data)

	for p in json_data:
		url =  formatURL(p["url"])
		submission_time = dateutil.parser.parse(p["submission_time"]).strftime("%Y-%m-%d %H:%M:%S")
		verification_time = dateutil.parser.parse(p["verification_time"]).strftime("%Y-%m-%d %H:%M:%S")
		url_dict[url] = (submission_time, verification_time)

	for k,v in url_dict.iteritems():
		url = k
		submission_time = v[0]
		verification_time = v[1]

		sql = "INSERT INTO phish_tank_urls_5(url, pt_submission_time, pt_verification_time) VALUES(%s, %s, %s)"
		try:
			cur.execute(sql, (url, submission_time, verification_time ))
			last_id = cur.lastrowid
			new_urls_counter += 1
		except Exception as e:
			existing_urls_counter += 1
			if e[0] != 1062:
				print e
	
	print "PhishTank blacklist stats:"
	print "unique URLs in json file:",len(url_dict)
	print "new URLs added to db:", new_urls_counter
	print "URLs already in db:", existing_urls_counter
	print "----\n"

	with con: 
		cur = con.cursor()
		sql = "INSERT INTO pt_op_update_log_5(blacklist, total_urls_in_json, total_unique_urls_in_json, total_new_urls_added, urls_already_in_db) VALUES(%s, %s, %s, %s, %s)"
		cur.execute(sql, ("PT", len(json_data), len(url_dict), new_urls_counter, existing_urls_counter ))

def updateOP():
	cur = con.cursor()
	# download latest version of PhishTank json file
	print "downloading latest version of OpenPhish json file... (openphish-latest.json)"
	r = requests.get('https://openphish.com/prvt-intell/', auth=(config['openphish-api']['username'], config['openphish-api']['password']), stream=True)
	print r.status_code
	print r.headers['content-type']
	with open('openphish-latest.json', 'wb') as f:
		shutil.copyfileobj(r.raw, f)
	
	openphish = []
	op_url_dict = {}
	new_urls_counter = 0
	existing_urls_counter =0

	for line in open('openphish-latest.json', 'r'):
		openphish.append(json.loads(line))

	print "length of json file:",len(openphish)

	for p in openphish:
		url =  formatURL(p["url"])
		discover_time = dateutil.parser.parse(p["discover_time"]).strftime("%Y-%m-%d %H:%M:%S")
		op_url_dict[url] = (discover_time, )

	for k,v in op_url_dict.iteritems():
		url = k
		discover_time = v[0]

		
		sql = "INSERT INTO open_phish_urls_5(url, op_discover_time) VALUES(%s, %s)"
		try:
			cur.execute(sql, (url, discover_time ))
			last_id = cur.lastrowid
			new_urls_counter += 1
		except Exception as e:
			existing_urls_counter += 1
			if e[0] != 1062:
				print e

	print "OpenPhish stats:"
	print "unique URLs in json:",len(op_url_dict)
	print "new URLs added:", new_urls_counter
	print "not new URLs:", existing_urls_counter

	sql = "INSERT INTO pt_op_update_log_5(blacklist, total_urls_in_json, total_unique_urls_in_json, total_new_urls_added, urls_already_in_db) VALUES(%s, %s, %s, %s, %s)"
	cur.execute(sql, ("OP", len(openphish), len(op_url_dict), new_urls_counter, existing_urls_counter ))
	cur.close()

while True:
	try:
		con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8')
		con.autocommit(True)
		updatePT()
		updateOP()
	except:
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
		print "We have an error:", sys.exc_info()[1]
		print "waiting 90 seconds"
		time.sleep(90)
	print "fin. wait 1 hour"
	print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	con.close()
	time.sleep(3600)

