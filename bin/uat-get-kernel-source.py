#!/usr/bin/python
#
# uat-get-kernel-source - retrieve the kernel source from a given url
#
# to do:
#  - download source
#  - unpack source tar
#  - do type-specific source fixups
#
import os, sys
from urlparse import urlparse
import urllib2
import copy

# Here's some important data
dev_table_wiki_page="http://elinux.org/Phones_Processors_and_Download_Sites" 
dev_table_raw_url="http://elinux.org/index.php?title=Phones_Processors_and_Download_Sites&action=raw" 
dev_key_field="Phone"
dev_url_field="Source Url"

source_types = ["tarfile", "sony", "mediatek", "samsung", "asustarzip"]

def vprint(verbose, msg):
	if verbose:
		print msg
def usage():
	prog_name = os.path.basename(sys.argv[0])
	print """Usage: %s [options] [-d <device>|-u <URL>]

Retrieve the kernel source for the indicated device (or from the specified
URL), and unpack it.   Either the device (from the wiki page) or a URL must
be specified.

  -h, --help      Show this usage help
  -o <output_dir> Put the kernel source in <output_dir>.  If not specified,
                  the program uses the directory 'uat-kernel', if a URL is
                  used, or the device name (with spaces converted to
                  underscores) if a device is specified.
  -t <type>       Specify the type of kernel source.  If not specified,
                  use a type of 'tarfile'.  Possible values are:
                  'tarfile', 'sony', 'mediatek', 'samsung', "asusziptar"
  -u <URL>        Download the source package from the indicated URL.
  -d <device>     Find the devices listed on the device page
  -l              List devices in the device wiki table

This tool uses data from a table on the following wiki page:
  %s
""" % (prog_name, dev_table_wiki_page)
	sys.exit(1)

# return a dictionary of "records" for a mediawiki table
# the key is the indicated field.  In case of duplicates, the
# last one in the table is used.
# the URL should be in http://example.com/index.php?title=Page_Name&action=raw
# the key_field argument should match the string in one of header cells
# if field_names is specified, then the table is assumed not to have
# a header row, and those names are used for the record fields in place of
# the field (column) names in the first row of the wiki table.
def parse_mediawiki_table(url, key_field, field_names=[]):
	page = urllib2.urlopen(url)
	lines = page.readlines()
	page.close()

	# parse the first table found
	# split into rows, then convert to records
	in_table = 0
	rows = []
	row = []
	for line in lines:
		#print line
		#print "row=", row

		# skip all lines before the table start
		if not in_table and not line.startswith("{|"):
			continue

		# mediawiki allows spaces before table markup elements
		line = line.strip()

		if line.startswith("{|"):
			in_table = 1
			row_num = 0
			in_row = 1
			row = []
			continue

		if line.startswith("|}"):
			rows.append(row[:])
			row_num += 1
			break

		if line.startswith("|-"):
			if row:
				# save current row
				rows.append(row[:])
				row_num += 1
				row = []
			continue
		
		if line.startswith("|"):
			# start of a cell
			for cell in line[1:].split("||"):
				row.append(cell)
			continue

		if line.startswith("!"):
			# start of a header cell
			for cell in line[1:].split("!!"):
				row.append(cell)
			continue

		# text on a line by itself appends to the current cell 
		row[-1] += '\n' + line

	if row_num == 0:
		print "Error: table could not be parsed at url: %s" % url
		return None

	# convert to records keyed on key_field

	# first, get record attribute names from the header row
	# and find key column number
	if field_names:
		attr_names = field_names
		data_start_row = 0
	else:
		header = rows[0]
		attr_names = []
		for attr in header:
			attr_names.append(attr.strip())
		data_start_row = 1
		
	try:
		key_index = attr_names.index(key_field)
	except:
		print "Error: Could not find table key '%s' in table at %s" % (key_field, url)
		return None

	records = {}
	for row in rows[data_start_row:]:
		record = {}
		try:
			key_value = row[key_index]
		except:
			print "Error: dropping row '%s' because it doesn't have a key value" % row
			continue

		for i in range(len(row)):
			name = attr_names[i]
			value = row[i]
			record[name] = value

		if records.has_key(key_value):
			print "Error: duplicate row for key '%s', skipping row '%s'" % (key_value, row)
			continue

		records[key_value] = copy.deepcopy(record)

	return records

# read wiki table and get device url for a specific device
def get_url_for_device(table_url, key_field, device_name):
	records = parse_mediawiki_table(table_url, key_field)
	record = None
	try:	
		record = records[device_name]
	except KeyError:
		print "Error: Cannot find device '%s' in wiki table" % \
			device_name
		sys.exit(1)
	
	try:
		url = record[dev_url_field]	
	except KeyError:
		print "Error: Missing column '%s' from wiki table" % \
			dev_url_field
		sys.exit(1)

	print "Url for device is: '%s'" % url
	return url

def download_git(url, output_dir):
	saved_cur_dir = os.getcwd()
	os.chdir(output_dir)
	git_cmd = "git clone %s ." % url
	rcode = os.system(git_cmd)
	if rcode != 0:
		raise ValueError

	path = output_dir
	os.chdir(saved_cur_dir)

	# check that this is a kernel source tree
	mpath = os.path.join(path, os.sep, "MAINTAINERS")
	if not os.path.isfile(mpath):
		print "Error: MAINTAINERS file not found in %s after download." % path
		raise ValueError
	
	return path
	

# download file from internet and place it in output_dir
# return the path to the file created
def download_from_web(url, output_dir):
	# use curl for now
	print "In download_from_web, url=%s" % url
	do_curl = 0
	do_wget = 1

	parse_object = urlparse(url)
	filename = os.path.basename(parse_object.path)
	path = os.path.join(output_dir, filename)

	if do_curl:
		saved_cur_dir = os.getcwd()
		os.chdir(output_dir)
		curl_cmd = "curl -# -o %s %s" % (filename, url)
		print "curl_cmd =", curl_cmd
		rcode = os.system(curl_cmd)
		os.chdir(saved_cur_dir)

	if do_wget:
		# use no-host-directories and no-directories with wget
		wget_cmd = "wget -nH -nd -t 3 -P %s %s" % (output_dir, url)
		#print "wget_cmd =", wget_cmd
		rcode = os.system(wget_cmd)

	if rcode != 0:
		raise ValueError

	if not os.path.isfile(path):
		print "Error: File not found at %s after download." % path
		raise ValueError
	
	return path

# need to define how I unpack things!!!
# make a uat-unpack directory
def find_maintainers():
	# FIXTHIS - write a routine to find the MAINTAINERS file
	return None
	

def multi_level_unpack(output_dir, path):
	# iterate over an unpack area until MAINTAINERS is found
	abspath = os.path.abspath(path)
	saved_cur_dir = os.getcwd()
	unpack_dir = output_dir + os.sep + "uat-unpack"
	os.mkdir(unpack_dir)
	os.chdir(unpack_dir)
	if abspath.endswith(".zip"):
		unzip_cmd = "unzip %s" % abspath
		os.system(unzip_cmd)

	if abspath.endswith(".tar"):
		untar_cmd = "tar -xf %s" % abspath
		os.system(untar_cmd)

	if abspath.endswith(".tar.bz2"):
		untar_cmd = "tar -xjf %s" % abspath
		os.system(untar_cmd)

	if abspath.endswith(".tar.gz"):
		untar_cmd = "tar -xzf %s" % abspath
		os.system(untar_cmd)

	if abspath.endswith(".tgz"):
		untar_cmd = "tar -xzf %s" % abspath
		os.system(untar_cmd)

	# now, look for MAINTAINERS
	mpath = find_maintainers()
	print "MAINTAINERS file found at", mpath

	os.chdir(saved_cur_dir)

		
	# handle a nested tar
	# $ unzip kernel0130.zip 
	# Archive:  kernel0130.zip
	#   creating: zenfone.MR10.2-2.21.40.tar/
	#  inflating: zenfone.MR10.2-2.21.40.tar/zenfone.MR10.2-2.21.40.tar  

	# specifically look for a tar file in a dir ending in .tar
	items = os.listdir(".")
	for item in items:
		if item.endswith(".tar") and os.path.isdir(item):
			# see if there's a tar file in this '.tar' dir
			sub_items = os.listdir(item)
			for sub_item in sub_items:
				if sub_item.endswith(".tar") and \
					os.path.isfile(sub_item):
					print "Found a sub-tar, unpack that!"

# this is the main routine.
# output_dir must exist
# source_type should be one of: 
def get_source(url, output_dir, source_type, verbose=1): 
	# download the source package from the url
	vprint(verbose, "Downloading source...")

	is_git = False
	path = None
	if url.endswith(".git"):
		is_git = True
		try:
			path = download_git(url, output_dir)
		except:
			pass

	else:
		# FIXTHIS - switch download method depending on source_type??
		try:
			path = "Zenfone_6/kernel0130.zip"
			#path = download_from_web(url, output_dir)
		except:
			pass

	if path:
		vprint(verbose, "Successfully downloaded %s" % path)
	else:
		print "Error: could not download source from %s" % url
		sys.exit(1)

	print "Unpacking source..."
	multi_level_unpack(output_dir, path)
	
def main():
	output_dir = None
	source_type = "tarfile"
	url = None
	device_name = None

	# parse command-line args
	if "-h" in sys.argv or "--help" in sys.argv:
		usage()
	if "-o" in sys.argv:
		output_dir = sys.argv[sys.argv.index("-o")+1]
		sys.argv.remove(output_dir)
		sys.argv.remove("-o")
	if "-t" in sys.argv:
		source_type = sys.argv[sys.argv.index("-t")+1]
		sys.argv.remove(source_type)
		sys.argv.remove("-t")
	if "-u" in sys.argv:
		url = sys.argv[sys.argv.index("-u")+1]
		sys.argv.remove(url)
		sys.argv.remove("-u")
	if "-d" in sys.argv:
		device_name = sys.argv[sys.argv.index("-d")+1]
		sys.argv.remove(device_name)
		sys.argv.remove("-d")
	if "-l" in sys.argv:
		records = parse_mediawiki_table(dev_table_raw_url, dev_key_field)
		keylist = records.keys()
		keylist.sort()
		print "Devices in wiki table:"
		for key in keylist:
			print "    '%s'" % key
			# url = records[key][dev_url_field]
		sys.exit(0)

	# check args
	if source_type not in source_types:
		print "Error: invalid source type: '%s'" % source_type
		usage()

	if url and device_name:
		print "Error: Please specify either a url or a device, but not both"
		usage()

	if not url and not device_name:
		print "Error: You must specify either a url or a device."
		usage()

	if device_name:
		url = get_url_for_device(dev_table_raw_url, dev_key_field,\
			device_name)
		if not output_dir:
			output_dir = device_name.replace(" ","_")
	else:
		if not output_dir:
			output_dir = "uat-kernel"
		
	# make output_dir and change to it
	if not os.path.isdir(output_dir):
		os.mkdir(output_dir)

	get_source(url, output_dir, source_type)

	print "Done."


if __name__=="__main__":
	main()
