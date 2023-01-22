# #############################################################################
# Author: CobayeGunther
# Creation Date: 26/04/2020
#
# Description:     python script to recreate users from emby to jellyfin
#                 and migrate their watched content
#
# Github Source: https://github.com/CobayeGunther/Emby2Jelly
# Readme Source: https://github.com/CobayeGunther/Emby2Jelly/blob/master/README.md
#
# #############################################################################


import argparse
import getpass
import json
import logging
import requests
import sys
from configparser import ConfigParser


'''
migration_data[user['Name']] = []
migration_media={}
migration_media['Type']=''
migration_media['EmbyId']=''
migration_media['JellyId']=''
migration_media['Name']=''
migration_media['ProviderIds']={}
'''


def createConfig(file_obj):
    """
    Create a config file
    """
    config = ConfigParser()
    EmbySection = {'EMBY_APIKEY': 'aaaabbbbbbbcccccccccccccdddddddd', 'EMBY_URLBASE': 'http://127.0.0.1:8096/emby/'}
    config['Emby'] = EmbySection

    JellySection = {
        'JELLY_APIKEY': 'eeeeeeeeeeeeeeeffffffffffffffffggggggggg',
        'JELLY_URLBASE': 'http://127.0.0.1:8096/jellyfin/',
    }
    config['Jelly'] = JellySection

    config.write(file_obj)


def decode_response(response, log=None):
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        try:
            error_text = "Error {http_code}: {output}".format(
                http_code=response.status_code, output=json.loads(response.content.decode("utf-8"))
            )
            if log:
                log.error(error_text)
            else:
                return error_text
        except Exception as e:
            content = response.content.decode('utf-8')
            error_text = "Error {http_code} ({response}) decoding '{content}': {e}".format(
                e=e, http_code=response.status_code, content=content, response=response.reason
            )
            if log:
                log.error(error_text)
            else:
                return error_text


def emby(migration_data, selected_users, config_file, log, emby_apikey, emby_urlbase):
    emby_headers = {'accept': 'application/json', 'api_key': '{0}'.format(emby_apikey)}

    users = dict()

    def emby_get_users_list(emby_apikey, emby_urlbase, emby_headers):

        api_url = '{0}Users?api_key={1}'.format(emby_urlbase, emby_apikey)

        response = requests.get(api_url, headers=emby_headers)

        return decode_response(response)

    def get_watched_status():
        # lister les utilsateurs et leur ID respectives
        userCount = 0
        log.debug("\033[92mEmby has {0} Users\033[00m".format(user_total))
        user_playlist = {}
        for user in users:
            userCount += 1
            if (user['Name'] in selected_users) and (user['Name'] is not None):
                migration_data[user['Name']] = []
                played_item = 0
                log.debug("{0} ({2} / {3}) : {1}".format(user['Name'], user['Id'], userCount, user_total))

                api_url = '{0}Users/{1}/Items?{2}'.format(
                    emby_urlbase,
                    user['Id'],
                    "&".join(
                        [
                            "Filters=IsPlayed",
                            "IncludeItemTypes=Movie,Episode",
                            "Recursive=True",
                            "api_key={}".format(emby_apikey),
                        ]
                    ),
                )
                emby_headers_auth = {'accept': 'application/json', 'api_key': '{0}'.format(emby_apikey)}
                response = requests.get(api_url, headers=emby_headers_auth)
                if response.status_code == 200:
                    user_playlist = json.loads(response.content.decode('utf-8'))
                    for item in user_playlist["Items"]:
                        migration_media = {}
                        migration_media['Type'] = ''
                        migration_media['EmbyId'] = ''
                        migration_media['JellyId'] = ''
                        migration_media['Name'] = ''
                        migration_media['ProviderIds'] = {}

                        played_item += 1
                        api_url = '{0}Users/{1}/Items/{3}?api_key={2}'.format(
                            emby_urlbase, user['Id'], emby_apikey, item['Id']
                        )
                        # emby_headers_auth = {'accept': 'application/json', 'api_key': '{0}'.format(emby_apikey)}
                        response = requests.get(api_url, headers=emby_headers_auth)
                        if response.status_code == 200:
                            itemDto = json.loads(response.content.decode('utf-8'))
                            migration_media['Type'] = item['Type']
                            migration_media['EmbyId'] = item['Id']
                            migration_media['JellyId'] = ''
                            migration_media['Name'] = item['Name']
                            itemDto["ProviderIds"].pop('sonarr', None)
                            migration_media['ProviderIds'] = itemDto["ProviderIds"]
                            migration_data[user['Name']].append(migration_media)

                else:
                    log.error(
                        "\033[91merror : {0}  =  {1}\033[00m".format(
                            response.status_code, response.content.decode('utf-8')
                        )
                    )

        log.info("\n\n\033[92m##### EmbySync Done #####\033[00m\n\n")

    users = emby_get_users_list(emby_apikey, emby_urlbase, emby_headers)
    if selected_users == []:
        try:
            log.info(users.strip())
            return
        except AttributeError:
            pass
        for user in users:
            selected_users.append(user['Name'])

    user_total = len(users)
    get_watched_status()


def jelly(migration_data, new_user_pw, config_file, selected_users, log, jelly_apikey, jelly_urlbase):
    report_str = ''
    report = {}

    jelly_headers = {'accept': 'application/json', 'api_key': '{0}'.format(jelly_apikey)}

    def jelly_get_users_list():
        api_url = '{0}Users?api_key={1}'.format(jelly_urlbase, jelly_apikey)

        response = requests.get(api_url, headers=jelly_headers)
        return decode_response(response)

    def compare_users():

        log.info("\033[96mJelly has {0} Users\033[00m".format(user_total))

        nonlocal jelly_users_id_dict
        nonlocal report

        report['users'] = ''
        jelly_users_id_dict['Name'] = 0
        embyList = []
        for eUser in migration_data:
            embyList.append(eUser)
        for jUser in jelly_users:
            jelly_users_id_dict[jUser['Name']] = jUser['Id']
            # Jelly does not accept char space in userNames
        for eUser in migration_data:
            if eUser.replace(" ", "_") in jelly_users_id_dict.keys():
                log.info(
                    "Jelly already knows {0} (Id {1})".format(
                        eUser.replace(" ", "_"), jelly_users_id_dict[eUser.replace(" ", "_")]
                    )
                )
                report['users'] += "{0} (Emby) is  {1} (Jelly)\n".format(eUser, eUser.replace(" ", "_"))
            else:
                log.info("{0} ..  Creating".format(eUser))
                # creating user account
                jelly_headers_usercreate = {'accept': 'application/json', 'api_key': '{0}'.format(jelly_apikey)}

                api_url = '{0}Users/New?&api_key={1}'.format(jelly_urlbase, jelly_apikey)

                response = requests.post(
                    api_url,
                    headers=jelly_headers_usercreate,
                    json={'name': eUser.replace(" ", "_"), 'Password': set_pw(eUser.replace(" ", "_"), new_user_pw)},
                )
                if response.status_code == 200:
                    text = "{0}  Created".format(eUser.replace(" ", "_"))
                    log.info(text)
                    report['users'] += "{} on Jelly".format(text)

                else:
                    log.info("{1} -- {0}\n\n".format(response.content.decode('utf-8'), response.status_code))
        # update the jelly Users in case we created any

    '''
    ### I originaly wanted to ask Jellyfin server for Any item matching the provider ID of the migration_media,
    ### But it seems the Jellyfin api doesn't implement this (seen this in emby api "documentation")
    def normalise_migration_data():


        #migration_data[user['Name']] = []
        #migration_media={}
        #migration_media['Type']=''
        #migration_media['EmbyId']=''
        #migration_media['JellyId']=''
        #migration_media['Name']=''
        #migration_media['ProviderIds']={}

        nonlocal normalized_migration_data
        #log.debug(jelly_users)
        for user in jelly_users:
            if (user['Name'].replace("_"," ") in selected_users):

                normalized_migration_data[user['Name'].replace("_"," ")] = []

                for migration_media in migration_data[user['Name'].replace("_"," ")]:
                    #if type(migration_media['ProviderIds']) != str:
                    log.info(migration_media)
                    #migration_data[user['Name'].replace("_"," ")].remove(migration_media)
                    normalisedProviderIds = [
                        "{}.{}".format(k.lower(), v) for k, v in migration_media['ProviderIds'].items()
                    ]
                    log.debug("\n".join(normalisedProviderIds))
                    migration_media['ProviderIds'] = ",".join(normalisedProviderIds)
                    normalized_migration_data[user['Name'].replace("_"," ")].append(migration_media)
                    #else:
                    #    continue
    '''

    def get_user_library(user):
        user['Name'].replace("_", " ")
        log.debug("getting jelly DB for {0}".format(user['Name']))
        api_url = (
            '{0}Users/{2}/Items?Recursive=True&Fields=ProviderIds&IncludeItemTypes=Episode,Movie&api_key={1}'.format(
                jelly_urlbase, jelly_apikey, user['Id']
            )
        )
        jelly_headers_movie = {'accept': 'application/json', 'api_key': '{0}'.format(jelly_apikey)}
        response = requests.get(api_url, headers=jelly_headers_movie)
        return decode_response(response, log)

    def send_watched_status():
        nonlocal report

        for user in jelly_users:

            if (user['Name'].replace("_", " ") in selected_users) and (user['Name'] is not None):
                report[user['Name'].replace("_", " ")] = {}
                report[user['Name'].replace("_", " ")]['ok'] = 0
                report[user['Name'].replace("_", " ")]['nok'] = []
                report[user['Name'].replace("_", " ")]['tosend'] = 0

                toSend = len(migration_data[user['Name'].replace("_", " ")])
                report[user['Name'].replace("_", " ")]['tosend'] = toSend
                ok = 0
                nok = 0
                for migration_media in migration_data_final[user['Name'].replace("_", " ")]:
                    if migration_media['JellyId'] is not None:
                        jelly_headers_movie = {
                            'accept': 'application/json',
                            'api_key': '{0}'.format(jelly_apikey),
                            'item': json.dumps(
                                {'Name': migration_media['Name'], 'Id': migration_media['JellyId'], 'Played': 1},
                                separators=(',', ':'),
                            ),
                        }
                        api_url = '{0}Users/{1}/played_items/{2}?api_key={3}'.format(
                            jelly_urlbase, user['Id'], migration_media['JellyId'], jelly_apikey
                        )
                        response = requests.post(api_url, headers=jelly_headers_movie)
                        if response.status_code == 200:
                            ok += 1
                            report[user['Name'].replace("_", " ")]['ok'] += 1
                            log.debug(
                                "\033[92mOK ! {2}/{3} - {0} has been seen by {1}\n\033[00m".format(
                                    migration_media['Name'], user['Name'], ok, toSend
                                )
                            )
                            # return
                        else:
                            log.error("\033[91merror: '{0}'\033[00m".format(response.content.decode('utf-8')))
                    else:
                        nok += 1
                        report[user['Name'].replace("_", " ")]['nok'].append(migration_media)
                        log.error(
                            "Couldn't find Id for {0}\n{1}".format(
                                migration_media['Name'], migration_media['ProviderIds']
                            )
                        )

    def search_byName(migration_media, Library):

        for jelly_movie in Library['Items']:
            if jelly_movie['Name'] == migration_media['Name']:
                log.debug("found by name {0}".format(jelly_movie['Name']))
                return jelly_movie['Id']
        return None

    def search_jelly_library(migration_media, library):
        for item in library['Items']:
            if item["Type"] != migration_media["Type"]:
                continue

            for it_prov, it_id in item['ProviderIds'].items():
                for prov_name, prov_id in migration_media['ProviderIds'].items():
                    if it_prov.lower() == prov_name.lower() and it_id == prov_id:
                        return item['Id']
        return None

    def iterate_migration_data():
        library = {}
        nonlocal migration_data_final
        for user in jelly_users:
            if user['Name'].replace("_", " ") in selected_users:
                migration_data_final[user['Name'].replace("_", " ")] = []
                library = get_user_library(user)
                for migration_media in migration_data[user['Name'].replace("_", " ")]:
                    migration_media['JellyId'] = search_jelly_library(migration_media, library)
                    if migration_media['JellyId'] is None:
                        migration_media['JellyId'] = search_byName(migration_media, library)
                    migration_data_final[user['Name'].replace("_", " ")].append(migration_media)

    def generate_report():
        nonlocal report_str
        nonlocal report
        # report['users'] = '..'
        # report[user['Name'].replace("_"," ")]['ok'] = 0
        # report[user['Name'].replace("_"," ")]['nok'] = []
        # report[user['Name'].replace("_"," ")]['tosend'] = 0
        report_str += "\n\n\n                      ### Emby2Jelly ###\n\n\n"
        report_str += report['users']
        report_str += "\n\n"
        for user in jelly_users:
            if user['Name'].replace("_", " ") in selected_users:
                report_str += "--- {0} ---\n".format(user['Name'].replace("_", " "))
                report_str += "Medias Migrated : {0} / {1}\n".format(
                    report[user['Name'].replace("_", " ")]['ok'], report[user['Name'].replace("_", " ")]['tosend']
                )
                if report[user['Name'].replace("_", " ")]['nok'] != []:
                    report_str += "Unfortunately, I Missed {0} Medias :\n{1}\n".format(
                        report[user['Name'].replace("_", " ")]['tosend'] - report[user['Name'].replace("_", " ")]['ok'],
                        list(report[user['Name'].replace("_", " ")]['nok']),
                    )
        with open('RESULTS.txt', 'w') as outfile:
            outfile.write(''.join(report_str))
            outfile.close()

    def set_pw(u, new_user_pw):
        p1 = "p1"
        p2 = "p2"
        if new_user_pw is not None:
            return new_user_pw
        while 1:
            log.info("\nEnter password for user {0}".format(u))
            p1 = getpass.getpass(prompt='Password : ')
            p2 = getpass.getpass(prompt='confirm   : ')
            if p1 == p2:
                if p1 == "":
                    log.warning("Warning ! Password is set to empty !")
                return p1
            else:
                log.error("passwords does not match \n")

    migration_data_final = {}
    jelly_users_id_dict = {}
    # normalized_migration_data = {}
    jelly_users = jelly_get_users_list()
    user_total = len(jelly_users)
    compare_users()
    # update the jelly Users in case we created any
    jelly_users = jelly_get_users_list()
    user_total = len(jelly_users)
    iterate_migration_data()
    send_watched_status()

    generate_report()


def setup_logging(app_name, verbose, quiet):
    log = logging.getLogger(app_name)
    stdout_handler = logging.StreamHandler(sys.stdout)
    log.addHandler(stdout_handler)
    if verbose:
        loglevel = logging.DEBUG
    elif quiet:
        loglevel = logging.ERROR
    else:
        loglevel = logging.INFO
    log.setLevel(loglevel)
    return log


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Migrate from Emby to Jellyfin (or Jellyfin to Jellyfin)")
    g = parser.add_mutually_exclusive_group()
    g.add_argument(
        "--config",
        "-c",
        default="settings.ini",
        type=argparse.FileType('r'),
        help="Config file to read endpoints and API keys, See README",
    )
    g.add_argument(
        "--tofile",
        "-t",
        type=argparse.FileType('w'),
        help="run the script saving viewed statuses to a file instead of sending them to destination server",
    )
    g.add_argument(
        "--fromfile",
        "-f",
        type=argparse.FileType('r'),
        help="run the script with a file as source server and send viewed statuses to destination serve",
    )
    parser.add_argument("--new-user-pw", "-p")
    g = parser.add_mutually_exclusive_group()
    g.add_argument('-q', '--quiet', action='store_true')
    g.add_argument('-v', '--verbose', action='store_true')
    cfg = parser.parse_args(argv)
    cfg.log = setup_logging(__name__, cfg.verbose, cfg.quiet)
    return cfg


def getConfig(file_obj, section, option, type, log):
    config = ConfigParser()
    config.read_file(file_obj)
    log.debug("Read config from{}: {}".format(file_obj, dict(config)))
    if type == 'str':
        return config[section][option]
    elif type == 'int':
        return int(config[section][option])
    elif type == 'bool':
        result = config[section][option].lower() == 'true'
        log.debug('bool : ', section, option, result)
        if result:
            return 1
        else:
            return 0


def main(argv=None):
    migration_data = {}
    selected_users = []

    argv = sys.argv[1:] if argv is None else argv
    cfg = parse_args(argv)
    config_file = cfg.config
    app_config = ConfigParser()
    app_config.read_file(config_file)
    cfg.log.debug("Read config from {}: {}".format(config_file, dict(app_config)))

    migration_file = None

    if cfg.tofile is not None:
        cfg.log.info("Migration to file {}".format(cfg.tofile))
        migration_file = cfg.tofile

    elif cfg.fromfile is not None:
        cfg.log.info("Migration from file {}".format(cfg.fromfile))
        file_content = None
        migration_file = cfg.fromfile
        try:
            file_content = migration_file.read()
            migration_data = json.loads(file_content)
        except Exception as e:
            cfg.log.info("Error reading or decoding file {} content '{}': {}".format(cfg.tofile, file_content, e))
            return 1
    else:
        cfg.log.info("No file specified: will run from source server to destination server")

    if cfg.fromfile is None:
        emby(
            migration_data=migration_data,
            selected_users=selected_users,
            config_file=config_file,
            log=cfg.log,
            emby_apikey=app_config['Emby']['EMBY_APIKEY'],
            emby_urlbase=app_config['Emby']['EMBY_URLBASE'],
        )
        if cfg.tofile is not None:
            migration_file.write(json.dumps(migration_data))
            migration_file.close()
            return 0

    if cfg.tofile is None:
        jelly(
            migration_data=migration_data,
            new_user_pw=cfg.new_user_pw,
            config_file=config_file,
            selected_users=selected_users,
            log=cfg.log,
            jelly_apikey=app_config['Jelly']['JELLY_APIKEY'],
            jelly_urlbase=app_config['Jelly']['JELLY_URLBASE'],
        )
    if migration_file is not None:
        migration_file.close()
    return 0


if __name__ == "__main__":
    main()
