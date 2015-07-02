#!/usr/bin/python
#
# uat-get-kernel-source - retrieve the kernel source from a given url
#
# to do:
#  - unpack source tar
#    - write "find maintainers" routine
#  - do type-specific source fixups
#
import os, sys
from urlparse import urlparse
import urllib2
import copy

# a uat work area looks like this:
# <device_name_dir>/<source-archive>
#                  /uat-unpack
#                  /kernel
#                  /data
#
# <device_name_dir> defaults to "uat-device"

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
	print """Usage: %s [options] [-d <device>|-u <URL>|-f <file>]

Retrieve the kernel source for the indicated device (or from the specified
URL), and unpack it.   Either the device (from the wiki page) or a URL must
be specified.

  -h, --help      Show this usage help
  -o <output_dir> Put the kernel source in <output_dir>.  If not specified,
                  the program uses the directory 'uat-device', if a URL is
                  used, or the device name (with spaces converted to
                  underscores) if a device is specified.
  -t <type>       Specify the type of kernel source.  If not specified,
                  use a type of 'tarfile'.  Possible values are:
                  'tarfile', 'sony', 'mediatek', 'samsung', "asusziptar"
  -u <URL>        Download the source package from the indicated URL.
  -d <device>     Find the devices listed on the device page
  -f <file>       Unpack the indicated file.  This is used to unpack a
                  source archive that was manually downloaded.
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
		print "Error: Table could not be parsed at url: %s" % url
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
			print "Error: Dropping row '%s' because it doesn't have a key value" % row
			continue

		for i in range(len(row)):
			name = attr_names[i]
			value = row[i]
			record[name] = value

		if records.has_key(key_value):
			print "Error: Duplicate row for key '%s', skipping row '%s'" % (key_value, row)
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
	mpath = path +  os.sep + "MAINTAINERS"
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
	path = output_dir + os.sep +  filename

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
def find_maintainers(path):
	# FIXTHIS - write a routine to find the MAINTAINERS file
	for root, dirs, files in os.walk(path):
		for f in files:
			if f=="MAINTAINERS":
				return os.path.join(root, f)
	return None
	
# list consists of tuples with (<suffix>, <action>)
unpack_action_list=[(".zip", "unzip %s"),
	(".tar", 'tar -xf "%s"'),
	(".tar.gz", 'tar -xzf "%s"'),
	(".tar.bz2", 'tar -xjf "%s"'),
	(".tar.xz", 'tar -xJf "%s"'),
	(".tgz", 'tar -xzf "%s"'),
	(".tbz", 'tar -xjf "%s"'),
	(".tbz2", 'tar -xjf "%s"'),
	(".tb2", 'tar -xjf "%s"'),
	(".txz", 'tar -xJf "%s"'),
]

# output_dir and abspath must be absolute paths
def multi_level_unpack(output_dir, abspath):
	# iterate over an unpack area until MAINTAINERS is found
	unpack_done = False
	for ext, action in unpack_action_list:
		if abspath.endswith(ext):
			unpack_cmd = action % abspath
			os.system(unpack_cmd)
			unpack_done = True

	# now, look for MAINTAINERS
	mpath = find_maintainers(".")
	print "MAINTAINERS file found at", mpath

	# check here for some weird issues

	if mpath:
		abs_output_dir = os.path.abspath(output_dir)
		os.mkdir(abs_output_dir + os.sep + "kernel")

		src_dir = "uat-kernel"+ os.sep + os.path.dirname(mpath)
		dest_dir = abs_output_dir + os.sep + "kernel"

		# move kernel files to kernel directory
		# this is going to break mediatek links
		for item in os.listdir(src_dir):
			os.rename(src_dir + os.sep + item, \
				dest_dir + os.sep + item)
		
	else:
		# check for nested archives
		for root, dirs, files in os.walk("uat-unpack"):
			for f in files:
				for ext, action in unpack_action_list:
					if f.endswith(ext):
						multi_level_unpack(output_dir, os.path.abspath(os.join(root, dirs, f)))
						
						


# output_dir must exist
# url can be a local file, in which case the url starts with "file:"
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
	elif url.startswith("file:"):
		# just copy the file to the unpack directory
		src_path = url[5:]
		dest_path = output_dir + os.sep + os.path.basename(src_path)
		cp_cmd = 'cp "%s" "%s"' % (src_path, dest_path)
		cp_cmd = rcode = os.system(cp_cmd)
		if rcode != 0:
			print "Error: Could not copy file from %s to %s" % \
				(src_path, dest_path)
		else:
			path = dest_path
	else:
		# FIXTHIS - switch download method depending on source_type??
		try:
			#path = "Zenfone_6/kernel0130.zip"
			path = download_from_web(url, output_dir)
		except:
			pass

	if path:
		vprint(verbose, "Successfully downloaded %s" % path)
	else:
		print "Error: Could not download source from %s" % url
		sys.exit(1)

	return path

	
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
	if "-f" in sys.argv:
		filepath = sys.argv[sys.argv.index("-f")+1]
		sys.argv.remove(filepath)
		sys.argv.remove("-f")
		if not os.path.isfile(filepath):
			print "Error: Could not find file '%s'" % filepath
			sys.exit(1)
		url = "file:" + filepath
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
		print "Error: Invalid source type: '%s'" % source_type
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
			output_dir = "uat-device"
		
	# make output_dir if needed
	if not os.path.isdir(output_dir):
		os.mkdir(output_dir)

	path = get_source(url, output_dir, source_type)

	print "Unpacking source..."
	abspath = os.path.abspath(path)
	saved_cur_dir = os.getcwd()

	# get into the unpack directory
	unpack_dir = output_dir + os.sep + "uat-unpack"
	os.mkdir(unpack_dir)
	os.chdir(unpack_dir)

	multi_level_unpack(os.path.abspath(output_dir), abspath)
	os.chdir(saved_cur_dir)

	print "Done."


if __name__=="__main__":
	main()
