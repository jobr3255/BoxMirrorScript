from __future__ import print_function, unicode_literals
import os, time
#from datetime import datetime
import datetime
import calendar
from dateutil import tz
from boxsdk import Client
from boxsdk.exception import BoxAPIException
from boxsdk.exception import BoxOAuthException
from boxsdk import OAuth2
import sys
import json

# Global variables
CLIENT_ID = 'rekbftn97gk0j2f13lwm9ie27yprogcr'
CLIENT_SECRET = 'xS6nu9ftGAc2NxQJ0mcB9Ok2rD7nY3z0'
ACCESS_TOKEN = '5huKKnpNVd33o2pXtVp9emgXd3XsmaCY'
CLIENT = None
PATH = None
ID = None
UPLOADED = 0
UPLOAD_FAILED = 0
DOWNLOADED = 0
DOWNLOAD_FAILED = 0
UTC_OFFSET = None

# Helper class to deal with flags
class Flag():
	VALID = ["-f", "-full", "-o", "-overwrite", "-e"]
	FULL = False
	OVERWRITE = False
	ERROR = False
	@staticmethod
	def evaluate(flag):
		if flag == "-f" or flag == "-full":
			Flag.FULL = True
		elif flag == "-o" or flag == "-overwrite":
			Flag.OVERWRITE = True
		elif flag == "-e":
			Flag.ERROR = True

# Helper class for coloring the output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ContinueSearch(Exception):
	pass

# ------------------------------------------
# General functions
# ------------------------------------------

# Options menu for valid options and flags
def options():
	print("Usage: python "+sys.argv[0]+" [option] [flags] <path>")
	options = """
	---------------------------------------------------------------
	-----------------------    Options     ------------------------
	---------------------------------------------------------------

	-h, -help 			: Open options help
	-u, -user			: Print user login
	-s <path> 			: Search for a file or folder 
					  from Box
	-l <path>			: List all items in a folder
	-i <path>, -info <path>		: Get info on a file or folder
	-U, -upload   [flags] <path> 	: Uploads a file or all the files 
					  in a folder to box
	-D, -download [flags] <path> 	: Downloads a file or all the 
					  files in a folder from box to the 
					  current directory
	-S, -sync <path> 		: Sync file or folder in Box 
					  and locally

	-----------------------     Flags      ------------------------

	-f, -full 			: Uploads or downloads all files 
					  and all subdirectores
	-o, -overwrite			: Overwrites files on Box or 
					  locally when uploading or 
					  downloading
	"""
	print(options)

# Handler function when an unknown flag is used
def invalid():
	print(bcolors.FAIL+"Invalid option "+bcolors.ENDC+"\'"+ sys.argv[1] +"\' \033[0m")
	print("Try \'python "+ sys.argv[0] +" -h\' for more information.")

# returns a name given the full path to that file or folder
def nameFromPath(path):
	name = path
	while("/" in name):
		name = name[name.index("/")+1:]
	return name

def pathDoesNotExist(path, location="on box"):
	print("\'" + path + "\' " + bcolors.FAIL + "Does not exist " + location + bcolors.ENDC)
	os._exit(0)

# displays an error message is a path is not given
def pathNotGiven():
	print(bcolors.FAIL + "Path or ID not specified" + bcolors.ENDC)
	print("Try \'python "+ sys.argv[0] +" -h\' for more information.")
	os._exit(0)

def test():
	json_response = CLIENT.make_request(
    'GET',
    CLIENT.get_url('files', '297752586807')).json()
	print(json_response)

# This will return a file id or the path if they are given
# Will quit if no valid path or id is given
# Also sets optional flags
def loadArgs():
	path_id = None
	global ID, PATH
	if(len(sys.argv) == 1):
		invalid()
		os._exit(0)
	for a in sys.argv[2:]:
		if a in Flag.VALID:
			Flag.evaluate(a)
		else:
			path_id = a
	if sys.argv[1] in  ["-h", "-help", "-u", "-user"]:
		return
	if not path_id:
		pathNotGiven()
		os._exit(0)
	try:
		ID = int(path_id)
	except Exception as e:
		PATH = path_id

# displays a yes or no message that must be answered before continuing
# returns true or false
def yesNo(message):
	userInput = None
	validYes = {'y','yes',''}
	validNo = {'n','no'}
	while(userInput not in validYes and userInput not in validNo):
		userInput = raw_input(message)
	if(userInput in validYes):
		return True
	else:
		return False

def error(function_name, error):
	print(bcolors.FAIL + "An error occured in " + bcolors.ENDC + function_name)
	if Flag.ERROR:
		if type(error) == list:
			for e in error:
				print(e)
				print()
		else:
			print(error)
	os._exit(0)

def alreadyExists(path, location="on Box"):
	up_down = "Upload"
	if location == "locally":
		up_down = "Download"
	print(bcolors.FAIL + up_down + " failed: " + bcolors.ENDC +
	"\'" + path + "\' already exists " + location)

def info():
	try:
		item = myBoxGet(PATH).get()
		on_box = True
	except:
		on_box = False
	local = isLocal(PATH)
	if(on_box):
		name = item['name']
		item_id = item['id']
		item_type = item['type']
		box_created_at = str(getBoxTime(item['created_at']))
		box_modified_at = str(getBoxTime(item['modified_at']))
	if(local):
		name = nameFromPath(PATH)
		item_type = getLocalType(PATH)
		local_created_at = str(getLocalCreationDate(PATH))
		local_modified_at = str(getLocalModifiedDate(PATH))
	if not local and not on_box:
		pathDoesNotExist(PATH)
	information = [
	"Name 		: " + name,
	"Type 		: " + item_type,
	"Path 		: " + PATH,
	"On Box? 	: " + str(on_box),
	"Locally? 	: " + str(local)
	]
	for i in information:
		# add color toggle that will switch between white and blue for easy readability
		print(i)
	if(on_box):
		print("Box info:")
		print("Box id 		: " + item_id)
		print("Created 	: " + box_created_at)
		print("Modified 	: " + box_modified_at)
	if(local):
		print("Local info:")
		print("Created 	: " + local_created_at)
		print("Modified 	: " + local_modified_at)

def setUTC():
	global UTC_OFFSET
	utc_string = str(datetime.datetime.utcnow())[:-10]
	local_string = str(datetime.datetime.now())[:-10]
	utc_date = datetime.datetime.strptime(utc_string, "%Y-%m-%d %H:%M")
	local_date = datetime.datetime.strptime(local_string, "%Y-%m-%d %H:%M")
	UTC_OFFSET = utc_date - local_date
# ------------------------------------------
# Box functions
# ------------------------------------------

# Prints out user information
def user():
	me = CLIENT.user(user_id='me').get()
	print('user_login: ' + me['login'])
	print('user_name: ' + me['name'])

# returns a formated string for the full path of a file or folder on box given an item
def format(item):
	parent = item['parent']
	itemType = item['type']
	formated_string = ''
	path_name = ''
	while(parent['type'] == "folder" and parent['name'] != "All Files"):
		path_name = parent['name'] + "/" + path_name
		parent = CLIENT.folder(folder_id=parent['id']).get()['parent']
	path_name += item['name']
	formated_string += path_name
	return formated_string

# searches for items on box and prints out the results
def search():
	print("Searching for \'"+PATH+"\'...")
	results = CLIENT.search(PATH, limit=100, offset=0)
	for r in results:
		if(PATH.lower() not in r['name'].lower()):
			results.remove(r)
	if(len(results) == 1):
		print("1 result found")
	else:
		print(str(len(results)) + " results found")
	for r in results:
		itemType = r['type']
		formated_string = ''
		if(itemType == 'folder'):
			formated_string += bcolors.OKBLUE
		formated_string += format(r.get())
		if(itemType == 'folder'):
			formated_string += bcolors.ENDC
		print(formated_string)

# returns true or false if an item is found on Box given the path to that item
def findBox(path):
	results = CLIENT.search(path, limit=100, offset=0)
	for r in results:
		if(format(r.get()) == path):
			return r
	return False

# returns an item from box given the path to that item
def getBoxItemFromPath(path):
	results = CLIENT.search(nameFromPath(path), limit=100, offset=0)
	if(len(results) != 1):
		return False
	elif(format(results[0].get()) != path):
		return False
	else:
		return results[0].get()

def myBoxGet(path):
	root_folder = CLIENT.folder(folder_id='0')
	path_array = path.split("/")
	items = root_folder.get_items(limit=100, offset=0)
	while(len(path_array) != 0):
		current_search_item = path_array.pop(0)
		#print("searching for " + current_search_item)
		try:
			for i in items:
				if(i.get()['name'] == current_search_item):
					#print("found " + current_search_item)
					if(i.get()['type'] == "folder"):
						items = i.get().get_items(limit=100, offset=0)
					if(len(path_array) == 0):
						return i
					raise ContinueSearch()
		except ContinueSearch:
			continue
		return False
	return root_folder

# box search does not return recently uploaded files
def myBoxSearch():
	print("Searching for \'" + PATH + "\'...")
	item = myBoxGet(PATH)
	if(item):
		print("Found " + PATH)
	else:
		print(PATH + " not found")

# lists all the files and folder in a given directory
def listItems():
	if(len(sys.argv) == 2):
		items = CLIENT.folder(folder_id='0').get_items(limit=100, offset=0)
	else:
		folder = getBoxItemFromPath(PATH)
		if(folder):
			items = CLIENT.folder(folder['id']).get_items(limit=100, offset=0)
		else:
			pathDoesNotExist(PATH)
			return False
	for i in items:
		itemType = i['type']
		formated_string = ''
		if(itemType == 'folder'):
			formated_string += bcolors.OKBLUE
		formated_string += i['name']
		if(itemType == 'folder'):
			formated_string += bcolors.ENDC
		print(formated_string)

def getBoxTime(time_string):
	offset = time_string[-5:]
	h = int(offset[:2])
	m = int(offset[3:])
	no_offset = datetime.datetime.strptime(time_string[:-6], '%Y-%m-%dT%H:%M:%S')
	if time_string[-6:-5] == "-":
		utc_time = no_offset + datetime.timedelta(hours=h,minutes=m)
	else:
		utc_time = no_offset - datetime.timedelta(hours=h,minutes=m)
	#print(str(utc_time)+" applied offset, now in utc")
	local_time = utc_time - UTC_OFFSET
	#print(str(local_time)+" local time")
	return local_time
	#print(datetime.strptime(time_string[:-6], '%Y-%m-%dT%H:%M:%S'))

# ------------------------------------------
# Download functions
# ------------------------------------------

def download():
	item = myBoxGet(PATH)
	if not item:
		pathDoesNotExist(PATH)
	elif(item['type'] == 'file'):
		downloadFile(PATH, item)
	else:
		if(Flag.FULL):
			downloadFolderFull(PATH, item)
		else:
			downloadFilesInFolder(item, PATH)
		print(bcolors.FAIL + "Failed" + bcolors.ENDC + " to download " + bcolors.FAIL + str(DOWNLOAD_FAILED) + bcolors.ENDC + " file(s)")
		print(bcolors.OKGREEN + "Successfully" + bcolors.ENDC + " downloaded " + bcolors.OKGREEN + str(DOWNLOADED) + bcolors.ENDC + " file(s)")

def downloadFile(path, file):
	if(file):
		path_array = path.split("/")
		path_array.remove(file['name'])
		directory = ("/").join(path_array)
		print(bcolors.OKBLUE + "Downloading " + bcolors.ENDC + path + "...")
		if(len(directory) != 0):
			if not os.path.isfile(directory):
				os.makedirs(directory)
		if(os.path.exists(path)):
			if not Flag.OVERWRITE:
				alreadyExists(path, "locally")
				os._exit(0)
		f = open(path, "wb")
		file.download_to(f)
		f.close()
		changeModifiedDate(path, file.get()['modified_at'])
		print(bcolors.OKGREEN + "Successfully" + bcolors.ENDC + " downloaded " + path)
	else:
		print(bcolors.FAIL + "Could not find " + bcolors.ENDC + "\'" + path + "\'")

def downloadFolderFull(path, folder):
	folders = []
	unchecked_folders = [folder]
	while(len(unchecked_folders) != 0):
		f = unchecked_folders.pop()
		items = f.get_items(limit=100, offset=0)
		for i in items:
			if(i.get()['type'] == "folder"):
				unchecked_folders.append(i)
		folders.append((f,format(f.get())))
	for t in folders:
		downloadFilesInFolder(t[0],t[1])

def downloadFilesInFolder(folder, path):
	global DOWNLOADED, DOWNLOAD_FAILED
	items = folder.get_items(limit=100, offset=0)
	if(len(path) != 0):
		if not os.path.exists(path):
			os.makedirs(path)
	for i in items:
		file = i.get()
		if(file['type'] == "file"):
			file_path = path + "/" + file['name']
			print(bcolors.OKBLUE + "Downloading " + bcolors.ENDC + file_path + "...")
			if(os.path.isfile(file_path)):
				if not Flag.OVERWRITE:
					alreadyExists(file_path, "locally")
					DOWNLOAD_FAILED += 1
				else:
					f = open(file_path, "wb")
					file.download_to(f)
					f.close()
					DOWNLOADED += 1
			else:
				f = open(file_path, "wb")
				file.download_to(f)
				f.close()
				DOWNLOADED += 1

def changeModifiedDate(path, modified):
	box_modified_at = getBoxTime(modified)
	print(box_modified_at)
	modified_date = datetime.datetime.strptime(str(box_modified_at), "%Y-%m-%d %H:%M:%S")
	timestamp = modified_date.strftime("%Y%m%d%H%M.%S")
	query = "touch -a -m -t "+str(timestamp)+" "+path
	os.popen(query)

# ------------------------------------------
# Upload functions
# ------------------------------------------

# This will automatically detect if a file or a folder is being uploaded
def upload():
	if(os.path.isfile(PATH)):
		uploadFile(PATH)
	elif(os.path.isdir(PATH)):
		if(Flag.FULL):
			uploadFolderFull(PATH)
		else:
			uploadFolder(PATH)
		print(bcolors.FAIL + "Failed" + bcolors.ENDC + " to upload " + bcolors.FAIL + str(UPLOAD_FAILED) + bcolors.ENDC + " file(s)")
		print(bcolors.OKGREEN + "Successfully" + bcolors.ENDC + " uploaded " + bcolors.OKGREEN + str(UPLOADED) + bcolors.ENDC + " file(s)")
	else:
		pathDoesNotExist(PATH, "locally")

# Uploads a single file
def uploadFile(path):
	path_array = path.split("/")
	name = path_array.pop()
	folder = checkPathDependencies(("/").join(path_array))
	try:
		file = findBox(path)
		if(not file):
			print(bcolors.OKBLUE + "Uploading " + bcolors.ENDC + path + "...")
			file = folder.upload(path, file_name=name)
			print(bcolors.OKGREEN + "Successfully uploaded " + bcolors.ENDC + path)
		else:
			if Flag.OVERWRITE:
				overwriteFile(file, PATH, True, True)
			else:
				alreadyExists(path)
	except Exception as e:
		try:
			file_id = e.context_info['conflicts']['id']
			if(e.code == 'item_name_in_use'):
				file = CLIENT.file(file_id=file_id).get()
				if Flag.OVERWRITE:
					overwriteFile(file, PATH, True, True)
				else:
					alreadyExists(path)
		except Exception as er:
			error("uploadFile", [e, er])

# Uploads a whole folder
def uploadFolder(path):
	folder = checkPathDependencies(path)
	uploadFilesInFolder(folder, path)

# Uploads a folder and all subfolders and files
def uploadFolderFull(path):
	folder_paths = []
	for p, subdirs, files in os.walk(os.getcwd()+"/"+path):
		for sub in subdirs:
			folder_paths.append(p.replace(os.getcwd(),"")[1:]+"/"+sub)
	folder = checkPathDependencies(path)
	uploadFilesInFolder(folder, path)
	for f in folder_paths:
		folder = checkPathDependencies(f, False)
		uploadFilesInFolder(folder, f)

# Uploads all files in a given folder
def uploadFilesInFolder(folder, path, print_fail=True):
	global UPLOADED, UPLOAD_FAILED
	for name in os.listdir(path):
		file_path = path + "/" + name
		if(os.path.isfile(file_path)):
			try:
				print(bcolors.OKBLUE + "Uploading " + bcolors.ENDC + file_path + "...")
				file = folder.upload(file_path, file_name=name)
				UPLOADED += 1
			except Exception as e:
				try:
					file_id = e.context_info['conflicts']['id']
					if(e.code == 'item_name_in_use'):
						box_item = CLIENT.file(file_id=file_id).get()
						if Flag.OVERWRITE:
							overwriteFile(box_item, file_path)
						else:
							if print_fail:
								alreadyExists(file_path)
								UPLOAD_FAILED += 1
				except Exception as er:
					error("uploadFilesInFolder", [e, er])

# This checks the path dependencies and creates local directories if needed
# Returns the last folder in the path
def checkPathDependencies(path, print_checking = True):
	if not path:
		return CLIENT.folder(folder_id='0')
	path_array = path.split("/")
	dir_path = ""
	# This creates a path dependancy if one doesn't exist
	if(print_checking):
		print("Checking path dependancies...")
	current_folder = CLIENT.folder(folder_id='0')
	while(len(path_array) != 0):
		new_folder = path_array.pop(0)
		dir_path += new_folder
		folder = myBoxGet(dir_path)
		if(not folder):
			dir_path += "/"
			current_folder = current_folder.create_subfolder(new_folder)
			print("Creating folder " + dir_path)
		else:
			dir_path += "/"
			current_folder = folder
	return current_folder

def overwriteFile(file, path, print_success = False, print_upload = False):
	global UPLOADED, UPLOAD_FAILED
	try:
		if(print_upload):
			print(bcolors.OKBLUE + "Uploading " + bcolors.ENDC + path + "...")
		file.update_contents(path)
		UPLOADED += 1
		if(print_success):
			print(bcolors.OKGREEN + "Successfully uploaded " + bcolors.ENDC + path)
	except Exception as e:
		error("overwriteFile", e)
		UPLOAD_FAILED += 1

# ------------------------------------------
# Sync functions
# ------------------------------------------

def sync():
	try:
		item = myBoxGet(PATH).get()
		on_box = True
	except:
		on_box = False
	local = isLocal(PATH)
	if local and on_box:
		print("update most recently modified")
		local_type = getLocalType(PATH)
		if(local_type == "file"):
			syncFile(PATH, item)
		elif(local_type == "folder"):
			if(Flag.FULL):
				syncFolderFull(PATH)
			else:
				syncFolder(PATH)
	elif local:
		local_type = getLocalType(PATH)
		if(local_type == "file"):
			print("upload file to box")
			uploadFile(path, file)
		elif(local_type == "folder"):
			if(Flag.FULL):
				#downloadFolderFull(item, PATH)
				print("upload full folder to box")
			else:
				#downloadFilesInFolder(item, PATH)
				print("upload folder to box")
			#print(bcolors.FAIL + "Failed" + bcolors.ENDC + " to upload " + bcolors.FAIL + str(UPLOAD_FAILED) + bcolors.ENDC + " file(s)")
			#print(bcolors.OKGREEN + "Successfully" + bcolors.ENDC + " uploaded " + bcolors.OKGREEN + str(UPLOADED) + bcolors.ENDC + " file(s)")
	elif on_box:
		if(item['type'] == "file"):
			downloadFile(path)
		else:
			if(Flag.FULL):
				#uploadFolderFull(PATH)
				print("download full folder")
			else:
				#uploadFolder(PATH)
				print("download folder")
			#print(bcolors.FAIL + "Failed" + bcolors.ENDC + " to upload " + bcolors.FAIL + str(UPLOAD_FAILED) + bcolors.ENDC + " file(s)")
			#print(bcolors.OKGREEN + "Successfully" + bcolors.ENDC + " uploaded " + bcolors.OKGREEN + str(UPLOADED) + bcolors.ENDC + " file(s)")

def syncFile(path, file):
	local_modified_at = getLocalModifiedDate(path)
	box_modified_at = getBoxTime(file['modified_at'])
	print(local_modified_at)
	print(box_modified_at)

def syncFolder(path):
	print("syncFolder")

def syncFolderFull(path):
	print("syncFolderFull")

# ------------------------------------------
# Local functions
# ------------------------------------------

def isLocal(find):
	for path, subdirs, files in os.walk(os.getcwd()):
		for name in files:
			full_path = os.path.join(path, name)
			path_name = full_path[len(os.getcwd())+1:]
			if(find == path_name):
				return True
		for dirname in subdirs:
			full_path = os.path.join(path, dirname)
			path_name = full_path[len(os.getcwd())+1:]
			if(find == path_name):
				return True
	return False
def getLocalID(path):
	var = os.popen("stat "+path+" | grep 'Inode: '[0-9]*").read()
	var = var.replace("\t", " ")
	array = (var.replace("\t", " ")).split(" ")
	return(array[array.index("Inode:")+1])

def getLocalType(path):
	if(os.path.isfile(path)):
		return "file"
	elif(os.path.isdir(path)):
		return "folder"
	else:
		return "unknown"

def getLocalCreationDate(path):
	local_id = getLocalID(path)
	var = os.popen("sudo debugfs -R 'stat <"+local_id+">' /dev/sda1 2> /dev/null | grep 'crtime'.*").read()
	date_str = var[var.index("--")+3:].replace("\n", "")
	return(datetime.datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y"))

def getLocalModifiedDate(path):
	local_file_date_string = datetime.datetime.fromtimestamp(os.stat(path).st_mtime).strftime("%Y-%m-%d %H:%M:%S")
	local_file_date = datetime.datetime.strptime(local_file_date_string, '%Y-%m-%d %H:%M:%S')
	return local_file_date

if __name__ == '__main__':

    oauth = OAuth2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,access_token=ACCESS_TOKEN)
    client = Client(oauth)
    CLIENT = client
    loadArgs()
    setUTC()
    switcher = {
    "-h": options, "-help": options,
    "-u": user, "-user": user,
    "-s": search,
    "-l": listItems,
    "-info": info,
    "-U": upload, "-upload": upload,
    "-D": download, "-download": download,
    "-S": sync, "-sync": sync,
    "-test": test,
    "-mySearch": myBoxSearch
    }
    #print switcher.get(userInput, "Invalid")

    func = switcher.get(sys.argv[1], lambda: invalid())
    try:
    	func()
    except BoxOAuthException:
    	print(bcolors.FAIL + "Developer token has expired" + bcolors.ENDC)

    os._exit(0)