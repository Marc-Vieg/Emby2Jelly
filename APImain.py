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
import re
import requests
import urllib.parse
from configobj import ConfigObj
import os
import time
import sys, getopt
import getpass

def auth_headers(api_key):
    return {
        "Accept": "application/json",
        # Modern Jellyfin/Emby token header. Some Jellyfin versions only accept
        # this one for /Users/{id}/Items, while older ones need the
        # MediaBrowser Authorization header below. Send both.
        "X-Emby-Token": api_key,
        "Authorization": (
            f'MediaBrowser Token="{api_key}", '
            f'Client="Emby2Jelly", '
            f'Device="Python", '
            f'DeviceId="Emby2Jelly", '
            f'Version="1.0"'
        )
    }


def normalise_name(name):
    """Lowercase and strip punctuation so minor naming differences still match."""
    if name is None:
        return ''
    text = str(name).strip().lower()
    # Jellyfin sometimes prefixes episode names with S01E02 / 1x02.
    text = re.sub(r'^[sS]\d{1,2}[eE]\d{1,4}\s*[-._]?\s*', '', text)
    text = re.sub(r'^\d{1,2}x\d{1,4}\s*[-._]?\s*', '', text)
    return re.sub(r'[^a-z0-9]+', '', text)


def provider_id_variants(prov, ident):
    """Yield (provider, id) pairs, including Stremio -> IMDb aliases."""
    if ident is None:
        return
    name = str(prov).strip().lower()
    value = str(ident).strip().lower()
    yield name, value
    if name in ('stremio', 'stremiothumb'):
        # Stremio composite ids look like "tt1234567:0:2".
        match = re.match(r'^(tt\d+)', value)
        if match:
            yield 'imdb', match.group(1)
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

# Cached copy of the administrator's global library, used when Jellyfin refuses
# a per-user Items query (401 Unauthorized for API keys without access to that
# user's view).
_JELLY_GLOBAL_LIBRARY = None
_JELLY_AUTH_OVERRIDE = None  # None = not tried yet, False = unavailable, dict = token headers
_JELLY_USER_HEADERS = {}     # per-user tokens, keyed by Jellyfin user id
_MATCH_DIAGNOSTICS_PRINTED = False


def getConfigOptional(path, section, option, default=None):
    try:
        return ConfigObj(path)[section][option]
    except Exception:
        return default


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
	EMBY_HEADERS = auth_headers(EMBY_APIKEY)

	
	users =  dict()
	
	def emby_get_users_list(EMBY_APIKEY,EMBY_URLBASE,EMBY_HEADERS):

		api_url = f"{EMBY_URLBASE}Users"

		response = requests.get(api_url, headers=EMBY_HEADERS)

		if response.status_code == 200:
			return json.loads(response.content.decode('utf-8'))
		else:
                        print("Status:", response.status_code)
                        print("Response:")
                        print(response.text)
                        sys.exit(1)
	
	
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

				api_url = '{0}Users/{1}/Items?Filters=IsPlayed&IncludeItemTypes=Movie,Episode&Recursive=True'.format(EMBY_URLBASE,user['Id'],EMBY_APIKEY)
				EMBY_HEADERS_Auth = auth_headers(EMBY_APIKEY)
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
						MigrationMedia['Year']=None
						MigrationMedia['SeriesName']=None

						PlayedItem +=1
						api_url = '{0}Users/{1}/Items/{3}'.format(EMBY_URLBASE,user['Id'],EMBY_APIKEY,item['Id'])
						EMBY_HEADERS_Auth = auth_headers(EMBY_APIKEY)
						response = requests.get(api_url, headers=EMBY_HEADERS_Auth)
						if response.status_code == 200:
							itemDto = json.loads(response.content.decode('utf-8'))							
							MigrationMedia['Type']=item['Type']
							MigrationMedia['EmbyId']=item['Id']
							MigrationMedia['JellyId']=''
							MigrationMedia['Name']=item['Name']
							MigrationMedia['Year']=itemDto.get('Year') or item.get('Year')
							MigrationMedia['SeriesName']=itemDto.get('SeriesName') or item.get('SeriesName')
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
	# Headers are resolved lazily by jelly_headers() so an admin login token can
	# be used for every call when credentials are available.


	def jelly_token_headers():
		"""Last-resort auth: log in as a Jellyfin admin to get a user token.

		Some Jellyfin builds accept an API key for /Users and Users/New but
		return 401 Unauthorized for /Users/{id}/Items. Set JELLY_USERNAME (and
		optionally JELLY_PASSWORD) in settings.ini to enable this fallback.
		"""
		global _JELLY_AUTH_OVERRIDE
		if _JELLY_AUTH_OVERRIDE is not None:
			return _JELLY_AUTH_OVERRIDE or None

		username = (os.environ.get('JELLY_USERNAME')
		            or getConfigOptional(path, 'Jelly', 'JELLY_USERNAME', ''))
		password = (os.environ.get('JELLY_PASSWORD')
		            or getConfigOptional(path, 'Jelly', 'JELLY_PASSWORD', ''))
		if not username:
			_JELLY_AUTH_OVERRIDE = False
			return None
		if not password:
			try:
				password = getpass.getpass(prompt='Jellyfin password for {0}: '.format(username))
			except (EOFError, KeyboardInterrupt):
				_JELLY_AUTH_OVERRIDE = False
				return None

		try:
			response = requests.post(
				'{0}Users/AuthenticateByName'.format(JELLY_URLBASE),
				headers={
					'Accept': 'application/json',
					'Content-Type': 'application/json',
					'X-Emby-Authorization': (
						'MediaBrowser Client="Emby2Jelly", Device="Python", '
						'DeviceId="Emby2Jelly", Version="1.0"'
					),
				},
				# This Jellyfin build expects `Pw`; older ones expect `Password`.
				json={'Username': username, 'Password': password, 'Pw': password},
				timeout=30)
			if response.status_code == 200:
				token = response.json().get('AccessToken')
				if token:
					_JELLY_AUTH_OVERRIDE = auth_headers(token)
					print("Authenticated to Jellyfin as {0}".format(username))
					return _JELLY_AUTH_OVERRIDE
			print("Jellyfin login failed: {0} - {1}".format(response.status_code, response.text[:300]))
		except (requests.RequestException, ValueError) as exc:
			print("Jellyfin login error: {0}".format(exc))
		_JELLY_AUTH_OVERRIDE = False
		return None


	def jelly_headers():
		"""Headers for every Jellyfin call.

		Jellyfin API keys are scoped to the user that created them: the
		configured key can read lbeavisc's view but returns 401 for every other
		user. An administrator login token (JELLY_USERNAME/JELLY_PASSWORD) is
		therefore used everywhere when available.
		"""
		if isinstance(_JELLY_AUTH_OVERRIDE, dict):
			return _JELLY_AUTH_OVERRIDE
		if _JELLY_AUTH_OVERRIDE is None:
			jelly_token_headers()
		if isinstance(_JELLY_AUTH_OVERRIDE, dict):
			return _JELLY_AUTH_OVERRIDE
		return auth_headers(JELLY_APIKEY)


	def jelly_login_headers(username, password):
		"""Sign in as a specific Jellyfin user and return token headers."""
		try:
			response = requests.post(
				'{0}Users/AuthenticateByName'.format(JELLY_URLBASE),
				headers={
					'Accept': 'application/json',
					'Content-Type': 'application/json',
					'X-Emby-Authorization': (
						'MediaBrowser Client="Emby2Jelly", Device="Python", '
						'DeviceId="Emby2Jelly", Version="1.0"'
					),
				},
				json={'Username': username, 'Password': password, 'Pw': password},
				timeout=30)
			if response.status_code == 200:
				token = response.json().get('AccessToken')
				if token:
					return auth_headers(token)
			print("Jellyfin login failed for {0}: {1} - {2}".format(
				username, response.status_code, response.text[:200]))
		except (requests.RequestException, ValueError) as exc:
			print("Jellyfin login error for {0}: {1}".format(username, exc))
		return None


	def jelly_user_headers(user):
		"""Headers authenticated as the destination user.

		This Jellyfin build only accepts watched-status writes from the token of
		the user whose data is being changed, even for administrators. When a
		migration password is supplied, the admin token can reset that user's
		password and then we sign in as them. The token is cached per user.
		"""
		global _JELLY_USER_HEADERS
		uid = user.get('Id')
		if uid in _JELLY_USER_HEADERS:
			return _JELLY_USER_HEADERS[uid]

		username = user.get('Name')
		password = set_pw(user.get('Name', '').replace('_', ' '), newUser_pw)
		if not password:
			print("No migration password for {0}; cannot mark its watched status".format(username))
			return None

		admin_headers = jelly_headers()
		reset = requests.post(
			'{0}Users/{1}/Password'.format(JELLY_URLBASE, uid),
			headers=admin_headers,
			json={'NewPw': password},
			timeout=30)
		if reset.status_code not in (200, 204):
			print("Could not set Jellyfin password for {0}: {1} - {2}".format(
				username, reset.status_code, reset.text[:200]))
			return None
		print("Using per-user Jellyfin session for {0} (password set to the migration password)".format(username))

		headers = jelly_login_headers(username, password)
		if headers is not None:
			_JELLY_USER_HEADERS[uid] = headers
		return headers


	def jelly_get_users_list():
		api_url = f"{JELLY_URLBASE}Users"

		response = requests.get(api_url, headers=jelly_headers())
		if response.status_code == 200:
			#print(json.loads(response.content.decode('utf-8')))
			return json.loads(response.content.decode('utf-8'))
		else:
			print("error : {0} - {1}".format(response.status_code, response.text[:300]))
			return []
	
	
	
	
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
				JELLY_HEADERS_usercreate = jelly_headers()

				api_url = '{0}Users/New?'.format(JELLY_URLBASE,JELLY_APIKEY)

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
	
	
	
	def fetch_library(api_url, headers, label, quiet=False):
		"""Fetch an Items endpoint and normalise the response to {'Items': [...]}."""
		try:
			response = requests.get(api_url, headers=headers, timeout=60)
		except requests.RequestException as exc:
			print("error : request failed for {0}: {1}".format(label, exc))
			return None

		if response.status_code != 200:
			if not quiet:
				print("error : {0} - {1} (URL: {2})".format(
					response.status_code, response.text[:300], api_url))
			return None

		try:
			result = response.json()
		except ValueError:
			print("error : non-JSON response for {0}".format(label))
			return None

		if result is None:
			return {"Items": []}
		if isinstance(result, list):
			return {"Items": result}
		if isinstance(result, dict):
			if isinstance(result.get("Items"), list):
				return result
			for key in ("items", "Results"):
				if isinstance(result.get(key), list):
					return {"Items": result[key]}
		print("Unexpected response format for {0}: {1}".format(label, type(result)))
		return None


	def get_userLibrary(user):
		global _JELLY_GLOBAL_LIBRARY
		name = user['Name'].replace("_", " ")
		print("getting jelly DB for {0}".format(name))
		headers = jelly_headers()

		# Ask for extra identifying fields so we can fall back to name+year
		# matching when provider IDs are missing or differ between servers.
		fields = 'ProviderIds,Name,Type,Year,SeriesName'
		item_types = 'Episode,Movie'

		# First try the per-user view. This is what the API is supposed to allow,
		# but Jellyfin rejects it with 401 when the API key is not permitted to
		# read that particular user's view.
		user_url = '{0}Users/{1}/Items?Recursive=True&Fields={2}&IncludeItemTypes={3}&Limit=100000'.format(
			JELLY_URLBASE, user['Id'], fields, item_types)
		# A 401 here is expected on builds that only allow users to read their
		# own view, so probe quietly and fall back to the global library.
		library = fetch_library(user_url, headers, name, quiet=True)
		if library is not None:
			_print_library_diagnostics('per-user ({0})'.format(name), library)
			return library

		# Fallback: the administrator's global library contains every item the
		# per-user view would. Provider-ID matching does not depend on which user
		# the query ran as, so this is safe for migration purposes.
		global_url = '{0}Items?Recursive=True&Fields={1}&IncludeItemTypes={2}&Limit=100000'.format(
			JELLY_URLBASE, fields, item_types)
		if _JELLY_GLOBAL_LIBRARY is None:
			_JELLY_GLOBAL_LIBRARY = fetch_library(global_url, headers, name)
			if _JELLY_GLOBAL_LIBRARY is not None:
				_print_library_diagnostics('global', _JELLY_GLOBAL_LIBRARY)
		if _JELLY_GLOBAL_LIBRARY is not None:
			return _JELLY_GLOBAL_LIBRARY

		# Last resort: authenticate as a Jellyfin user and retry with a real
		# access token (requires JELLY_USERNAME in settings.ini).
		token_headers = jelly_token_headers()
		if token_headers is not None:
			library = fetch_library(user_url, token_headers, name, quiet=True)
			if library is not None:
				_print_library_diagnostics('per-user token ({0})'.format(name), library)
				return library
			_JELLY_GLOBAL_LIBRARY = fetch_library(global_url, token_headers, name)
			if _JELLY_GLOBAL_LIBRARY is not None:
				_print_library_diagnostics('global token', _JELLY_GLOBAL_LIBRARY)
		return _JELLY_GLOBAL_LIBRARY


	def _print_library_diagnostics(label, library):
		"""Print a small sample of a fetched library so matching issues are visible."""
		items = library.get('Items', []) if isinstance(library, dict) else []
		print("[DIAG] {0} library: {1} items".format(label, len(items)))
		for item in items[:3]:
			if isinstance(item, dict):
				print("[DIAG]   {0}: {1} | ProviderIds={2} | Year={3} | SeriesName={4}".format(
					item.get('Type'), item.get('Name'), item.get('ProviderIds'),
					item.get('Year'), item.get('SeriesName')))
		
		

	


	def send_watchedStatus():
		nonlocal report
		admin_name = (os.environ.get('JELLY_USERNAME')
		              or getConfigOptional(path, 'Jelly', 'JELLY_USERNAME', ''))

		for user in jellyUsers:
				
			if (user['Name'].replace("_"," ") in selectedUsers) and (user['Name'] is not None) :
				userName = user['Name'].replace("_"," ")
				report[userName] = {}
				report[userName]['ok'] = 0
				report[userName]['nok'] = []
				report[userName]['failed'] = []
				report[userName]['tosend'] = len(MigrationData.get(userName, []))
				
				toSend = report[userName]['tosend']
				ok 	= 0
				nok = 0
				user_headers = None
				for MigrationMedia in MigrationDataFinal.get(userName, []):
					if MigrationMedia['JellyId'] is not None:
						if user_headers is None:
							# This server only accepts watched-status writes from the
							# user's own token. The admin account can use its login
							# token directly; other users get a per-user session.
							if user['Name'] == admin_name:
								user_headers = jelly_headers()
							else:
								user_headers = jelly_user_headers(user)
						if user_headers is None:
							failure = '{0} -> no user session'.format(MigrationMedia.get('Name'))
							report[userName]['failed'].append(failure)
							continue
						# Modern route; token already identifies the user.
						api_url = '{0}UserPlayedItems/{1}'.format(
							JELLY_URLBASE, MigrationMedia['JellyId'])
						try:
							response = requests.post(api_url, headers=user_headers, timeout=30)
						except requests.RequestException as exc:
							failure = '{0} -> request failed: {1}'.format(MigrationMedia.get('Name'), exc)
							report[userName]['failed'].append(failure)
							print("\033[91merror : {0}\033[00m".format(failure))
							continue
						if response.status_code in (200, 204):
							ok +=1
							report[userName]['ok'] +=1
							print("\033[92mOK ! {2}/{3} - {0} has been seen by {1}\n\033[00m".format(MigrationMedia['Name'], user['Name'], ok, toSend))
							#return
						else:
							failure = '{0} -> {1}: {2}'.format(
								MigrationMedia.get('Name'), response.status_code,
								response.text[:120].replace('\n', ' '))
							report[userName]['failed'].append(failure)
							print("\033[91merror : {0} - {1} (URL: {2})\033[00m".format(
								response.status_code, response.text[:300], api_url))
					else:
						nok +=1
						report[userName]['nok'].append(MigrationMedia)
						print("Couldn't find Id for {0}\n{1}".format(MigrationMedia['Name'], MigrationMedia['ProviderIds']))
	
	
	def search_byName(MigrationMedia,Library):
		items = Library.get('Items', []) if isinstance(Library, dict) else []
		media_type = MigrationMedia.get('Type')
		media_name = MigrationMedia.get('Name')
		media_year = MigrationMedia.get('Year')
		media_series = MigrationMedia.get('SeriesName')
		best = None
		for jelly_movie in items:
			if not isinstance(jelly_movie, dict):
				continue
			if jelly_movie.get('Name') != media_name:
				continue
			if media_type is not None and jelly_movie.get('Type') != media_type:
				continue
			# Prefer an exact year match when both sides have one.
			if (media_year is not None and jelly_movie.get('Year') is not None
					and str(jelly_movie.get('Year')) != str(media_year)):
				continue
			if (media_series is not None and jelly_movie.get('SeriesName') is not None
					and jelly_movie.get('SeriesName') != media_series):
				continue
			print("found by name {0}".format(jelly_movie.get('Name')))
			return jelly_movie.get('Id')
		return best
	
	
	def build_library_index(Library):
		"""Build fast lookup tables for one Jellyfin library fetch."""
		index = {'ids': {}, 'names': {}, 'series_names': {},
		         'names_no_series': {}, 'items': []}
		for item in ((Library or {}).get('Items', []) if isinstance(Library, dict) else []):
			if not isinstance(item, dict):
				continue
			iid = item.get('Id')
			if iid is None:
				continue
			index['items'].append(item)
			media_type = item.get('Type')
			for prov, ident in (item.get('ProviderIds') or {}).items():
				for name, value in provider_id_variants(prov, ident):
					index['ids'].setdefault((name, value), iid)

			name = item.get('Name')
			if name is None:
				continue
			year = (str(item.get('Year')) if item.get('Year') is not None else None)
			lower_name = str(name).strip().lower()
			flat_name = normalise_name(name)
			for key in (
				('exact', media_type, lower_name, year),
				('norm', media_type, flat_name, year),
				('exact', media_type, lower_name, None),
				('norm', media_type, flat_name, None),
			):
				index['names'].setdefault(key, iid)

			series = item.get('SeriesName')
			if series:
				index['series_names'].setdefault(
					(media_type, normalise_name(series), flat_name), iid)
			else:
				# Only use name-only matching for Jellyfin items that have no
				# series information; otherwise "Pilot" matches every series.
				for key in (
					('exact', media_type, lower_name, year),
					('norm', media_type, flat_name, year),
					('exact', media_type, lower_name, None),
					('norm', media_type, flat_name, None),
				):
					index['names_no_series'].setdefault(key, iid)
		return index


	def searchJellyLibrary(MigrationMedia, Library, index=None):
		global _MATCH_DIAGNOSTICS_PRINTED
		if index is None:
			index = build_library_index(Library)

		providers = MigrationMedia.get('ProviderIds') or {}
		# Older --fromfile exports stored providers as "imdb.tt123,tmdb.456"
		if isinstance(providers, str):
			providers = dict(
				(part.strip().split('.', 1)[0].lower(), part.strip().split('.', 1)[1])
				for part in providers.split(',') if '.' in part
			)

		# Provider IDs (including Stremio composite ids -> IMDb aliases).
		for prov, ident in providers.items():
			for name, value in provider_id_variants(prov, ident):
				found = index['ids'].get((name, value))
				if found is not None:
					return found

		media_type = MigrationMedia.get('Type')
		name = MigrationMedia.get('Name')
		year = (str(MigrationMedia.get('Year'))
		        if MigrationMedia.get('Year') is not None else None)
		series = MigrationMedia.get('SeriesName')

		if series is not None and name is not None:
			# Episodes: the series matters. "Pilot" alone is ambiguous.
			found = index['series_names'].get(
				(media_type, normalise_name(series), normalise_name(name)))
			if found is not None:
				print("found by series + name {0} - {1}".format(series, name))
				return found
			# Jellyfin items without SeriesName can still be matched by title,
			# but only when the title is unique in its type.
			for table in (index['names_no_series'],):
				for key in (
					('exact', media_type, str(name).strip().lower(), year),
					('norm', media_type, normalise_name(name), year),
					('exact', media_type, str(name).strip().lower(), None),
					('norm', media_type, normalise_name(name), None),
				):
					if key in table:
						print("found by name (no series in Jellyfin) {0}".format(name))
						return table[key]
		elif name is not None:
			# Movies: name + type, year disambiguates remakes.
			for key in (
				('exact', media_type, str(name).strip().lower(), year),
				('norm', media_type, normalise_name(name), year),
				('exact', media_type, str(name).strip().lower(), None),
				('norm', media_type, normalise_name(name), None),
			):
				found = index['names'].get(key)
				if found is not None:
					print("found by name {0}".format(name))
					return found

		if not _MATCH_DIAGNOSTICS_PRINTED:
			_MATCH_DIAGNOSTICS_PRINTED = True
			print("[DIAG] No match for {0} ({1})".format(
				MigrationMedia.get('Name'), MigrationMedia.get('Type')))
			print("[DIAG]   Wanted provider IDs: {0}".format(providers))
			print("[DIAG]   Normalised name: {0}".format(normalise_name(name)))
			matching_type = [i for i in index['items']
			                 if i.get('Type') == MigrationMedia.get('Type')]
			print("[DIAG]   Library has {0} items of type {1}".format(
				len(matching_type), MigrationMedia.get('Type')))
			for item in matching_type[:3]:
				print("[DIAG]     {0}: ProviderIds={1}".format(
					item.get('Name'), item.get('ProviderIds')))
		return None
		
		
	def iterateMigrationData():
		nonlocal MigrationDataFinal
		for user in (jellyUsers):
			userName = user['Name'].replace("_"," ")
			if userName in selectedUsers:
				MigrationDataFinal[userName] = []
				userItems = MigrationData.get(userName, [])
				Library = get_userLibrary(user)
				library_index = build_library_index(Library) if Library is not None else None
				if Library is None:
					print("ERROR: no Jellyfin library for {0} - {1} item(s) cannot be matched".format(
						userName, len(userItems)))
					if not (os.environ.get('JELLY_USERNAME')
					        or getConfigOptional(path, 'Jelly', 'JELLY_USERNAME', '')):
						print("HINT: Set JELLY_USERNAME and JELLY_PASSWORD in settings.ini [Jelly] "
						      "to authenticate as an admin and unlock library access.")
					for MigrationMedia in userItems:
						MigrationMedia['JellyId'] = None
						MigrationDataFinal[userName].append(MigrationMedia)
					continue
				for MigrationMedia in userItems:
					MigrationMedia['JellyId'] = searchJellyLibrary(
						MigrationMedia, Library, library_index)
					MigrationDataFinal[userName].append(MigrationMedia)
	


	def generate_report():
		nonlocal reportStr
		nonlocal report
		#report['users'] = '..'
		#report[user['Name'].replace("_"," ")]['ok'] = 0
		#report[user['Name'].replace("_"," ")]['nok'] = []
		#report[user['Name'].replace("_"," ")]['tosend'] = 0
		reportStr += "\n\n\n                      ### Emby2Jelly ###\n\n\n"
		reportStr += report['users']
		if newUser_pw:
			reportStr += "\nNOTE: Jellyfin passwords for migrated non-admin users were set to the supplied migration password.\n"
		reportStr += "\n\n"
		for user in jellyUsers:
			if (user['Name'].replace("_"," ") in selectedUsers):
				reportStr += "--- {0} ---\n".format(user['Name'].replace("_"," "))
				userName = user['Name'].replace("_"," ")
				reportStr += "Medias Migrated : {0} / {1}\n".format(
					report[userName]['ok'], report[userName]['tosend'])
				if report[userName]['failed']:
					reportStr += "Could not send {0} media(s) (Jellyfin API error):\n{1}\n".format(
						len(report[userName]['failed']),
						'\n'.join(report[userName]['failed'][:20]))
				if report[userName]['nok'] != []:
					reportStr += "Unfortunately, I Missed {0} Medias :\n{1}\n".format(report[userName]['tosend'] - report[userName]['ok'], list(report[userName]['nok']))
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
			selectedUsers = list(MigrationData.keys())
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

	


