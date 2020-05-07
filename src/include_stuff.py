import sys

# used to display progress bar on terminal
def progress_bar(count, total, suffix=''):
	bar_len = 10
	filled_len = int(round(bar_len * count / float(total)))

	percents = round(100.0 * count / float(total), 1)
	bar = '#' * filled_len + '-' * (bar_len - filled_len)

	#sys.stdout.write('\r[%s] %s%s (%s)' % (bar, percents, '%', suffix))
	sys.stdout.write('\x1b[0;33m \r[%s] %s%s \x1b[0m' % (bar, percents, '%'))
	sys.stdout.flush()
	if percents == 100:
		print ""
# used to display progress bar on terminal
def progress_bar_full(count, total, suffix=''):
	bar_len = 10
	filled_len = int(round(bar_len * count / float(total)))

	percents = round(100.0 * count / float(total), 1)
	bar = '#' * filled_len + '-' * (bar_len - filled_len)

	sys.stdout.write('\x1b[0;33m \r[%s] %s%s (%s) \x1b[0m' % (bar, percents, '%', suffix))
	#sys.stdout.write('\x1b[0;33m \r[%s] %s%s \x1b[0m' % (bar, percents, '%'))
	sys.stdout.flush()
	if percents == 100:
		print ""
