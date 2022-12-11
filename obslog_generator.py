import argparse
import csv
from datetime import datetime, timedelta
import getpass
import io
import json
import numpy as np
import os
import pandas as pd
from past_observation_crawler import find_obsdates, find_weather_and_comments
import pyshorteners
import requests
import sys
import time
import tqdm
import urllib

parser = argparse.ArgumentParser(description=\
'## obslog formatter ver. 2022 Nov. 19 ##')

parser.add_argument('--obsdate', type=int, help='observation date in yymmdd format')
parser.add_argument('--jd', help='if provided, timestamps will be given in jd instead of ut', action='store_true')
parser.add_argument('--bypass', help='if provided, data download from wiki is bypassed. may be useful for checking tonight\'s obslog', action='store_true')
parser.add_argument('--obj', type=str, help='if given, only the log for that object will be returned. \
                                            variations of names (eg: TOI0XXXX and TOI-XXXX) are treated equally for most cases.\
                                            planet identifiers (eg: -b, b, .01, .1 etc.) are not necessary because it is difficult to\
                                            account for the inconsistencies and query may return empty results.\
                                            case insensitive.',default='all')

args = parser.parse_args()
if args.obsdate is None and args.obj == 'all':
   parser.error("at least one of --obsdate and --obj required")

dirname = os.path.dirname(__file__)
credentials = os.path.join(dirname, 'cred.json')
server = os.path.join(dirname, 'ip.json')

try: 
    with open(credentials, 'r') as openfile:
        payload = json.load(openfile)
except FileNotFoundError:
    print("\n***you can also provide a cred.json file under the same directory bypass login***")
    username = input('username: ')
    password = getpass.getpass(prompt='password: ')
    payload = {"username": username, "password": password}

try:
    with open(server, 'r') as openfile:
        ip = json.load(openfile)
except FileNotFoundError:
    ip = {"shine": "161.72.192.46"}

#print(args.connect)
# Use 'with' to ensure the session context is closed after use.
if not args.bypass:
    try:
        with requests.Session() as s:
            print('_________________________________________________\n')
            print('Authenticating... (takes about 10-15 seconds)')
            print('_________________________________________________')
            time_start = time.time()
            p = s.post('http://research.iac.es/proyecto/muscat/users/login', data=payload)
            time_end = time.time()
            elapsed = time_end - time_start
            if elapsed < 2:
                print("\nlogin failed: wrong username/password\n")
                sys.exit(1)
            # print the html returned or something more intelligent to see if it's a successful login page.
            obs_path = 'http://research.iac.es/proyecto/muscat/observations/export'
            targets_path = 'http://research.iac.es/proyecto/muscat/stars/export'
            path_list = [obs_path,targets_path]
            r = [s.get(path) for path in tqdm.tqdm(path_list, desc=f'Downloading past observation and registered targets data... (about 15 seconds)')]
            obs_text = r[0].text#.encode('utf-8')
            targets_text = r[1].text
            #column = ["id","telescope","observer","weather","seeing","temperature","start_time","end_time","flats","bias","exposure_time","lightcurve","quicklook","comments","files","star_id","code"]
            obs_reader = csv.reader(io.StringIO(obs_text), delimiter=';',quotechar='"',
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)#,index_col=column)
            targets_reader = csv.reader(io.StringIO(targets_text), delimiter=';',quotechar='"',
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)
            observations_df = pd.DataFrame([row for row in obs_reader])
            targets_df = pd.DataFrame([row for row in targets_reader])
    except requests.exceptions.ConnectionError:
        print('Bad connection with the server. A simple retry should fix the issue. Make sure that you are connected to VPN.')
        sys.exit(1)
if args.obsdate is None and args.obj != "all": #日付指定せず、かつ特定の天体を探している場合
    obsdates, weather, comments = find_obsdates(args.obj,observations_df,targets_df)
    #print(obsdates)
else: #日付指定をしている場合(天体指定の有無に関わらず)weatherとコメントは後でprint_obslog内で取得するのでとりあえず空の箱を作る
    obsdates = [str(args.obsdate)]
    weather, comments = [""],[""]

#returns the observation date according to input
def obs(obsdate):
    year = 2000 + int(obsdate[0:2])
    month = int(obsdate[2:4])
    day = int(obsdate[4:6])
    return {'year':year,'month':month,'day':day}

def past_midnight(int):
    return int >= 0 and int <= 12

#returns the time of an exposure as datetime object
def round_ut(obsdate, x):
    if int(x[0:2]) >= 0 and int(x[0:2]) <= 14:
        obs_time = datetime(obs(obsdate)['year'],obs(obsdate)['month'],obs(obsdate)['day'],int(x[0:2]),int(x[3:5]),int(x[6:8])) + timedelta(days=1)
    else:
        obs_time = datetime(obs(obsdate)['year'],obs(obsdate)['month'],obs(obsdate)['day'],int(x[0:2]),int(x[3:5]),int(x[6:8]))
    if int(x[6:8])  >= 58: #takes care of exposure times that have not been rounded up due to the microsecond lag between CCDs
        #JDで下二桁clipをすると、10秒間なまされる
        obs_time += timedelta(seconds=5)
    return obs_time.replace(second=0, microsecond=0) 

def round_jd(jd):
    if len(str(int(jd))) == 4:
        return float(str(jd)[0:8])
    elif len(str(int(jd))) == 5:
        return float(str(jd)[0:9])

def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]

def adjust_name(str:str):
    str = str.lower()
    if 'toi0' in str:
        str = str.replace('toi0', 'toi')
    if '.01' in str:
        str = str.replace('.01', '')
    if '.1' in str:
        str = str.replace('.1', '')
    str = str.replace('-','')
    return str

def take_exposure_log(obslog, exptimes_list, exp_change_time_all_ccd, jd):
    exptimes_mask = obslog.duplicated(subset=4)
    exptimes = np.array(obslog)[~exptimes_mask]

    exp_change_time = []
    
    if jd:
        exp_change_time[:] = map(lambda x: round_jd(x), exptimes[:,3])
    else:
        exp_change_time[:] = map(lambda x: round_ut(obsdate, x), exptimes[:,4])

    exp_change_time_all_ccd.append(exp_change_time)
    exp_value = []
    exp_value[:] = map(lambda x: f'{x}', exptimes[:,5])

    exp_log = list(zip(exp_value,exp_change_time))
    exptimes_list.append(exp_log)

def take_focus_log (obslog,jd):
    focus_mask = obslog.duplicated(subset=10)
    focus = np.array(obslog)[~focus_mask]

    focus_change_time = []
    if jd:
        focus_change_time[:] = map(lambda x: f'[{round_jd(x)}] ', focus[:,3])
    else:
        focus_change_time[:] = map(lambda x: f'[{x[0:5]}] ', focus[:,4])
    focus_value = []
    focus_value[:] = map(lambda x: f'{x}', focus[:,11])

    focus_log = list(zip(focus_change_time,focus_value))
    if len(focus_log) != 1:
        focus_log[:] = map(lambda x: ''.join(x), focus_log)
        focus_log = ', '.join(focus_log)
    else:
        focus_log = focus_log[0][1]
    return focus_log

def print_obslog(obsdate, obsdate_weather, comment, ip):
    dt_object = datetime(obs(obsdate)['year'],obs(obsdate)['month'],obs(obsdate)['day'])
    date_for_mail = dt_object.strftime('%B %d, %Y')

    paths = []
    for num in range(0,4):
        paths.append(f'http://{ip}/obslog/{obsdate}/obslog-muscat2-{obsdate}-ccd{num}.csv')

    active_ccds = list(range(0,4))
    ccds = []
    error_message = []
    error_count = 0
    for index, path in enumerate(tqdm.tqdm(paths, desc=f'\rDownloading obslog for observation on {date_for_mail}')):
        try:
            l  = np.array(pd.read_csv(path, encoding='UTF-8').reset_index())
            ccds.append(l)
        except urllib.error.HTTPError:
            print(f'\r***No obslog is found for CCD {index} on {date_for_mail}***')
            error_count += 1
            if error_count == 4:
                print(f'\r***There was no observation on {date_for_mail}***\r')
            active_ccds.remove(index)
        except pd.errors.ParserError:
            print(f'\r***Obslog for CCD {index} may be corrupt. Please check on http://{ip}/obslog/{args.obsdate}/obslog-muscat2-{args.obsdate}-ccd{index}.html directly***\r')
            active_ccds.remove(index)

    if len(ccds) == 0:
        sys.exit(1) 

    if args.obj == "all":
        object = unique(ccds[0][:,1])
        try:
            object.remove('FLAT')
        except ValueError:
            error_message.append('**MISSING FLAT** FLAT is NOT taken for this observation')
            #pass
        try:
            object.remove('DARK')
        except ValueError:
            error_message.append('**MISSING DARK**DARK is NOT taken for this observation')
            #pass
    else: #create list of matching objects after removing '-'
        object = [s for s in unique(ccds[0][:,1]) if adjust_name(args.obj) in adjust_name(s)]

    df = pd.DataFrame(ccds[0])

    print('\n====== OUTPUT ===================================\n')
    print(f'[MuSCAT2] End of night report {date_for_mail}\n')
    if len(object) == 1:
        print(f'{object[0]} was observed on {date_for_mail}')
    else:
        print(f'{len(object)} targets were observed on {date_for_mail}')

    for item in object:
        obslog = df[df[1] == item].reset_index()
        if args.jd:
            obstimes = f'Obs: {obslog[2][0]} - {obslog[2].iloc[-1]} (JD)'
        else:
            obstimes = f'Obs: {obslog[3][0][0:5]} - {obslog[3].iloc[-1][0:5]} UT'

        start_time = dt_object + timedelta(hours=int(obslog[3][0][0:5][:2])) + timedelta(minutes=int(obslog[3][0][0:5][3:]))
        end_time = dt_object + timedelta(hours=int(obslog[3].iloc[-1][0:5][:2])) + timedelta(minutes=int(obslog[3].iloc[-1][0:5][3:]))
        if past_midnight(int(obslog[3][0][0:5][:2])):
            start_time += timedelta(days=1)
        if past_midnight(int(obslog[3].iloc[-1][0:5][:2])):
            end_time += timedelta(days=1)

        humidity_path = f'http://stella-archive.aip.de/stella/status/detail-text.php?typ=2&from={start_time.strftime("%d.%m.%Y %T")}&until={end_time.strftime("%d.%m.%Y %T")}&onescale=0&minmax=0'
        humidity_plot = f'http://stella-archive.aip.de/stella/status/getdetail{humidity_path[54:]}'

        exptimes_list = [] #list of tuples containing (exptime, change_time) for all exposures
        exp_change_time_all_ccd = [] # cumulative list of all ccds of times when exposure time has changed

        focus_log = take_focus_log(obslog,args.jd)
        focus = "" #create empty string which can be overwritten in when generating obslog for emails and registeration to wiki
        ag = None #create empty variable which can be overwritten in when generating obslog for emails and registeration to wiki

        if not args.bypass: #if a specific date is returned and connected to wiki, obtain info from wiki
            obsdate_weather, comment , focus , ag, altitude_plot = find_weather_and_comments(item,observations_df,targets_df,obsdate,start_time,end_time,obslog[2][0],obslog[2].iloc[-1],payload)
        #args.obsdate is not None and 
        for ccd in ccds:
            df = pd.DataFrame(ccd)
            obslog = df[df[1] == item].reset_index()
            take_exposure_log(obslog,exptimes_list,exp_change_time_all_ccd,args.jd)

        exp_change_time_all_ccd = sorted(unique(np.concatenate(exp_change_time_all_ccd)))

        '''
        prepare pandas dataframe containing the exposure times of each CCD at timestamps when exposure times were changed
        eg:
                0     1     2     3
        20:21  15.0  90.0  90.0  90.0
        20:32  90.0  90.0  90.0  90.0
        20:45  30.0  90.0  90.0  90.0
        20:56  30.0  90.0  15.0  90.0
        '''
        #initialize an empty dataframe
        exp_df = pd.DataFrame(columns=range(len(active_ccds)),index=exp_change_time_all_ccd)#.sort_index()
        #fill in cells
        for index, exposure in enumerate(exptimes_list):
            for log in unique(exposure):
                exp_df[index][log[1]] = log[0]
        exp_df = exp_df.fillna(method='ffill')
        if not args.jd:
            exp_df = exp_df.fillna(method='ffill').rename(index=lambda s: s.strftime('%H:%M'))
        if ag is not None: #indicates the ccd used for ag if specified
            active_ccds[active_ccds.index(ag)] = f'[{ag}]'
        exp_df.columns = active_ccds
        #if not simply write in a single line
        if len(exp_df) == 1:
            if ag is not None:
                (exp_df.iloc[0][ag]) = f'[{exp_df.iloc[0][0]}]'
            exp_df = ', '.join((exp_df.iloc[0]))

        if not args.bypass:
            with requests.Session() as s:
                r = s.get(humidity_path)
                humidity = r.text#.encode('utf-8')
                humidity_reader = csv.reader(io.StringIO(humidity), delimiter=',',quotechar='"',
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)
                humidity_df = pd.DataFrame([row for row in humidity_reader])
                try:
                    humidity_df[1] = humidity_df[1].astype(float)
                    max_humidity = f'{np.round(humidity_df[1].max(),decimals=1)}% (max),'
                    min_humidity = f'{np.round(humidity_df[1].min(),decimals=1)}% (min)'
                except KeyError:
                    max_humidity = "Observation too short for archival data"
                    min_humidity = ""

        url_shortener = pyshorteners.Shortener()
        altitude_plot = url_shortener.tinyurl.short(altitude_plot)
        humidity_plot = url_shortener.tinyurl.short(humidity_plot)

        #print output
        print('_________________________________________________')
        print(item)
        print(obstimes)   
        print(f'Exp: {exp_df}')
        if len(focus_log) >= 10:
            print(f'Focus: {focus}')
            print(f'{focus_log}')
        else:
            print(f'Focus: {focus} {focus_log}')
        if not args.bypass:
            print(f'Weather: {obsdate_weather}')
            print(f'Humidity: {max_humidity} {min_humidity}')
            print(f'Comments: {comment}\n')
            print(f'Altitude plot: {altitude_plot}')
            print(f'Humidity plot: {humidity_plot}')
            #time.sleep(2)
        else:
            print('Comments:')
    print('_________________________________________________')
    print('\nNote:')
    if len(active_ccds) != 4:
        print(f'\n**MISSING CCD**Exposure times are for CCDs {active_ccds} respectively.\n')
    for error in error_message:
        print(f'{error}\n')
    #if args.obsdate is not None:
    #    print('Please specify the CCD used for ag separately.')
    print('Optional argument --jd can be provided to show times in JD.\n')

for obsdate, obsdate_weather, comment in zip(obsdates, weather, comments):
    print_obslog(obsdate, obsdate_weather, comment, ip['shine'])
#一番短い露光時間のCCDの観測開始時間が1分遅れてしまうバグがある m秒のずれでCCD間で59秒と00秒になってしまうことが判明したのでseconds == 59の場合、(timdelta(seconds=1))で解決
