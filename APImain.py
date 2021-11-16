# #############################################################################
# Author: CobayeGunther
# Creation Date: 26/04/2020
#
# Description: 	python script to recreate users from emby to jellyfin 
#				and migrate their watched content 
#
# Github Source: https://github.com/CobayeGunther/Emby2Jelly
# Readme Source: https://github.com/CobayeGunther/Emby2Jelly/blob/master/README.md
#
# #############################################################################


import json
import requests
import urllib.parse
from configobj import ConfigObj
import os
import time
import sys, getopt
import getpass 



'''
MigrationData[user['Name']] = []
MigrationMedia={}
MigrationMedia['Type']=''
MigrationMedia['EmbyId']=''
MigrationMedia['JellyId']=''
MigrationMedia['Name']=''
MigrationMedia['ProviderIds']={}
'''
						
						
						


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






def emby(selectedUsers):
	global MigrationData
	EMBY_APIKEY = getConfig(path, 'Emby', 'EMBY_APIKEY', 'str')
	EMBY_URLBASE = getConfig(path, 'Emby', 'EMBY_URLBASE', 'str')
	EMBY_HEADERS = {'accept': 'application/json',
					'api_key': '{0}'.format(EMBY_APIKEY)}

	
	users =  dict()
	
	def emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS):

		api_url = '{0}Users?api_key={1}'.format(EMBY_URLBASE,EMBY_APIKEY)

		response = requests.get(api_url, headers=EMBY_HEADERS)

		if response.status_code == 200:
			return json.loads(response.content.decode('utf-8'))
		else:
			return "error : " + json.loads(response.content.decode('utf-8'))
	
	
	
	
	
	def get_watched_status():
		global MigrationData
		#lister les utilsateurs et leur ID respectives
		i=0
		userCount = 0
		print("\033[92mEmby has {0} Users\033[00m".format(userTotal))
		UserPlaylist = {}
		for user in users:
			userCount += 1
			if (user['Name'] in selectedUsers) and (user['Name'] is not None) :
				MigrationData[user['Name']] = []
				PlayedItem = 0
				print("{0} ({2} / {3}) : {1}".format(user['Name'],user['Id'],userCount,userTotal))

				api_url = '{0}Users/{1}/Items?Filters=IsPlayed&IncludeItemTypes=Movie,Episode&Recursive=True&api_key={2}'.format(EMBY_URLBASE,user['Id'],EMBY_APIKEY)
				EMBY_HEADERS_Auth = {'accept': 'application/json',
				   'api_key': '{0}'.format(EMBY_APIKEY)}
				response = requests.get(api_url, headers=EMBY_HEADERS_Auth)   
				if response.status_code == 200:
					UserPlaylist = json.loads(response.content.decode('utf-8'))	
					for item in UserPlaylist["Items"]:
						MigrationMedia={}
						MigrationMedia['Type']=''
						MigrationMedia['EmbyId']=''
						MigrationMedia['JellyId']=''
						MigrationMedia['Name']=''
						MigrationMedia['ProviderIds']={}

						PlayedItem +=1
						api_url = '{0}Users/{1}/Items/{3}?api_key={2}'.format(EMBY_URLBASE,user['Id'],EMBY_APIKEY,item['Id'])
						EMBY_HEADERS_Auth = {'accept': 'application/json',
						   'api_key': '{0}'.format(EMBY_APIKEY)}
						response = requests.get(api_url, headers=EMBY_HEADERS_Auth)   
						if response.status_code == 200:
							itemDto = json.loads(response.content.decode('utf-8'))							
							MigrationMedia['Type']=item['Type']
							MigrationMedia['EmbyId']=item['Id']
							MigrationMedia['JellyId']=''
							MigrationMedia['Name']=item['Name']
							itemDto["ProviderIds"].pop('sonarr', None)
							MigrationMedia['ProviderIds']=itemDto["ProviderIds"]
							MigrationData[user['Name']].append(MigrationMedia)

				else:
					print( "\033[91merror : {0}  =  {1}\033[00m".format(response.status_code,response.content.decode('utf-8')))
				
		print("\n\n\033[92m##### EmbySync Done #####\033[00m\n\n")
		
		

	users = emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS)
	if selectedUsers ==[]:
		for user in users:
			selectedUsers.append(user['Name'])
	
	userTotal = len(users)
	get_watched_status()


	
	
	
def jelly(newUser_pw):
	reportStr = ''
	report = {}


	JELLY_APIKEY = getConfig(path, 'Jelly', 'JELLY_APIKEY', 'str')
	JELLY_URLBASE = getConfig(path, 'Jelly', 'JELLY_URLBASE', 'str')
	JELLY_HEADERS = {'accept': 'application/json','api_key': '{0}'.format(JELLY_APIKEY)}
	
	def jelly_get_users_list():
		api_url = '{0}Users?api_key={1}'.format(JELLY_URLBASE,JELLY_APIKEY)

		response = requests.get(api_url, headers=JELLY_HEADERS)
		if response.status_code == 200:
			#print(json.loads(response.content.decode('utf-8')))
			return json.loads(response.content.decode('utf-8'))
		else:
			return "error : " + json.loads(response.content.decode('utf-8'))
	
	
	
	
	def compare_users():
		
		print("\033[96mJelly has {0} Users\033[00m".format(userTotal))

		nonlocal JellyUsersIdDict
		nonlocal report

		report['users'] = ''
		JellyUsersIdDict['Name'] = 0
		embyList = []
		jellyList = []
		for eUser in MigrationData:
			embyList.append(eUser)
		for jUser in jellyUsers: 
			JellyUsersIdDict[jUser['Name']] = jUser['Id']
			## Jelly does not accept char space in userNames
		for eUser in MigrationData:
			if eUser.replace(" ","_") in JellyUsersIdDict.keys():
				print("Jelly already knows {0} (Id {1})".format(eUser.replace(" ","_"), JellyUsersIdDict[eUser.replace(" ","_")] ))
				report['users'] += "{0} (Emby) is  {1} (Jelly)\n".format(eUser, eUser.replace(" ","_"))
			else:
				print("{0} ..  Creating".format(eUser))
				##creating user account
				JELLY_HEADERS_usercreate = {'accept': 'application/json',
											'api_key': '{0}'.format(JELLY_APIKEY)}

				api_url = '{0}Users/New?&api_key={1}'.format(JELLY_URLBASE,JELLY_APIKEY)

				response = requests.post(api_url, headers=JELLY_HEADERS_usercreate,\
							json={'name': eUser.replace(" ","_"), 'Password' : set_pw(eUser.replace(" ","_"),newUser_pw)})
				if response.status_code == 200:
					print("{0}  Created".format(eUser.replace(" ","_")))
					report['users'] += "{0} Created on Jelly".format(eUser, eUser.replace(" ","_"))

					
				else:
					print("{1} -- {0}\n\n".format(response.content.decode('utf-8'), response.status_code))
		#uptade the jelly Users in case we created one

	'''
	
	### I originaly wanted to ask Jellyfin server for Any item matching the provider ID of the MigrationMedia,
	### But it seems the Jellyfin api dont implement this (seen this in emby api "documentation")
	def normalise_MigrationData():
		
		
		#MigrationData[user['Name']] = []
		#MigrationMedia={}
		#MigrationMedia['Type']=''
		#MigrationMedia['EmbyId']=''
		#MigrationMedia['JellyId']=''
		#MigrationMedia['Name']=''
		#MigrationMedia['ProviderIds']={}
		
		
		
		nonlocal NormalizedMigrationData
		#print(jellyUsers)
		for user in jellyUsers:
			if (user['Name'].replace("_"," ") in selectedUsers):
				
				NormalizedMigrationData[user['Name'].replace("_"," ")] = []
				
				for MigrationMedia in MigrationData[user['Name'].replace("_"," ")]:
					#if type(MigrationMedia['ProviderIds']) != str:
					print(MigrationMedia)
					#MigrationData[user['Name'].replace("_"," ")].remove(MigrationMedia)
					normalisedProviderIds =''
					for Provider in MigrationMedia['ProviderIds'].keys():
						print("p = {0}, id = {1}".format(Provider, MigrationMedia['ProviderIds'][Provider]))
						if normalisedProviderIds == '':
							normalisedProviderIds = str("{0}.{1}".format(Provider.lower(),MigrationMedia['ProviderIds'][Provider]))
						else:
							normalisedProviderIds += str(",{0}.{1}".format(Provider.lower(),MigrationMedia['ProviderIds'][Provider]))
					#print(normalisedProviderIds)
					MigrationMedia['ProviderIds'] = normalisedProviderIds
					NormalizedMigrationData[user['Name'].replace("_"," ")].append(MigrationMedia)
					#else:
					#	continue
	'''
	
	
	
	def get_userLibrary(user):
		user['Name'].replace("_"," ")
		print("getting jelly DB for {0}".format(user['Name']))
		api_url = '{0}Users/{2}/Items?Recursive=True&Fields=ProviderIds&IncludeItemTypes=Episode,Movie&api_key={1}'.format(\
						JELLY_URLBASE,JELLY_APIKEY,user['Id'])
		JELLY_HEADERS_movie = {'accept': 'application/json',
											'api_key': '{0}'.format(JELLY_APIKEY)}
		response = requests.get(api_url, headers=JELLY_HEADERS_movie)
		if response.status_code == 200:
			#print(json.loads(response.content.decode('utf-8')))
			return json.loads(response.content.decode('utf-8'))
		else:
			print("error : " + response.content.decode('utf-8'))
		
		

	


	def send_watchedStatus():
		nonlocal report
		
		for user in jellyUsers:
				
			if (user['Name'].replace("_"," ") in selectedUsers) and (user['Name'] is not None) :
				report[user['Name'].replace("_"," ")] = {}
				report[user['Name'].replace("_"," ")]['ok'] = 0
				report[user['Name'].replace("_"," ")]['nok'] = []
				report[user['Name'].replace("_"," ")]['tosend'] = 0
				
				toSend = len(MigrationData[user['Name'].replace("_"," ")])
				report[user['Name'].replace("_"," ")]['tosend'] = toSend
				ok 	= 0
				nok = 0
				for MigrationMedia in MigrationDataFinal[user['Name'].replace("_"," ")]:
					if MigrationMedia['JellyId'] is not None:
						JELLY_HEADERS_movie = {'accept': 'application/json',
													'api_key': '{0}'.format(JELLY_APIKEY),
													'item' : json.dumps({'Name' : MigrationMedia['Name'],
																		'Id' : MigrationMedia['JellyId'],
																		'Played' : 1 },
																		 separators=(',', ':'))}
						api_url = '{0}Users/{1}/PlayedItems/{2}?api_key={3}'.format(JELLY_URLBASE,user['Id'],MigrationMedia['JellyId'],JELLY_APIKEY)
						response = requests.post(api_url, headers=JELLY_HEADERS_movie)
						if response.status_code == 200:
							ok +=1
							report[user['Name'].replace("_"," ")]['ok'] +=1
							print("\033[92mOK ! {2}/{3} - {0} has been seen by {1}\n\033[00m".format(MigrationMedia['Name'], user['Name'], ok, toSend))
							#return
						else:
							print("\033[91merror : {0}\033[00m".format(response.content.decode('utf-8')))
					else:
						nok +=1
						report[user['Name'].replace("_"," ")]['nok'].append(MigrationMedia)
						print("Couldn't find Id for {0}\n{1}".format(MigrationMedia['Name'], MigrationMedia['ProviderIds']))
	
	
	def search_byName(MigrationMedia,Library):

		for jelly_movie in Library['Items'] :
			if  jelly_movie['Name'] == MigrationMedia['Name']:
				print("found by name {0}".format(jelly_movie['Name']))
				return jelly_movie['Id']
		return None
	
	
	def searchJellyLibrary(MigrationMedia, Library):
		for Item in Library['Items']:
			if Item["Type"] != MigrationMedia["Type"]:
				continue

			for itProv, itId in Item['ProviderIds'].items():
				for prov, id in MigrationMedia['ProviderIds'].items():
					if itProv.lower() == prov.lower() and itId == id:
						return Item['Id']
		return None
		
		
	def iterateMigrationData():
		Library = {}
		nonlocal MigrationDataFinal
		for user in (jellyUsers):
			if (user['Name'].replace("_"," ") in selectedUsers):
				MigrationDataFinal[user['Name'].replace("_"," ")] = []
				Library = get_userLibrary(user)
				for MigrationMedia in MigrationData[user['Name'].replace("_"," ")]:
					MigrationMedia['JellyId'] = searchJellyLibrary(MigrationMedia, Library)
					if MigrationMedia['JellyId'] is None:
						MigrationMedia['JellyId'] = search_byName(MigrationMedia,Library)
					MigrationDataFinal[user['Name'].replace("_"," ")].append(MigrationMedia)
	


	def generate_report():
		nonlocal reportStr
		nonlocal report
		#report['users'] = '..'
		#report[user['Name'].replace("_"," ")]['ok'] = 0
		#report[user['Name'].replace("_"," ")]['nok'] = []
		#report[user['Name'].replace("_"," ")]['tosend'] = 0
		reportStr += "\n\n\n                      ### Emby2Jelly ###\n\n\n"
		reportStr += report['users']
		reportStr += "\n\n"
		for user in jellyUsers:
			if (user['Name'].replace("_"," ") in selectedUsers):
				reportStr += "--- {0} ---\n".format(user['Name'].replace("_"," "))
				reportStr += "Medias Migrated : {0} / {1}\n".format(report[user['Name'].replace("_"," ")]['ok'],report[user['Name'].replace("_"," ")]['tosend']) 
				if report[user['Name'].replace("_"," ")]['nok'] != []:
					reportStr += "Unfortunately, I Missed {0} Medias :\n{1}\n".format(report[user['Name'].replace("_"," ")]['tosend'] - report[user['Name'].replace("_"," ")]['ok'], list(report[user['Name'].replace("_"," ")]['nok']))
		with open('RESULTS.txt', 'w') as outfile:
			outfile.write(''.join(reportStr))
			outfile.close()
		
		
		
		
		
	
	def set_pw(u,newUser_pw):
		p1 = "p1"
		p2 = "p2"
		if newUser_pw is not None:
			return newUser_pw
		while 1:
			print("\nEnter password for user {0}".format(u))
			p1 = getpass.getpass(prompt='Password : ') 
			p2 = getpass.getpass(prompt='confirm   : ') 
			if p1==p2:
				if p1 == "":
					print("Warning ! Password is set to empty !")
				return p1
			else:
				print("passwords does not match \n")
				

	
				
	MigrationDataFinal = {}
	JellyUsersIdDict = {}
	NormalizedMigrationData = {}
	jellyUsers = jelly_get_users_list()
	userTotal = len(jellyUsers)
	compare_users()
	#uptade the jelly Users in case we created one
	jellyUsers = jelly_get_users_list()
	userTotal = len(jellyUsers)
	iterateMigrationData()
	send_watchedStatus()
	
	generate_report()
	
	



if __name__ == "__main__":
	path = "settings.ini"
	if not exist(path):
		createConfig(path)
		print("Please see the README and complete the config\n thank you")

		sys.exit()
		
		
		
	global MigrationData
	MigrationData = {}
	selectedUsers = []
	
	argv = sys.argv[1:]
	tofile = None
	fromfile = None
	newUser_pw = None
	MigrationFile = None
	try:
		opts, args = getopt.getopt(argv,"",["tofile=","fromfile=","new-user-pw="])
	except getopt.GetoptError:
		print('python3 APImain.py\n\nMigrate from Emby to Jellyfin (or Jellyfin to Jellyfin)\n')
		print('--tofile [file]     run the script saving viewed statuses to a file instead of sending them to destination server')
		print('--fromfile [file]       run the script with a file as source server and send viewed statuses to destination server')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('python3 APImain.py\n\nMigrate from Emby to Jellyfin (or Jellyfin to Jellyfin)\n')
			print('--tofile [file]     run the script saving viewed statuses to a file instead of sending them to destination server')
			print('--fromfile [file]       run the script with a file as source server and send viewed statuses to destination server')
			sys.exit()
		elif opt == "--tofile":
			tofile = arg
		elif opt == "--fromfile":
			fromfile = arg
		elif opt == "--new-user-pw":
			newUser_pw = arg


	if tofile != None:
		print ('Migration to file {0}'.format(tofile))
		try :
			MigrationFile = open(tofile, 'w')
		except : 
			print("cannot open file {0}".format(tofile))
			sys.exit(1)

	elif fromfile != None:
		print ('Migration from file {0}'.format(fromfile))
		try :
			MigrationFile = open(fromfile, 'r')
			MigrationData = json.loads(MigrationFile.read())
			#print(MigrationData)
		except : 
			print("cannot open file {0}".format(tofile))
			sys.exit(1)
	else:
		print("no file specified, will run from source server to destination server")


	
	if fromfile is None:
		emby(selectedUsers)	
		if tofile is not None:
			MigrationFile.write(json.dumps(MigrationData))
			MigrationFile.close()
			sys.exit(1)
	
	if tofile is None:
		jelly(newUser_pw)
	if MigrationFile is not None:
		MigrationFile.close()
	sys.exit(1)

	
