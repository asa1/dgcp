#!/usr/bin/env python
import os,time,argparse,sqlite3
homedir = os.path.expanduser("~")

#Default paths:
output_path = homedir + "/Desktop"
db_path = homedir + "/pictures/photos/digikam4.db"

# Command line argument parsing:
parser = argparse.ArgumentParser(description="Searches the digikam database, and copies folders of matching albums")

# Query arguments: tag, rating, date range:
parser.add_argument('-t', '--tags', help='Tag query. Must be in quotes, with conditionals outside quotes')
parser.add_argument('-r', '--rating', help='Rating (1 - 5)')
parser.add_argument('-d', '--date', help='Date Range (mm/dd/yyyy - mm/dd/yyyy')

# Optional arguments to change Digikam DB location, or output folder:
parser.add_argument('--outputpath', help='Specify alternate output directory. Default is ~/Desktop/digikam-search_<unixtime>')
parser.add_argument('--dbpath', help='Specify alternate Digikam database location. Default is ~/pictures/photos/digikam4.db')

args = parser.parse_args()

#If DB or output paths have been specified as arguments, override the defaults:
if args.dbpath:
	db_path = args.dbpath
if args.outputpath:
	output_path = args.outputpath
#If directory already exists, create a subdirectory with unix time stamp:
if os.path.isdir(output_path):
	newpath = output_path + "/digikam_export_" + str(int(time.time()))
	if not os.path.exists(newpath):
		#DISABLED WHILE TESTING:
		#os.makedirs(newpath)
		pass

#Establish database connection:
print(db_path)
try:
	conn = sqlite3.connect(db_path)
except:
	print("Database connection failed. Perhaps the specified database path is incorrect?")

c = conn.cursor()

sql = "SELECT * FROM Tags WHERE name LIKE ?"
c.execute(sql, [("%"+args.tags+"%")])
out = (c.fetchall())

#NEED TO BUILD CONDITIONAL LOGIC BEFORE CHECKING NUMBER OF TAGS RETURNED!

#If tag search comes up with more than one result, throw error listing tags:
if len(out) > 1:
	print("ERROR: Multiple tags found:")
	for tag in out:
		print("   "+tag[2])
	print("Try again with a more exact tag query")

# Assuming AND between above options


# Construct tag query
# Each tag string must be in quotes, AND/OR outside of quotes?

# Construct rating query

# Construct date query (mm/dd/yyyy or mm/dd/yy)
