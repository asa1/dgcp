#!/usr/bin/env python
import sys,os,re,time,shutil,argparse,sqlite3
homedir = os.path.expanduser("~")

#Default paths:
output_path = homedir + "/Desktop"
db_path = homedir + "/pictures/photos/digikam4.db"

# Command line argument parsing:
parser = argparse.ArgumentParser(description="Searches the digikam database, and copies folders of matching albums")

# Query arguments: tag, rating, date range:
parser.add_argument('-t', '--tags', help='Tag query. For multiple tags, separate tags with AND. Example: -t \"frank AND ian underwood\"')
parser.add_argument('-r', '--rating', help='Rating range, from 0 to 5. Example: -r 3-5')
parser.add_argument('-d', '--date', help='Date Range <mm/dd/yyyy-mm/dd/yyyy>')

# Optional arguments to change Digikam DB location, output folder or run in test mode:
parser.add_argument('--outputpath', help='Specify alternate output directory. Default is ~/Desktop/digikam-search_<unixtime>')
parser.add_argument('--dbpath', help='Specify alternate Digikam database location. Default is ~/pictures/photos/digikam4.db')
parser.add_argument('--test', action='store_true', help='Run in test mode: disables directory creation and file copying, and prints list of matching files')

# If no arguments given, print help and exit:
if len(sys.argv) == 1:
	parser.print_help()
	sys.exit(1)

args = parser.parse_args()

#If DB or output paths have been specified as arguments, override the defaults:
if args.dbpath:
	db_path = args.dbpath
if args.outputpath:
	output_path = args.outputpath
#Set test mode:
if args.test:
	testmode = True
else:
	testmode = False
#If output directory already exists, create a subdirectory with unix time stamp:
if os.path.isdir(output_path):
	newpath = output_path + "/digikam_export_" + str(int(time.time()))
	if not os.path.exists(newpath):
		output_path = newpath
		if not testmode:
			os.makedirs(newpath)

#Establish database connection:
try:
	conn = sqlite3.connect(db_path)
except:
	print("Database connection failed. Perhaps the specified database path is incorrect?")

c = conn.cursor()

#####################################
#QUERY BUILDING:

# Parse rating range. Raise errors if input format is invalid or out of range:
if args.rating:
	# If only a single rating number is specified (e.g. 5, rather than 4-5), set upper and lower to same value:
	singlerating = re.compile("^[0-5]$")
	if singlerating.match(str(args.rating)):
		rating_lower = int(args.rating)
		rating_upper = int(args.rating)
	# Otherwise, proceed assuming a range was specified:
	else:
		rating_lower = str(args.rating).split("-")[0]
		rating_upper = str(args.rating).split("-")[1]
	try:
		rl = int(rating_lower)
		ru = int(rating_upper)
	except:
		raise Exception("Rating input is invalid. Should be in the format 0-5")
	if not (((rl >= 0) and (rl <=5)) and ((ru >=0) and (ru <=5))):
		raise Exception("Rating range invalid. Ratings must be between 0 and 5")
else :
	rating_lower = 0
	rating_upper = 5

#---------------------------------
# Parse date range arguments (mm/dd/yyyy-mm/dd/yyyy). Raise errors if input format is invalid:
if args.date:
	date_sections = str(args.date).split("-")
	if len(date_sections) == 2:
		date_lower = date_sections[0]
		date_upper = date_sections[1]
		#Shuffle date around into SQL format:
		date_lower = date_lower.split("/")[2]+"-"+date_lower.split("/")[0].zfill(2)+"-"+date_lower.split("/")[1].zfill(2)
		date_upper = date_upper.split("/")[2]+"-"+date_upper.split("/")[0].zfill(2)+"-"+date_upper.split("/")[1].zfill(2)
	else:
		raise Exception("Invalid date range. Date must be in format mm/dd/yyyy-mm/dd/yyyy")
	

#---------------------------------
# CONSTRUCT SQL QUERY:
# Build tag section of query:

#Find matching tag from query. Return tag ID. If more than one match, throw error and break:
#BUG: will not work if entered tag is incomplete version of another tag. For example, it won't be possible to search for a tag named "Bob" if a tag named "Bob Smith" also exists:
def find_tag(query):
	sql = "SELECT id,name FROM Tags WHERE name LIKE ?" 
	c.execute(sql, ["%"+query+"%"])
	out = c.fetchall()
	#If tag search comes up with more than one result, throw error listing tags:
	if len(out) > 1:
		error_text = "Multiple tags found:\n"
		for tag in out:
			error_text = error_text + "   "+tag[1]+"\n"
		error_text = error_text + "Try again with a more exact tag query"
		raise Exception(error_text)
	else:
		conn.row_factory = sqlite3.Row
		c.execute(sql, ["%"+query+"%"])
		out = c.fetchone()
		tag_id = out[0]
		tag_name = out[1]
		return(tag_id)

tagsearch_array = str(args.tags).split(" AND ")
tag_array = []

for tag in tagsearch_array:
	tag_array.append(find_tag(tag))

#Using id's from tag_array, put together SQL query section to finding matching albums:
sql = """
SELECT *
FROM (
	SELECT id,relativePath FROM Albums WHERE id IN ( 
			SELECT album FROM Images WHERE id IN ( SELECT imageid FROM ImageTags WHERE tagid="""+str(tag_array[0])+"""
			)
		)
	) tag"""+str(tag_array[0])+"""

"""
lasttag = str(tag_array[0])
#Loop to add section for each additional tag specified:
for i in range(int(len(tag_array))-1):
	tagid_prev = str(tag_array[i])
	tagid_curr = str(tag_array[i+1])
	lasttag = tagid_curr
	sql = sql+"""INNER JOIN (
	SELECT id,relativePath FROM Albums WHERE id IN (
			SELECT album FROM Images WHERE id IN (
				SELECT imageid FROM ImageTags WHERE tagid="""+tagid_curr+"""
			)
		)
	) tag"""+tagid_curr+"""
	ON tag"""+tagid_prev+""".id=tag"""+tagid_curr+""".id
	"""
#Add rating SQL (NOTE: this currently will choose any album with matching tags, and any images in the album that meet rating. Ideally, should check matched tag images for rating range instead):
sql = sql + """INNER JOIN (
	SELECT id,relativePath FROM Albums WHERE id IN (
		SELECT album FROM Images WHERE id IN (
			SELECT imageid FROM ImageInformation WHERE rating>="""+format(rating_lower)+""" AND rating<="""+format(rating_upper)+"""
		)
	)
) rating
ON rating.id=tag"""+format(lasttag)+".id"

#Add date range SQL:
if args.date:
	sql = sql + """
	INNER JOIN (
		SELECT id,relativePath FROM Albums WHERE id IN (
			SELECT album FROM Images WHERE id IN (
				SELECT imageid FROM ImageInformation WHERE creationDate BETWEEN \'"""+date_lower+"\' AND \'"+date_upper+"\'"+"""
			)
		)
	) date
	ON rating.id=date.id
"""
c.execute(sql)
out = c.fetchall()
#For each album, get list of images and copy:
for album in out:
	# Get list of image file names:
	sql = "SELECT name FROM Images WHERE album="+str(album[0])
	c.execute(sql)
	photolist = c.fetchall()
	# Get album root:
	sql = """
		SELECT specificPath FROM AlbumRoots WHERE id in (
			SELECT albumRoot FROM Albums WHERE id="""+str(album[0])+")"
	c.execute(sql)
	albumroot = c.fetchall()[0][0]
	for photofile in photolist:
		fullpath = albumroot + album[1] + "/" + photofile[0]
		dst_path = output_path + album[1] + "/"
		if testmode:
			print("===================")
			print("Copying from:")
			print(fullpath)
			print("to:")
			print(dst_path)
			print(" ")
		else:
			# If output subdirectory doesn't exist, create it:
			if not os.path.exists(dst_path):
				os.makedirs(dst_path)
			# Copy image:
			shutil.copyfile(fullpath,dst_path + "/" + photofile[0])
