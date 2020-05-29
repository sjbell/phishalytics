import certstream
import tqdm
import entropy
import MySQLdb as mdb
import MySQLdb.cursors
import sys
import json

with open('config.json') as data_file:    
    config = json.load(data_file)

log_suspicious = 'suspicious_domains.log'

suspicious_keywords = [
    'login',
    'log-in',
    'account',
    'verification',
    'verify',
    'support',
    'activity',
    'security',
    'update',
    'authentication',
    'authenticate',
    'wallet',
    'alert',
    'purchase',
    'transaction',
    'recover',
    'live',
    'office'
    ]

highly_suspicious = [
    'paypal',
    'paypol',
    'poypal',
    'twitter',
    'appleid',
    'gmail',
    'outlook',
    'protonmail',
    'amazon',
    'facebook',
    'microsoft',
    'windows',
    'cgi-bin',
    'localbitcoin',
    'icloud',
    'iforgot',
    'isupport',
    'kraken',
    'bitstamp',
    'bittrex',
    'blockchain',
    '.com-',
    '-com.',
    '.net-',
    '.org-',
    '.gov-',
    '.gouv-',
    '-gouv-'
    ]

suspicious_tld = [
    '.ga',
    '.gq',
    '.ml',
    '.cf',
    '.tk',
    '.xyz',
    '.pw',
    '.cc',
    '.club',
    '.work',
    '.top',
    '.support',
    '.bank',
    '.info',
    '.study',
    '.party',
    '.click',
    '.country',
    '.stream',
    '.gdn',
    '.mom',
    '.xin',
    '.kim',
    '.men',
    '.loan',
    '.download',
    '.racing',
    '.online',
    '.ren',
    '.gb',
    '.win',
    '.review',
    '.vip',
    '.party',
    '.tech',
    '.science'
    ]

#pbar = tqdm.tqdm(desc='certificate_update', unit='cert')
#pbar = tqdm.tqdm(desc='CU', unit='cs', bar_format='{r_bar}{bar}{l_bar}')

def score_domain(domain):
    """Score `domain`.

    The highest score, the most probable `domain` is a phishing site.

    Args:
        domain (str): the domain to check.

    Returns:
        int: the score of `domain`.
    """
    score = 0
    for tld in suspicious_tld:
        if domain.endswith(tld):
            score += 20
    for keyword in suspicious_keywords:
        if keyword in domain:
            score += 25
    for keyword in highly_suspicious:
        if keyword in domain:
            score += 60
    score += int(round(entropy.shannon_entropy(domain)*50))

    # Lots of '-' (ie. www.paypal-datacenter.com-acccount-alert.com)
    if 'xn--' not in domain and domain.count('-') >= 4:
        score += 20
    return score

# used to display progress bar on terminal
x = 0
def progress_bar():
    global x
    x += 1

    sys.stdout.write('\r%s ' % ("{:,}".format(x)))
    sys.stdout.flush()

def display_message(message):
    sys.stdout.write('\n\r%s\n' % (message))
    sys.stdout.flush()

def callback(message, context):
    """Callback handler for certstream events."""
    if message['message_type'] == "heartbeat":
        return

    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']

        for domain in all_domains:

            sql = "INSERT IGNORE INTO certstream_domains_5(domain) VALUES(%s)"
            cur.execute(sql, (domain,))
        
            #pbar.update(1)
            progress_bar()
            #print "listening..."
            score = score_domain(domain)
            if score > 75:

                sql = "INSERT IGNORE  INTO certstream_suspicious_5(domain, score) VALUES(%s,%s)"
                cur.execute(sql, (domain,score))
        
                display_message(
                    "\033[91mSus: "
                    "\033[4m{}\033[0m\033[91m (s={})\033[0m".format(domain[0:8], score))
                with open(log_suspicious, 'a') as f:
                    f.write("{}\n".format(domain))
            elif score > 65:

                sql = "INSERT IGNORE  INTO certstream_potential_5(domain, score) VALUES(%s,%s)"
                cur.execute(sql, (domain,score))

                display_message(
                    "Pot: "
                    "\033[4m{}\033[0m\033[0m (s={})".format(domain[0:8], score))

while True:
    try:
        con = mdb.connect(config['mysql']['host'], config['mysql']['username'], config['mysql']['password'], config['mysql']['database_5'],charset='utf8',cursorclass = mdb.cursors.SSCursor)
        con.autocommit(True)
        cur = con.cursor()
        certstream.listen_for_events(callback)
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
        
    print "waiting 60 secs..."
    time.sleep(60)

