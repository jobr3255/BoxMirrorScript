import os



def boxTimeDiff(client, path):
    root_folder = client.folder(folder_id='0')

    local_time = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    temp_file = root_folder.upload(path, file_name="fakefile.txt")
    temp_file.delete()
    box_time = datetime.strptime(temp_file["modified_at"][:-6], '%Y-%m-%dT%H:%M:%S')
    #print(box_time)
    
    #print(local_time)
    time_diff = local_time - box_time
    return time_diff
    #print(time_diff)
    #print("local box time  : " + str(box_time + time_diff))
    #print("local time  : " + str(local_time))

def syncItem(client, item, path):

    box_file_date = datetime.strptime(item['modified_at'][:-6], '%Y-%m-%dT%H:%M:%S') + boxTimeDiff(client, path)
    #print(item['modified_at'])
    local_file = os.stat(path)
    local_file_date_string = datetime.fromtimestamp(local_file.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    local_file_date = datetime.strptime(local_file_date_string, '%Y-%m-%d %H:%M:%S')

    #print(type(box_file_date))
    #print(type(local_file_date))
    print("Box file last modified       : " + str(box_file_date))
    print("Local file last modified     : " + str(local_file_date))

    if(local_file_date > box_file_date):
        print("Updating " + path + "...")
        try:
            #item.update_contents(path)
            to_update = {"modified_at": "2018-06-15T17:26:51-07:00", "name": "FUUUUUUUUUUUUUCK"}
            print(item.update_info(to_update))
            print("Successfully updated " + path)
        except Exception as e:
            print("An error occured: " + e.message)
    elif(local_file_date < box_file_date):
        print("Downloading " + path + "...")

# helpful little script that gives size of terminal
def terminal_size():
    import fcntl, termios, struct
    th, tw, hp, wp = struct.unpack('HHHH',
        fcntl.ioctl(0, termios.TIOCGWINSZ,
        struct.pack('HHHH', 0, 0, 0, 0)))
    return tw, th

#print('Number of columns and Rows: ',terminal_size())

#os.system("ls")

from datetime import datetime

var = os.popen("stat MyFile.txt | grep 'Inode: '[0-9]*").read()
var = var.replace("\t", " ")
array = (var.replace("\t", " ")).split(" ")
print(array[array.index("Inode:")+1])
#item_id = var.replace("Inode: ","")
#print("id: " + item_id)
var = os.popen("sudo debugfs -R 'stat <399438>' /dev/sda1 2> /dev/null | grep 'crtime'.*").read()
#print(var[var.index("--")+3:].replace("\n", ""))

date_str = var[var.index("--")+3:].replace("\n", "")
dt_obj = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
print(dt_obj)
#print(var)
"""
import subprocess
result = subprocess.run(["sudo","debugfs","-R","'stat <399438>'","/dev/sda1"], stdout=subprocess.PIPE)
result.stdout
print(result.stdout)
print(type(result.stdout))
"""


#date = "2018-06-12T09:31:05-07:00"
#utc = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')
#print(utc)
#utc = utc.replace(tzinfo=from_zone)
#central = utc.astimezone(to_zone)
#print(central)