# Emby2Jelly

Python script to recreate users from emby to jellyfin and migrate their watched content for movies and TV shows.

the script work by asking emby what each user's watched list, and then search them on Jellyfin by their ProviderIds (theTvdb, Imdb...)
if ProviderIds are not available, it try to recognize your media by names (`Les Animaux fantastiques : Les Crimes de Grindelwald`) 

***Be sure to have your content identified (It's prefered to refresh missing metadatas on your Library before) ***


Tested with Emby server Version : **4.4.0.40**
and Jellyfin server Version : **10.5.4**


!! Be sure to make emby and Jelly search for missing metadata, Even each Tvshow Episode need to have their providerIds identified to be correctly migrated

---
### Requirements
python3
```
json
collections
requests
urllib.parse
configobj
time
concurrent.futures
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
```

---

## Using
python3 APImain.py 
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

**due to security reason** their is no way by using API that could permit this script to get password, hashed pass etc.. of a user, 

**Each user created will be password-less**

```
Jelly has 0 Users
TestUser ..  Creating
TestUser  Created
Warning ! Password is set to empty !
getting jelly DB for TestUser
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
  WARNING ! Password is empty


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

