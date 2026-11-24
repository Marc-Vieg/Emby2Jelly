# Emby2Jelly

Python script to recreate users from emby to jellyfin and migrate their watched content for movies and TV shows.

the script work by asking emby what each user's watched list, and then search them on Jellyfin by their ProviderIds (theTvdb, Imdb...)
if ProviderIds are not available, it try to recognize your media by names (`Les Animaux fantastiques : Les Crimes de Grindelwald`) 

***Be sure to have your content identified (It's prefered to refresh missing metadatas on your Library before) ***


Tested with Emby server Version : **4.4.0.40**
and Jellyfin server Version : **10.5.4**


!! Be sure to make emby and Jelly search for missing metadata, Even each Tvshow Episode need to have their providerIds identified to be correctly migrated

---
### Jellyfin 12.x / per-user authentication

Some newer Jellyfin-compatible servers only accept watched-status writes from the token of the user whose data is being changed. An API key, or even an administrator token, can read the user list and create users but returns `401 Unauthorized` when marking another user's items as played.

When `JELLY_USERNAME` / `JELLY_PASSWORD` are configured for an administrator **and** `--new-user-pw` is supplied, this script:

1. signs in as the administrator;
2. sets each selected non-admin user's Jellyfin password to the `--new-user-pw` value;
3. signs in as that user and writes their watched status using their own token.

> **Warning:** step 2 changes the Jellyfin password of every migrated non-admin user. Tell those users the new password. If you do not want passwords changed, do not pass `--new-user-pw`; only the configured administrator's own watched status can then be migrated on affected servers.

Unmatched media in `RESULTS.txt` usually means the title/episode is not present in the destination Jellyfin library (or its provider IDs do not match), not an authentication problem. Refresh metadata on both servers before migrating.

---
### Requirements
python3
```
json
requests
urllib.parse
configobj
time
getpass
```
## Configuration
simply edit settings.ini with your emby and jelly url and api keys
```
[Emby]
EMBY_APIKEY = aaaabbbbbbbcccccccccccccdddddddd
EMBY_URLBASE = http://127.0.0.1:8096/
[Jelly]
JELLY_APIKEY = eeeeeeeeeeeeeeeffffffffffffffffggggggggg
JELLY_URLBASE = http://127.0.0.1:8096/ 

# do not forget the trailing slash 

## if you have a custom path, or a reverse proxy, do not forget /emby/ or /jelly/ 

## Recommended on servers with per-user watched-status restrictions:
## administrator credentials, used to create users and reset their passwords
# JELLY_USERNAME = admin
# JELLY_PASSWORD = yourpassword
```

> Keep `settings.ini` private: it contains API keys and passwords. Do not commit it.

---

## Using
```
python3 APImain.py 
Migrate from Emby to Jellyfin (or Jellyfin to Jellyfin)
Option Argument : (only one file can be used at a time, one run to a file, then one run from a file)
			--tofile [file]     run the script saving viewed statuses to a file instead of sending them to destination server
			--fromfile [file]       run the script with a file as source server and send viewed statuses to destination server
			--new-user-pw "change-your-password-9efde123"
```

`--new-user-pw` is used both for newly created users and, on servers that require it, as the temporary new password for existing users whose watched status is migrated.

### users
the script will get user list from Emby,

```
[user@computer Emby2Jelly]$ python3 APImain.py 
Emby has 1 Users
TestUser (1 / 1) : aaaabbbbbcccc4555577779999444422

```

### Emby part
then very rapidly, it will get the viewed contend for all users from emby

`##### EmbySync Done #####
`

### Jelly part
the script will work user by user (create them on Jelly if they don't already exist),
asking Jelly for their viewable content 

**When creating users, the script will ask you for password and confirmation.**
```
TestUser ..  Creating
you will now enter password for user TestUser
Password : 
confirm   : 
TestUser  Created
```



Identify your media and tell to jelly the user already seen it


working by name when there is no ProviderId


```
found by name 101 - Towne Hall Follies
found by name 102 - The Quail Hunt

```
Working by Id the major part
```
OK ! 1/17 - 101 - Towne Hall Follies has been seen by TestUser

OK ! 2/17 - Night Mission: Stealing Friends Back has been seen by TestUser

OK ! 3/17 - 102 - The Quail Hunt has been seen by TestUser

OK ! 4/17 - Zombie Island... In Space has been seen by TestUser

OK ! 5/17 - An American Story has been seen by TestUser

OK ! 6/17 - Babysitting Unibaby has been seen by TestUser

OK ! 7/17 - Birthday Month has been seen by TestUser

OK ! 8/17 - The Rabbit Who Broke All the Rules has been seen by TestUser

OK ! 9/17 - No More Bad Guys has been seen by TestUser

OK ! 10/17 - Super Axe has been seen by TestUser

OK ! 11/17 - When Night Creatures Attack has been seen by TestUser

OK ! 12/17 - 28 Days Before has been seen by TestUser

OK ! 13/17 - Taxi Cop has been seen by TestUser

OK ! 14/17 - The Dumb List has been seen by TestUser

OK ! 15/17 - 2 Guns has been seen by TestUser

OK ! 16/17 - 2001 : l'odyssée de l'espace has been seen by TestUser

OK ! 17/17 - Alabama Monroe has been seen by TestUser

```
## Result

The script will generate a RESULTS.txt with summary for each user and a list of the media not found : 
```
                      ### Emby2Jelly ###


TestUser Created on Jelly


--- TestUser ---
Medias Migrated : 17 / 18
Unfortunately, I Missed 1 Medias :
[{'Type': 'Episode', 'EmbyId': '97723', 'JellyId': None, 'Name': 'La Griffe du passé', 'ProviderIds': {'Tvdb': '6218102', 'Imdb': 'tt5989942'}}]
```

### Timing
just start the script, sip a beer and i'll be done
example with a decent user (2986 media seen)

```
$time python3 APImain.py
real	5m22,223s
user	0m43,433s
sys	0m1,485s
```


# CONTRIBUTE

Feel free to contribute however you want, I will be a pleasure !

