#!/usr/bin/env python
import os,time,argparse,sqlite3
homedir = os.path.expanduser("~")

#Default paths:
output_path = homedir + "/Desktop"
db_path = homedir + "/pictures/photos/digikam4.db"

# Command line argument parsing:
parser = argparse.ArgumentParser(description="Searches the digikam database, and copies folders of matching albums")

# Query arguments: tag, rating, date range:
parser.add_argument('-t', '--tags', help='Tag query. For multiple tags, separate tags with AND')
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
try:
	conn = sqlite3.connect(db_path)
except:
	print("Database connection failed. Perhaps the specified database path is incorrect?")

c = conn.cursor()

#####################################
#QUERY BUILDING:
#SELECT name FROM Tags JOIN Albumroots ON Tags.id=Albumroots

#---------------------------------
# Construct rating query
#Rating is rating column in ImageInformation table
if args.rating:
	sql = sql + ""


#---------------------------------
# Construct date query (mm/dd/yyyy or mm/dd/yy)

#---------------------------------
# Construct tag query

#Find matching tag from query. Return tag ID. If more than one match, throw error and break:
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
#ERROR: tag AND tag is operating as OR due to "IN" statement
sql_example_delete_this_varibale = """
repeat this selection for each tag, then JOIN where album id's match?

SELECT id,relativePath FROM Albums WHERE id IN (
		SELECT album FROM Images WHERE id IN (
			SELECT imageid FROM ImageTags WHERE tagid=<tagid>
		)
	)
"""

sql = """
SELECT id,relativePath FROM Albums WHERE id IN (
		SELECT album FROM Images WHERE id IN (
			SELECT imageid FROM ImageTags WHERE tagid IN (?"""
for i in range(int(len(tag_array))-1):
	sql = sql + ", ?"
sql = sql + ")))"

#EXAMPLE of how to find albums containing two tags (not necessarily tagged in the same photo. Need to figure out how to apply to more than two tags:
sql = """
SELECT *
FROM (
	SELECT id,relativePath FROM Albums WHERE id IN ( 
			SELECT album FROM Images WHERE id IN (
				SELECT imageid FROM ImageTags WHERE tagid=2
			)
		)
	) a
JOIN (
SELECT id,relativePath FROM Albums WHERE id IN (
		SELECT album FROM Images WHERE id IN (
			SELECT imageid FROM ImageTags WHERE tagid=121
		)
	)
) b
ON a.id=b.id

"""
#c.execute(sql, tag_array)
c.execute(sql)
out = c.fetchall()
print(out)
