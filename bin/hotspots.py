#!/usr/bin/python
#
# hotspots.py - examine a set of git commits, and indicate an area
#   where a lot of work is being conducted 

import sys
import os
import commands

def usage():
	print """usage: %s <git_log_args>
This program shows "hotspot areas" for a selected set of commits
in the current git repository

 -h        Show this usage
""" % (os.path.basename(sys.argv[0]))
	sys.exit(0)

# get a list of areas to collect information for
# get a complexity measure for each area
# show a treemap, segmented by  ?
def get_complexity(git_args, area):
	# gather the commit data
	cmd="complexity %s -s %s" % (git_args, area)
	print "cmd=", cmd
	(rcode, result) = commands.getstatusoutput(cmd)
	#print "result=", result
	complexity = "0"
	for line in result.split('\n'):
		if line.startswith("@@@"):
			(ats, complexity, rest) = line.split(None, 2)
			break
	return int(complexity)


def main():
	if '-h' in sys.argv:
		usage()

	git_args = sys.argv[1:]
	git_args_str = " ".join(git_args)

	# yuk - this is hand-tuned
	area_list = ["arch", 
		"arch/arm", "arch/arm/boot", "arch/arm/configs",
		"arch/arm/mach-msm", "arch/arm/kernel",
#		"arch/arm/lib", "arch/arm/mm",
#		"arch/arm/vfp", "arch/arm/oprofile", 
		"block", "crypto", "drivers", "firmware", "fs",
		"include", "init", "ipc", "kernel", "lib", "mm", "net",
		"samples", "scripts", "security", "sound", "tools", "usr",
		"virt",
		"drivers/block",
		"drivers/bluetooth",
#		"drivers/cdrom",
		"drivers/char",
		"drivers/clk",
		"drivers/cpufreq",
		"drivers/cpuidle",
#		"drivers/dca",
		"drivers/devfreq", 
		"drivers/gpio",
		"drivers/hid",
		"drivers/hwmon",
		"drivers/input", 
		"drivers/input/misc", 
		"drivers/input/touchscreen", 
		"drivers/leds", 
		"drivers/platform",
		"drivers/power",
		"drivers/staging",
		"drivers/tty",
		"drivers/usb",
		"drivers/video",] 

	areas = {}
	for area in area_list:
		complexity = get_complexity(git_args_str, area)
		print "area=", area, "complexity=", complexity
		# should form this into a treemap structure
		# which is nested tuples
		areas[area] = complexity

	# print out domains sorted by count of commits
	print "area                  complexity" 
	area_list = areas.items()
	area_list.sort(key=lambda x: x[1])
	for a_tuple in area_list: 
		print "%-24s %6d" % (a_tuple[0], a_tuple[1])


	#author_count = [[a, len(authors[a])] for a in authors]
	#author_count.sort(key=lambda x: x[1])
	#for a_tuple in author_count:
	#	# print count, author
	#	#print a_tuple[1], a_tuple[0]
	#	pass

	# this is where I would create a treemap, if I had code
	# lying around for this 

if __name__=="__main__":
	main()
