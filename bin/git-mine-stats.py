#!/usr/bin/env python
#
# git-mine-stats.py - collect commit stats from git logs using a set of
# user-specific filters in loops.
#
# This is designed to get stats for multiple "groups", over a set of conditions
# both the "groups" and the "conditions" are user-configurable
#
# output should be in CSV format
#

import sys
import os
import commands

def usage():
	print """usage: %s <git_log_args>
This program produces information for a set of groups
for a particular set of conditions for commits
in the current git repository

It is intended to be modified to support data-mining
of git repositories.

Modify the base_command, group_list and cond_list
in the program, to generate the data.  The format
output can be fed directly into a spreadsheet program,
to generate charts and graphs or do other data analysis.

 -h        Show this usage
 -n <num>  Limit output to top <num> domains
""" % (os.path.basename(sys.argv[0]))
	sys.exit(0)


# each command should yield a single number
# include %(cond) and %(group) somewhere in the string
base_command = "git log v3.4.. --format=%%ae %(cond)s %(group)s | wc -l"

# each tuple has ("label", "filter string")
group_list = [ 
	("google", "| egrep google\|android"),
	("qualcomm", "| egrep codeaurora"),
	("sonymobile", "| egrep sony[me]"),
	("other", "| egrep -v google\|android | egrep -v codeaurora | egrep -v sony[me] | egrep -v codeaurora | egrep -v lnxbuild"),
	("month total", "| egrep -v lnxbuild"),
]
	
# each tuple has ("label", "conditional string")
# this should fit into the base_command in a way that selects unique
# "buckets" of data from the git logs
cond_list = [
	("Jan 2012", "--since=2012-01-01 --until=2012-02-01"),
	("Feb 2012", "--since=2012-02-01 --until=2012-03-01"),
	("Mar 2012", "--since=2012-03-01 --until=2012-04-01"),
	("Apr 2012", "--since=2012-04-01 --until=2012-05-01"),
	("May 2012", "--since=2012-05-01 --until=2012-06-01"),
	("Jun 2012", "--since=2012-06-01 --until=2012-07-01"),
	("Jul 2012", "--since=2012-07-01 --until=2012-08-01"),
	("Aug 2012", "--since=2012-08-01 --until=2012-09-01"),
	("Sep 2012", "--since=2012-09-01 --until=2012-10-01"),
	("Oct 2012", "--since=2012-10-01 --until=2012-11-01"),
	("Nov 2012", "--since=2012-11-01 --until=2012-12-01"),
	("Dec 2012", "--since=2012-12-01 --until=2013-01-01"),

	("Jan 2013", "--since=2013-01-01 --until=2013-02-01"),
	("Feb 2013", "--since=2013-02-01 --until=2013-03-01"),
	("Mar 2013", "--since=2013-03-01 --until=2013-04-01"),
	("Apr 2013", "--since=2013-04-01 --until=2013-05-01"),
	("May 2013", "--since=2013-05-01 --until=2013-06-01"),
	("Jun 2013", "--since=2013-06-01 --until=2013-07-01"),
	("Jul 2013", "--since=2013-07-01 --until=2013-08-01"),
	("Aug 2013", "--since=2013-08-01 --until=2013-09-01"),
	("Sep 2013", "--since=2013-09-01 --until=2013-10-01"),
	("Oct 2013", "--since=2013-10-01 --until=2013-11-01"),
	("Nov 2013", "--since=2013-11-01 --until=2013-12-01"),
	("Dec 2013", "--since=2013-12-01 --until=2014-01-01"),

	("Jan 2014", "--since=2014-01-01 --until=2014-02-01"),
	("Feb 2014", "--since=2014-02-01 --until=2014-03-01"),
	("Mar 2014", "--since=2014-03-01 --until=2014-04-01"),
	("Apr 2014", "--since=2014-04-01 --until=2014-05-01"),
	("May 2014", "--since=2014-05-01 --until=2014-06-01"),
	("Jun 2014", "--since=2014-06-01 --until=2014-07-01"),
	("Jul 2014", "--since=2014-07-01 --until=2014-08-01"),
	("Aug 2014", "--since=2014-08-01 --until=2014-09-01"),
	("Sep 2014", "--since=2014-09-01 --until=2014-10-01"),
	("Oct 2014", "--since=2014-10-01 --until=2014-11-01"),
	("Nov 2014", "--since=2014-11-01 --until=2014-12-01"),
	("Total", "--since=2012-01-01 --until=2015-01-01"),
]

# NOTE: git doesn't handle future dates correctly

def main():
	if '-h' in sys.argv:
		usage()

	count_limit = 99999
	if '-n' in sys.argv:
		i = sys.argv.index('-n')
		count_limit = int(sys.argv[i+1])
		del sys.argv[i+1]
		del sys.argv[i]

#	git_args = sys.argv[1:]
#	git_args_str = " ".join(git_args)

	# print the first line of labels
	print "groups,",
	for cond_tuple in cond_list:
		cond_label = cond_tuple[0]
		print cond_label+",",
	print
	sys.stdout.flush()

	#print "<now for the data>"
	# gather the data
	for group_tuple in group_list:
		group_label = group_tuple[0]
		group = group_tuple[1]
		print group_label+",",
		for cond_tuple in cond_list:
			cond = cond_tuple[1]
			cmd= base_command % locals()
			#print "<cmd='%s'>" % cmd
			(rcode, result) = commands.getstatusoutput(cmd)
			print result.strip()+",",
			sys.stdout.flush()
		print
		sys.stdout.flush()

if __name__=="__main__":
	main()
