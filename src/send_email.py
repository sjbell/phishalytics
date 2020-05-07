import smtplib
import datetime

def getTS():
  return ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))

def sendAdminAlert(subject, message):
	sender = 'you@organisation.com'
	receivers = ['recipient@organisation.com']

	message = """From: Name <you@organisation.com>
To: Name <recipient@organisation.com>
Subject: """+subject+"""

"""+message+"""

Reported: """+str(getTS())+"""
"""

	try:
		smtpObj = smtplib.SMTP('localhost')
		smtpObj.sendmail(sender, receivers, message)         
		#print "Successfully sent error email"
	except smtplib.SMTPException as e:
		print "Error: unable to send error email"
		print e

# sendAdminAlert("This is a test alert", "Contents of test alert go here...")
