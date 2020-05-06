# Phishalytics #

Codebase for <b>Phish</b>alytics: the measurement infrastructure system I designed and built to research phishing and malware attacks on Twitter during my PhD studies at Royal Holloway, University of London

## Screenshot ##
![phishalytics terminal screenshot](https://github.com/sjbell/phishalytics/blob/master/terminal-screenshot.png?raw=true)

Interacting with <b>Phish</b>alytics is carried out via an SSH connection in a terminal window. The server-side interface uses GNU Screen. The Screenshot above shows <b>Phish</b>alytics during one of our measurement studies. The layout consists of 18 windows; 16 small and 2 large. The two larger windows display a development area and the system monitor (<i>htop</i> command showing CPU and RAM usage, top processes, etc). The 16 smaller windows, labelled s1 to s16, contain the following:

- s01: Twitter filter stream (tweets containing URLs). Each character in this window represents the following:
  - ``\#'' the tweet that is about to be processed is a retweet
  - ``.'' tweet received from Twitter Stream API for processing
  - ``!'' for each URL within this single tweet
  - ``+'' tweet saved to our system's database

- s02: Twitter sample stream (same characters as above)
- s03: Update our local copy of GSB blacklist
- s04: Update our local copies of PT and OP blacklists
- s05: Fast GSB Twitter URL lookup system
- s06: Slow (comprehensive) GSB Twitter URL lookup system
- s07: Slow (comprehensive) OP and PT Twitter URL lookup system
- s08: Fast OP and PT Twitter URL lookup system
- s09: GSB timestamp lookup system
- s10: Twitter search API lookup system
- s11: Retrieve and save current trending hashtags from Twitter API
- s12: Post Twitter collection processing (for metadata such as: lookup redirections chains, num URL hops, landing page URL, calculate Levenshtein distance, determine if trending hashtags used, etc)
- s13: Calculate, update, and compare GSB sizes
- s14: Not currently being used for the present study
- s15: Check everything is functioning correctly, check all feeds are live, etc. Send error notification emails to authors
- s16: Currently trending hashtags on Twitter for London
