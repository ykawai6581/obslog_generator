#import csv
from datetime import datetime, timedelta
import json
import os
#import pandas as pd
import sys
import warnings

try:
    import numpy as np
    from astropy.time import Time
    import requests
except ModuleNotFoundError:
    print("Some required modules are not installed.\n pip install -r requirements.txt\n Please run the above command and try again.")
    sys.exit(1)

warnings.filterwarnings("ignore")

def obs(obsdate):
    year = 2000 + int(obsdate[0:2])
    month = int(obsdate[2:4])
    day = int(obsdate[4:6])
    return {'year':year,'month':month,'day':day}

def replace_header(df):
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #get dataframe without the first row
    df.columns = new_header 
    return df

def replace_index(df):
    return df.set_index(df['star_id'])

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

def adjust_date(str):
    dt = datetime.strptime(str,'%x, %I:%M %p')
    if dt.hour >= 0 and dt.hour <= 6:
        dt += timedelta(days=-1)
    return dt.strftime('%y%m%d')

def adjust_string(str):
    if len(str) == 0:
        str = "None"
    return str

def deg_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = np.round((((deg - d) * 60) - m) * 60, decimals=2)
    return f'{d}:{np.abs(m)}:{np.abs(s)}'

def deg_to_hms(deg):
    d = int(deg/15)
    m = int((deg/15 - d) * 60)
    s = np.round((((deg/15 - d) * 60) - m) * 60, decimals=2)
    return f'{d}:{np.abs(m)}:{np.abs(s)}'

def find_obsdates(target, observations_df, targets_df):
    observations_df = replace_header(observations_df)
    targets_df = replace_header(targets_df)
    targets_df['name'] = [adjust_name(s) for s in targets_df['name']]
    try:
        star_id = targets_df[targets_df['name'].str.contains(adjust_name(target))]['id'].iloc[0]
    except IndexError:
        print(f'No previous observation for {target} is found. \nTarget could also be registered under a different name.\n(eg. TOI-XXXX and TOI0XXXX)')
        sys.exit(1) 
    past_observation = observations_df[observations_df['star_id'] == star_id]

    obsdates = list(past_observation['start_time'])
    obsdates = [adjust_date(x) for x in obsdates if int(adjust_date(x)) >= 180414]
    print('_________________________________________________')
    if len(obsdates) == 0:
        print(f'No previous observation for {target} is found. \nTarget could also be registered under a different name.\n(eg. TOI-XXXX and TOI0XXXX)')
        sys.exit(1)
    else:
        print(f'{len(obsdates)} observation(s) for {target} are found on: (yymmdd)\n')

    print(obsdates)

    print('\nIf no obslogs are returned with the above dates, this may be due to the observation date wrongly entered on MuSCAT2 wiki.\
           \neg: Observations past midnight are registered with the date before midnight.\
           \nIn that case, obslog can be found on the next day. [ie: /obslog_generator.py --obsdate=181129 -> 181130]')
    print('________________________________________________')
    weather = list(past_observation['weather'])
    comments = list(past_observation['comments'])

    choice = input("Download all [y/N]: ").lower()
    if choice in ['y', 'ye', 'yes']:
        pass
    elif choice in ['n', 'no']:
        dl = input("Obsdate(s) to download in yymmdd [int or list(int)]: ")
        if type(dl) == int:
            dl = [dl]
        dl_index = [obsdates.index(str(x)) for x in obsdates if x in dl]
        obsdates = [x for x in obsdates if x in dl]
        weather = [adjust_string(x) for x in weather if weather.index(x) in dl_index]
        comments = [adjust_string(x) for x in comments if comments.index(x) in dl_index]
        if len(weather) == 0: #accounts for obslog without weather data
            weather = ["" for x in dl_index]
        if len(comments) == 0: #accounts for obslog without comments
            comments = ["" for x in dl_index]
    return obsdates, weather, comments

def find_weather_and_comments(target, observations_df, targets_df, obsdate, start_time, end_time, jd_start, jd_end, payload):
    observations_df = replace_header(observations_df)
    targets_df = replace_header(targets_df)
    targets_df['wiki_name'] = targets_df['name']
    targets_df['name'] = [adjust_name(s) for s in targets_df['name']]
    try:
        star_id = targets_df[targets_df['name'].str.contains(adjust_name(target))]['id'].iloc[0]
        ra = float(targets_df[targets_df['name'].str.contains(adjust_name(target))]['RA'].iloc[0])
        ra = deg_to_hms(ra)
        dec = float(targets_df[targets_df['name'].str.contains(adjust_name(target))]['Decl'].iloc[0])
        dec = deg_to_dms(dec)
        jd = Time(start_time.strftime('%Y-%m-%d %T'),format='iso',out_subfmt='date_hm').jd
        warning = " (THE GREEN SECTION INDICATES OBSERVATION TIME NOT TRANSIT TIME)"
        altitude_plot = f'https://astro.swarthmore.edu/telescope/tess-secure/plot_airmass.cgi?observatory_string=28.3%3B-16.5097%3BAtlantic%2FCanary%3BMuSCAT2%201.52m%20at%20Teide%20Observatory%3BMuSCAT2%201.52m&observatory_latitude=28.3&observatory_longitude=-16.5097&target={target}{warning}&ra={ra}&dec={dec}&timezone=Atlantic/Canary&jd={jd}&jd_start={jd_start}&jd_end={jd_end}&use_utc=0&max_airmass=2.4'
    except IndexError:
        return "","Target does not seem to be registered on wiki.", "", None, "No link to altitude plot"
    
    past_observation = observations_df[observations_df['star_id'] == star_id]
    obsdates = list(past_observation['start_time'])
    past_observation['start_time'] = [adjust_date(x) for x in obsdates]
    try:
        weather = past_observation[past_observation['start_time'] == obsdate]['weather'].iloc[0]
        comments = past_observation[past_observation['start_time'] == obsdate]['comments'].iloc[0]
    except IndexError:
        #ここでtarget観測を登録するか聞く（各天体についてのループの中でここに辿り着いてるから、ここでinputを促せばそのまま登録できる？）
        date_for_view = datetime(obs(obsdate)['year'],obs(obsdate)['month'],obs(obsdate)['day']).strftime('%B %d, %Y')
        print('\n____NEW OBSERVATION______________________________')
        print(f'\nThe following observation of {target} has not been recorded on wiki yet.\n')
        choice = input(f'Register {target}\'s observation on {date_for_view} to wiki [y/N]: ').lower()
        print('_________________________________________________\n')
        if choice in ['y', 'ye', 'yes']:
            try:
                with requests.Session() as s:
                    weather = input('Weather: ')
                    ag = input('CCD for ag [0|1|2|3]: ')
                    focus_options = ["In focus,", "On focus,", "Slightly defocused,", "Defocused,", "Heavily defocused,"]
                    focus_index = input('Focus [0:in focus|1:on focus|2:slightly defocused|3:defocused|4:heavily defocused]: ')
                    focus = focus_options[int(focus_index)]
                    comments = input('Comments: ')
                    observers = input('Observers: ')
                    obsdata = {
                        'star_id': star_id,
                        'start_time[year]': start_time.year,
                        'start_time[month]': start_time.month,
                        'start_time[day]': start_time.day,
                        'start_time[hour]':start_time.hour,
                        'start_time[minute]':start_time.minute,
                        'end_time[year]': end_time.year,
                        'end_time[month]': end_time.month,
                        'end_time[day]': end_time.day,
                        'end_time[hour]':end_time.hour,
                        'end_time[minute]':end_time.minute,
                        'telescope' : 'MuSCAT2',
                        'observer': observers,
                        'weather': weather,
                        'seeing': "",
                        'exposure_time': "",
                        'bias':1,
                        'flats':1,
                        'lightcurve':1,
                        'quicklook':1,
                        'comments': f'Ag with CCD{ag}. {comments}',
                    }
                    #print(obsdata)
                    print('_________________________________________________\n')
                    print('Registering... (takes about 10-15 seconds)')
                    print('_________________________________________________')
                    p = s.post('http://research.iac.es/proyecto/muscat/users/login', data=payload)
                    #print(p.status_code)
                    registration = s.post('http://research.iac.es/proyecto/muscat/observations/add', data=obsdata)
                    if registration.status_code == 404:
                        print(f'Registration failed. Please check your word count in comments. ({target}, {date_for_view})')
                    else:
                        print(f'\nRegistration complete! ({target}, {date_for_view})\n')
                        print(f'Check at http://research.iac.es/proyecto/muscat/stars/view/{star_id}\n')
                    return weather, comments, focus, int(ag), altitude_plot
            except requests.exceptions.ConnectionError:
                print('Bad connection with the server. A simple retry should fix the issue. Make sure that you are connected to VPN.')
                sys.exit(1)
        elif choice in ['n', 'no']:
            return "","Observation does not seem to be registered on wiki yet.","", None, altitude_plot
    return weather, comments, "", None, altitude_plot
