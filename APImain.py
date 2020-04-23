import json
import collections
import requests
import urllib.parse
from configobj import ConfigObj
import os
import time



LocalCache = {}
syncCache = {}
jellyUserDb = {}
def getConfig(path, section, option, type):
    config = ConfigObj(path)
    if type == 'str':
        return config[section][option]
    elif type == 'int':
        return config[section].as_int(option)
    elif type == 'bool':
        print('bool : ', section, option, config[section].as_bool(option))
        result = config[section].as_bool(option)
        if result:
            return 1
        else:
            return 0


def exist(path):
    return os.path.exists(path)


def createConfig(path):
    """
    Create a config file
    """
    config = ConfigObj(path)
    EmbySection = {
        'EMBY_APIKEY': 'aaaabbbbbbbcccccccccccccdddddddd',
        'EMBY_URLBASE': 'http://127.0.0.1:8096/emby/'
    }
    config['Emby'] = EmbySection

    JellySection = {
        'JELLY_APIKEY': 'eeeeeeeeeeeeeeeffffffffffffffffggggggggg',
        'JELLY_URLBASE': 'http://127.0.0.1:8096/jellyfin/'
    }
    config['Jelly'] = JellySection

    config.write()












#### On se connecte a MBY pour recuperer la liste des utilisateurs et leurs visionnages ####
def emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS):

	api_url = '{0}Users?api_key={1}'.format(EMBY_URLBASE,EMBY_APIKEY)

	response = requests.get(api_url, headers=EMBY_HEADERS)

	if response.status_code == 200:
		return json.loads(response.content.decode('utf-8'))
	else:
		return "error : " + json.loads(response.content.decode('utf-8'))

def send_users_to_jelly(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS,JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS):
	embyUsers = emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS)
	jellyUsers = jelly_get_users_list(JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS)
	embyList = []
	jellyList = []
	print("Sending Emby Users to Jelly")
	for eUser in embyUsers:
		embyList.append(eUser['Name'])
	for jUser in jellyUsers:
		## Jelly does not accept char space in userNames
		jellyList.append(jUser['Name'])
	#print("JellyList : {0}\nEmbyList : {1}".format(jellyList, embyList))
	for user in embyUsers:
		if user['Name'].replace(" ","_") in jellyList:
			print("\033[92m{0} .. Exists !\033[00m".format(user['Name']))
			continue
		else:
			print("\033[93m{0} ..  Creating\033[00m".format(user['Name']))
			##creating user account
			JELLY_HEADERS_usercreate = {'accept': 'application/json',
										'api_key': '{0}'.format(JELLY_APIKEY),
										'Name': "user['Name']" }

			api_url = '{0}Users/New?&api_key={1}'.format(JELLY_URLBASE,JELLY_APIKEY)

			response = requests.post(api_url, headers=JELLY_HEADERS_usercreate,\
						data={'name': user['Name'].replace(" ","_")})
			if response.status_code == 200:
				print("\033[92m{0}  Created \033[00m".format(user['Name'].replace(" ","_")))
				print("\033[91mWarning ! Password is set to empty !\033[00m")
				
			else:
				print("{1} -- {0}\n\n".format(response.content.decode('utf-8'), response.status_code))
				

def get_watched_status(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS):
	#lister les utilsateurs et leur ID respectives
	i=0
	users = dict()
	users = emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS)
	userTotal = len(users)
	userCount = 0
	print("\033[92mEmby has {0} Users\033[00m".format(userTotal))
	UserPlaylist = {}
	for user in users:
		userCount += 1
		if user['Name'] is not None:
			print("\033[93m{0}\033[00m (\033[93m{2}\033[00m/\033[92m{3}\033[00m) : {1}".format(user['Name'],user['Id'],userCount,userTotal))
			LocalCache[user['Name'].replace(" ","_")]={}
			LocalCache[user['Name'].replace(" ","_")]['EId']="{0}".format(user['Id'])
			LocalCache[user['Name'].replace(" ","_")]['Movies'] = []
			LocalCache[user['Name'].replace(" ","_")]['Episode'] = [] 
			api_url = '{0}Users/{1}/Items?Filters=IsPlayed&IncludeItemTypes=Movie,Episode&Recursive=True&api_key={2}'.format(EMBY_URLBASE,user['Id'],EMBY_APIKEY)
			EMBY_HEADERS_Auth = {'accept': 'application/json',
			   'api_key': '{0}'.format(EMBY_APIKEY)}
			response = requests.get(api_url, headers=EMBY_HEADERS_Auth)   
			if response.status_code == 200:
				UserPlaylist = json.loads(response.content.decode('utf-8'))	
				for item in UserPlaylist["Items"]:
					if item['Type'] == 'Movie':
						LocalCache[user['Name'].replace(" ","_")]['Movies'].append(item['Name'])
					if item['Type'] == 'Episode':
						LocalCache[user['Name'].replace(" ","_")]['Episode'].append(item['Name'])
				with open('db.txt', 'w') as outfile:
					json.dump(LocalCache, outfile)
			else:
				print( "\033[91merror : {0}  =  {1}\033[00m".format(response.status_code,response.content.decode('utf-8')))
			
	print("\n\n\033[92m##### EmbySync Done #####\033[00m\n\n")#{0}".format(LocalCache))
		
		


def jelly_get_users_list(JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS):
	
	api_url = '{0}Users?api_key={1}'.format(JELLY_URLBASE,JELLY_APIKEY)

	response = requests.get(api_url, headers=JELLY_HEADERS)
	if response.status_code == 200:
		return json.loads(response.content.decode('utf-8'))
	else:
		return "error : " + json.loads(response.content.decode('utf-8'))


def jelly_getDb(user):
	
	
		print("\033[96m getting jelly DB for {0}\033[00m".format(user['Name']))
		api_url = '{0}Users/{2}/Items?Recursive=True&SortOrder=Ascending%2CSeries%2CMusicArtist&api_key={1}'.format(\
						JELLY_URLBASE,JELLY_APIKEY,user['Id'])
		JELLY_HEADERS_movie = {'accept': 'application/json',
											'api_key': '{0}'.format(JELLY_APIKEY)}
		response = requests.get(api_url, headers=JELLY_HEADERS_movie)
		if response.status_code == 200:
			return json.loads(response.content.decode('utf-8'))
		else:
			print("error : " + response.content.decode('utf-8'))

def jelly_search_itemId(movie, user,jellyUserDb):
	
	#print(JellyUserDb)
	print("\033[96msearching Jellyfin for {0}\033[00m".format(movie))
	for jelly_movie in jellyUserDb['Items'] :
		if  jelly_movie['Name'] == movie:
			print("found {0}".format(jelly_movie['Name']))
			return jelly_movie
	return None
	



def set_watched_status(JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS):
	users = dict()
	jellyDB = {}
	jellyUserDb = {}
	users = jelly_get_users_list(JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS)
	userTotal = len(users)
	global syncCache

	
	if exist('syncCache.txt'):
		with open('syncCache.txt') as infile:
			syncCache = json.load(infile)
	else:
		for user in users:
			syncCache[user['Name']]={}
			syncCache[user['Name']]['Movies']={}
			syncCache[user['Name']]['Movies']['OK'] = 0
			syncCache[user['Name']]['Movies']['Total'] = 0
			syncCache[user['Name']]['Movies']['Found'] = []
			syncCache[user['Name']]['Movies']['Not Found'] = []
			syncCache[user['Name']]['Episode']={}
			syncCache[user['Name']]['Episode']['OK'] = 0
			syncCache[user['Name']]['Episode']['Total'] = 0
			syncCache[user['Name']]['Episode']['Found'] = []
			syncCache[user['Name']]['Episode']['Not Found'] = []			

			with open('syncCache.txt', 'w') as outfile:
						json.dump(syncCache, outfile) 
	
	### MOVIES
	userCount = 0
	movieCount = 0
	for user in users:
		userCount += 1
		syncCache[user['Name']]={}
		syncCache[user['Name']]['Movies']={}
		syncCache[user['Name']]['Movies']['OK'] = 0
		syncCache[user['Name']]['Movies']['Total'] = 0
		syncCache[user['Name']]['Movies']['Found'] = []
		syncCache[user['Name']]['Movies']['Not Found'] = []
		syncCache[user['Name']]['Episode']={}
		syncCache[user['Name']]['Episode']['OK'] = 0
		syncCache[user['Name']]['Episode']['Total'] = 0
		syncCache[user['Name']]['Episode']['Found'] = []
		syncCache[user['Name']]['Episode']['Not Found'] = []	
		
		
		if exist('syncCache.txt'):
			with open('syncCache.txt') as infile:
				syncCache = json.load(infile)
		if user['Name']  is not None:
			jellyUserDb = jelly_getDb(user)
			for mediaType in ['Movies', 'Episode']:
				
				movieOk = 0
				movieTotal = 0
				movieCount = 0
				movieTotal = len(LocalCache[user['Name']][mediaType])
				syncCache[user['Name'].replace(" ","_")][mediaType]['Total'] = movieTotal
				####
				for movie in LocalCache[user['Name'].replace(" ","_")][mediaType]:
					movieCount +=1
					if movie not in syncCache[user['Name']][mediaType]:

						jelly_movie = jelly_search_itemId(movie, user,jellyUserDb)
						if jelly_movie is not None:
							if jelly_movie['Name'] == movie:
								print("User \033[93m{0}\033[00m/\033[92m{1}\033[00m ({5})\n{4} \033[93m{2}\033[00m/\033[92m{3}\033[00m".format(\
											userCount,userTotal,movieCount,movieTotal, mediaType, user['Name']))
								
								print("\033[96mSending viewed status for : {0} ( id : {1} )\033[00m".format(
											movie,jelly_movie['Id']) )
								JELLY_HEADERS_movie = {'accept': 'application/json',
														'api_key': '{0}'.format(JELLY_APIKEY),
														'item' : json.dumps({'Name' : jelly_movie['Name'],
																			'Id' : jelly_movie['Id'],
																			'Played' : 1 },
																			 separators=(',', ':'))}
								api_url = '{0}Users/{1}/PlayedItems/{2}?api_key={3}'.format(JELLY_URLBASE,user['Id'],jelly_movie['Id'],JELLY_APIKEY)
								response = requests.post(api_url, headers=JELLY_HEADERS_movie)
								if response.status_code == 200:
									print("\033[92mOK ! {0} has been seen by {1}\n\033[00m".format(movie, user['Name']))
									movieOk += 1
									syncCache[user['Name']][mediaType]['Found'].append(movie)
									#return
								else:
									print("\033[91merror : {0}\033[00m".format(response.content.decode('utf-8')))
									
						else:
							print("{0} Not found".format(movie))
							syncCache[user['Name']][mediaType]['Not Found'].append(movie)
					else : 
						print("\033[92m{0}\033[00m \033[93m deja Synchronisé\033[00m".format(movie))
					
				syncCache[user['Name']][mediaType]['OK'] = movieOk

			with open('syncCache.txt', 'w') as outfile:
				json.dump(syncCache, outfile)
	report(syncCache,users)

def report(syncCache, users):
	outstring = []
	for user in users:
		outstring.append("\n----{0}----  \n\n".format(user["Name"]))
		outstring.append("-->I have found {0} movie / {1} Total\n".format(\
			syncCache[user["Name"]]["Movies"]["OK"], syncCache[user["Name"]]["Movies"]["Total"]))
		outstring.append("-->And I have found {0} Episodes / {1} Total\n".format(\
			syncCache[user["Name"]]["Episode"]["OK"], syncCache[user["Name"]]["Episode"]["Total"]))
		
		if syncCache[user["Name"]]["Movies"]["Not Found"] != []:
			outstring.append("I'm sorry, but i have not found these on Jellyfin : \n {0}\n\n".format(syncCache[user["Name"]]["Movies"]["Not Found"]))
		
		if syncCache[user["Name"]]["Episode"]["Not Found"] != []:
			outstring.append("I'm sorry, but i have not found these on Jellyfin : \n {0}\n\n".format(syncCache[user["Name"]]["Episode"]["Not Found"]))
	outstring.append("\n\n This summary is saved in RESULTS.txt \n\n Thank You")
	print(''.join(outstring))
	with open('RESULTS.txt', 'w') as outfile:
		outfile.write(''.join(outstring))
		outfile.close()





if __name__ == "__main__":
	path = "settings.ini"
	if not exist(path):
		createConfig(path)
		print("Please see the README and complete the config\n thank you")
		import sys
		sys.exit()


	EMBY_APIKEY = getConfig(path, 'Emby', 'EMBY_APIKEY', 'str')
	EMBY_URLBASE = getConfig(path, 'Emby', 'EMBY_URLBASE', 'str')
	EMBY_HEADERS = {'accept': 'application/json',
					'api_key': '{0}'.format(EMBY_APIKEY)}   
	JELLY_APIKEY = getConfig(path, 'Jelly', 'JELLY_APIKEY', 'str')
	JELLY_URLBASE = getConfig(path, 'Jelly', 'JELLY_URLBASE', 'str')
	JELLY_HEADERS = {'accept': 'application/json','api_key': '{0}'.format(JELLY_APIKEY)}
	
	
	
	emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS)
	send_users_to_jelly(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS,JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS)
	
	
	get_watched_status(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS)
	
	set_watched_status(JELLY_APIKEY,JELLY_URLBASE,JELLY_HEADERS)
