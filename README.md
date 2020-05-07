# Phishalytics #

Codebase for <b>Phish</b>alytics: the measurement infrastructure system I designed and built to research phishing and malware attacks on Twitter during my PhD studies at Royal Holloway, University of London.

## Overview ##

- [Screenshot](#screenshot "Screenshot")
- [Services](#services "Services")
- [Publications](#publications "Publications")

## Screenshot ##
![phishalytics terminal screenshot](https://github.com/sjbell/phishalytics/blob/master/terminal-screenshot.png?raw=true)

Interacting with <b>Phish</b>alytics is carried out via an SSH connection in a terminal window. The server-side interface uses GNU Screen. The Screenshot above shows <b>Phish</b>alytics during one of our measurement studies. The layout consists of 18 windows; 16 small and 2 large. The two larger windows display a development area and the system monitor (<i>htop</i> command showing CPU and RAM usage, top processes, etc). The 16 smaller windows, labelled s1 to s16, contain the following:

- s1:  [twitter_stream.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_stream.py "twitter_stream.py") - Twitter filter stream (tweets containing URLs). Each character in this window represents the following:
  - <b>#</b> the tweet that is about to be processed is a retweet
  - <b>.</b> tweet received from Twitter Stream API for processing
  - <b>!</b> for each URL within this single tweet
  - <b>+</b> tweet saved to our system's database

- s2: [twitter_stream_sample.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_stream_sample.py "twitter_stream_sample.py") - Twitter sample stream (same characters as above)
- s3: [update_gsb.py](https://github.com/sjbell/phishalytics/blob/master/src/update_gsb.py "update_gsb.py") - Update our local copy of GSB blacklist
- s4: [update_phishtank_and_openphish.py](https://github.com/sjbell/phishalytics/blob/master/src/update_phishtank_and_openphish.py "update_phishtank_and_openphish.py") - Update our local copies of PT and OP blacklists
- s5: [twitter_gsb_lookup_fast.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_gsb_lookup_fast.py "twitter_gsb_lookup_fast.py") - Fast Twitter GSB URL lookup system
- s6: [twitter_gsb_lookup.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_gsb_lookup.py "twitter_gsb_lookup.py") - Comprehensive Twitter GSB URL lookup system
- s7: phishing_blacklist_lookup_system_comprehensive-phishing_5.py - Slow (comprehensive) OP and PT Twitter URL lookup system
- s8: phishing_blacklist_lookup_system_fast-phishing_5.py - Fast OP and PT Twitter URL lookup system
- s9: lookup_gglsbl_timesamps-phishing_5.py - GSB timestamp lookup system
- s10: twitter-search-api-lookup-phishing_5.py - Twitter search API lookup system
- s11: trending-hash-tags-phishing_5.py - Retrieve and save current trending hashtags from Twitter API
- s12: post-twitter-collection-processing-phishing_5.py - Post Twitter collection processing (for metadata such as: lookup redirections chains, num URL hops, landing page URL, calculate Levenshtein distance, determine if trending hashtags used, etc)
- s13: compare_gsb_updates-phishing_5.py - Calculate, update, and compare GSB sizes
- s14: Not currently being used for the present study
- s15: check-everything-is-working-phishing_5.py - Check everything is functioning correctly, check all feeds are live, etc. Send error notification emails to authors
- s16: trending-hash-tags-london.py - Currently trending hashtags on Twitter for London

## Services ##

Service name  | Description | File
------------- | ------------- | ------------- 
Twitter Stream |  Stream public tweets that contain URLs via Twitter's [filter stream API](https://developer.twitter.com/en/docs/tweets/filter-realtime/api-reference/post-statuses-filter "filter stream API") and save into local database |   [twitter_stream.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_stream.py "twitter_stream.py")
Twitter Sample Stream  | Stream a small random sample of all public tweets via Twitter's [sample stream API](https://developer.twitter.com/en/docs/tweets/sample-realtime/overview/get_statuses_sample "sample stream API") and save into local database | [twitter_stream_sample.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_stream_sample.py "twitter_stream_sample.py")
Update GSB | Update our local copy of GSB blacklist using [Safe Browsing Update API (v4)](https://developers.google.com/safe-browsing/v4/update-api "Safe Browsing Update API (v4)") | [update_gsb.py](https://github.com/sjbell/phishalytics/blob/master/src/update_gsb.py "update_gsb.py")
Update Phishtank and Openphish | Update our local copies of Phishtank and Openphish blacklists | [update_phishtank_and_openphish.py](https://github.com/sjbell/phishalytics/blob/master/src/update_phishtank_and_openphish.py "update_phishtank_and_openphish.py")
Comprehensive Twitter GSB Lookup | Looks up all tweeted URLs in GSB blacklist since measurement experiment began. Gets progresively slower as experiment duration increases | [twitter_gsb_lookup.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_gsb_lookup.py "twitter_gsb_lookup.py")
Fast Twitter GSB Lookup | Looks up all tweeted URLs in GSB blacklist from past 24 hours (approx. 1 million) | [twitter_gsb_lookup_fast.py](https://github.com/sjbell/phishalytics/blob/master/src/twitter_gsb_lookup_fast.py "twitter_gsb_lookup_fast.py")

## Publications ##

Research papers that feature results obtained with <b>Phish</b>alytics:

<b>Winner of the Best Paper and Best Student Paper awards:</b><br />BELL, S., AND KOMISARCZUK, P. "Measuring the Effectiveness of Twitter’s URL Shortener (t.co) at Protecting Users from Phishing and Malware Attacks". In <i>Proceedings of the Australasian Computer Science Week Multiconference (2020)</i>. <a href="https://dl.acm.org/doi/abs/10.1145/3373017.3373019" target="_new">Link to paper.</a>

BELL, S., AND KOMISARCZUK, P. "An Analysis of Phishing Blacklists: Google Safe Browsing, OpenPhish, and PhishTank". In <i>Proceedings of the Australasian Computer Science Week Multiconference (2020)</i>. <a href="https://dl.acm.org/doi/abs/10.1145/3373017.3373020" target="_new">Link to paper.</a>

BELL, S., PATERSON, K., AND CAVALLARO, L. "Catch Me (On Time) If You Can: Understanding the Effectiveness of Twitter URL Blacklists". <i>arXiv preprint arXiv:1912.02520 (2019)</i>. <a href="https://arxiv.org/abs/1912.02520" target="_new">Link to paper.</a>

