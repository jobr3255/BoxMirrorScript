from boxsdk import JWTAuth

import json

with open('/home/josh/keys/box/58354353_r2sa3in3_config.json') as f:
    data = json.load(f)

auth = JWTAuth(
    client_id=data['boxAppSettings']['clientID'],
    client_secret=data['boxAppSettings']['clientSecret'],
    enterprise_id=data.get('enterpriseID', None),
    jwt_key_id=data['boxAppSettings']['appAuth'].get('publicKeyID', None),
    #rsa_private_key_data=str(data['boxAppSettings']['appAuth'].get('privateKey', None)),
    rsa_private_key_passphrase=str(data['boxAppSettings']['appAuth'].get('passphrase', None)),
    rsa_private_key_file_sys_path='/home/josh/keys/box/private.pem',
)

#JWTAuth.from_settings_dictionary(data)
#auth = JWTAuth(data)

access_token = auth.authenticate_instance()

from boxsdk import Client

client = Client(auth)

#file = client.file(file_id=297752586807).get()
#print('user_login: ' + file['name'])

user = client.user(user_id=3718623393)
#print('user_name: ' + user['name'])
print(user)

me = client.user(user_id='me').get()
print('user_name: ' + me['name'])
print('user_login: ' + me['login'])
print('user_type: ' + me['type'])
print(me)

items = client.folder(folder_id='0').get_items(limit=100, offset=0)
for i in items:
	itemType = i['type']
	formated_string = ''
	if(itemType == 'folder'):
		formated_string += bcolors.OKBLUE
	formated_string += i['name']
	if(itemType == 'folder'):
		formated_string += bcolors.ENDC
	print(formated_string)

#file = client.folder(folder_id='0').upload("MyFile.txt", file_name="SomeFile.txt")