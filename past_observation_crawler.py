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
    print('_________________________________________________\n')
    print("Some required modules are not installed.\n\n    pip install -r requirements.txt\n\nPlease run the above command and try again.")
    print('_________________________________________________\n')
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

def exp_time_str(df,ag):
    l_list = []
    for i in range(len(df)):
        (df.iloc[i][int(ag)]) = f'[{df.iloc[i][int(ag)]}]'
        l = [str(t) for t in df.iloc[i]]
        l = ', '.join((l))
        l_list.append(l)
    l_list = ' -> '.join((l_list))
    return l_list

def find_obsdates(target, observations_df, targets_df):
    observations_df = replace_header(observations_df)
    targets_df = replace_header(targets_df)
    targets_df['wiki_name'] = targets_df['name']
    targets_df['name'] = [adjust_name(s) for s in targets_df['name']]
    try:
        star_id = targets_df[targets_df['name'].str.contains(adjust_name(target))]#['id']#.iloc[0]
        if len(star_id) > 1:
            registered_names = list(star_id["wiki_name"])
            print('\n____MULTIPLE NAMES ENCOUNTERED___________________')
            print(f'\nMultiple names for {target} are found on wiki. Which one should we choose?\n')
            print(f'{registered_names}')
            list_of_names = '|'.join([f'{registered_names.index(item)}:{item}' for item in registered_names])
            name_choice = input(f'\nOptions [{list_of_names}]: ')
            while int(name_choice) > len(registered_names)-1:
                    print(f'Plese give a valid index in the range 0-{len(registered_names)-1}')
                    name_choice = input(f'Options [{list_of_names}]: ')
            target = registered_names[int(name_choice)]
            print(f'Continuing with {target} ...')
            star_id = star_id['id'].iloc[int(name_choice)]
        else:
            star_id = star_id['id'].iloc[0]
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

def find_weather_and_comments(target, observations_df, targets_df, obsdate, start_time, end_time, jd_start, jd_end, payload, edit, exp_df):
    observations_df = replace_header(observations_df)
    targets_df = replace_header(targets_df)
    targets_df['wiki_name'] = targets_df['name']
    targets_df['name'] = [adjust_name(s) for s in targets_df['name']]
    try:
        star_id = targets_df[targets_df['name'].str.contains(adjust_name(target))]#['id']#.iloc[0]
        if len(star_id) > 1:
            registered_names = list(star_id["wiki_name"])
            print('\n____MULTIPLE NAMES ENCOUNTERED___________________')
            print(f'\nMultiple names for {target} are found on wiki. Which one should we choose?\n')
            print(f'{registered_names}')
            list_of_names = '|'.join([f'{registered_names.index(item)}:{item}' for item in registered_names])
            name_choice = input(f'\nOptions [{list_of_names}]: ')
            while int(name_choice) > len(registered_names)-1:
                    print(f'Plese give a valid index in the range 0-{len(registered_names)-1}')
                    name_choice = input(f'Options [{list_of_names}]: ')
            target = registered_names[int(name_choice)]
            print(f'Continuing with {target} ...')
            star_id = star_id['id'].iloc[int(name_choice)]
        else:
            star_id = star_id['id'].iloc[0]
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
    past_observation['start_time_short'] = [adjust_date(x) for x in obsdates]
    try:
        weather = past_observation[past_observation['start_time_short'] == obsdate]['weather'].iloc[0]
        comments = past_observation[past_observation['start_time_short'] == obsdate]['comments'].iloc[0]
        if edit:
            date_for_view = datetime(obs(obsdate)['year'],obs(obsdate)['month'],obs(obsdate)['day']).strftime('%B %d, %Y')
            print('\n____EDIT OBSERVATION_____________________________\n')
            choice = input(f'Edit {target}\'s observation on {date_for_view} on wiki [y/N]: ').lower()
            if choice in ['y', 'ye', 'yes']:
                print('\n____What would you like to edit?_________________')
                print('\n*** separate integers with commmas if multiple **\n')
                try:
                    edit_section = input('Options [0:start time|1:end time|2:weather|3:comments|4:observer]: ')
                    edit_section = edit_section.split(",")
                    edit_section = [int(num) for num in edit_section]
                    obs_id = past_observation[past_observation['start_time_short'] == obsdate]['id'].iloc[0]
                    weather = past_observation[past_observation['start_time_short'] == obsdate]['weather'].iloc[0]
                    comments = past_observation[past_observation['start_time_short'] == obsdate]['comments'].iloc[0]
                    observer = past_observation[past_observation['start_time_short'] == obsdate]['observer'].iloc[0]
                    start_time = datetime.strptime(past_observation[past_observation['id'] == obs_id]['start_time'].iloc[0],'%x, %I:%M %p')
                    end_time = datetime.strptime(past_observation[past_observation['id'] == obs_id]['end_time'].iloc[0],'%x, %I:%M %p')
                    obsdata = {
                                'star_id': star_id,
                                'start_time[year]'  : start_time.year,
                                'start_time[month]' : start_time.month,
                                'start_time[day]'   : start_time.day,
                                'start_time[hour]'  : start_time.hour,
                                'start_time[minute]': start_time.minute,
                                'end_time[year]'    : end_time.year,
                                'end_time[month]'   : end_time.month,
                                'end_time[day]'     : end_time.day,
                                'end_time[hour]'    : end_time.hour,
                                'end_time[minute]'  : end_time.minute,
                                'telescope'         : 'MuSCAT2',
                                'observer'          : observer,
                                'weather'           : weather,
                                'seeing'            : "",
                                'exposure_time'     : "",
                                'bias'              :1,
                                'flats'             :1,
                                'lightcurve'        :1,
                                'quicklook'         :1,
                                'comments'          : past_observation['comments'],
                            }

                    for i in edit_section:
                        if i == 0:
                            caution = input('CAUTION: Editing obsdate can cause mismatch with shine obslog. Continue? [y/N]: ')
                            if caution in ['y', 'ye', 'yes']:
                                print('\n____EDITING START TIME___________________________\n')
                                e_start_year   = input('Year   [press enter if unchanged]: ')
                                e_start_month  = input('Month  [press enter if unchanged]: ')
                                e_start_day    = input('Day    [press enter if unchanged]: ')
                                e_start_hour   = input('Hour   [press enter if unchanged]: ')
                                e_start_minute = input('Minute [press enter if unchanged]: ')

                                obsdata['start_time[year]']   = obsdata['start_time[year]'] if e_start_year == "" else e_start_year
                                obsdata['start_time[month]']  = obsdata['start_time[month]'] if e_start_month == "" else e_start_month
                                obsdata['start_time[day]']    = obsdata['start_time[day]'] if e_start_day == "" else e_start_day
                                obsdata['start_time[hour]']   = obsdata['start_time[hour]'] if e_start_hour == "" else e_start_hour
                                obsdata['start_time[minute]'] = obsdata['start_time[minute]'] if e_start_minute == "" else e_start_minute
                                print('_________________________________________________')

                        if i == 1:
                            caution = input('CAUTION: Editing obsdate can cause mismatch with shine obslog. Continue? [y/N]: ')
                            if caution in ['y', 'ye', 'yes']:
                                print('\n____EDITING END TIME_____________________________\n')
                                e_end_year   = input('Year   [press enter if unchanged]: ')
                                e_end_month  = input('Month  [press enter if unchanged]: ')
                                e_end_day    = input('Day    [press enter if unchanged]: ')
                                e_end_hour   = input('Hour   [press enter if unchanged]: ')
                                e_end_minute = input('Minute [press enter if unchanged]: ')

                                obsdata['end_time[year]']      = obsdata['end_time[year]'] if e_end_year == "" else e_end_year
                                obsdata['end_time[month]']     = obsdata['end_time[month]'] if e_end_month == "" else e_end_month
                                obsdata['end_time[day]']       = obsdata['end_time[day]'] if e_end_day == "" else e_end_day
                                obsdata['end_time[hour]']      = obsdata['end_time[hour]'] if e_end_hour == "" else e_end_hour
                                obsdata['endend_time[minute]'] = obsdata['end_time[minute]'] if e_end_minute == "" else e_end_minute
                                print('_________________________________________________\n')

                        if i == 2:
                            weather = input('Weather: ')
                            obsdata['weather'] = weather

                        if i == 3:
                            comments = input('Comments: ')
                            e_ag = input('CCD for ag [0|1|2|3|4:not sure]: ')
                            focus_index = input('Focus [0:in focus|1:on focus|2:slightly defocused|3:defocused|4:heavily defocused|custom string]: ')
                            try:
                                focus = focus_options[int(focus_index)]
                            except ValueError:
                                focus = focus_index                            
                            l_list = exp_time_str(exp_df,e_ag)
                            obsdata['comments'] = f'{l_list}. {focus}. {comments}'
                            comments = f'{l_list}. {focus}. {comments}'

                        if i == 4:
                            observer = input('Observer: ')
                            obsdata['observer'] = observer

                    with requests.Session() as s:
                        print('_________________________________________________\n')
                        print('Updating... (takes about 10-15 seconds)')
                        print('_________________________________________________')
                        p = s.post('https://research.iac.es/proyecto/muscat/users/login', data=payload)
                        registration = s.post(f'https://research.iac.es/proyecto/muscat/observations/edit/{obs_id}', data=obsdata)
                        if registration.status_code == 404:
                            print(f'Update failed. Please check your word count in comments. ({target}, {date_for_view})')
                        else:
                            print(f'\nUpdate complete! ({target}, {date_for_view})\n')
                            print(f'Check at https://research.iac.es/proyecto/muscat/observations/view/{obs_id}\n')
                except ValueError:
                    print("\nNo edits were specified")

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
                    ag = input('CCD for ag [0|1|2|3|4:not sure]: ')
                    focus_options = ["In focus,", "On focus,", "Slightly defocused,", "Defocused,", "Heavily defocused,"]
                    focus_index = input('Focus [0:in focus|1:on focus|2:slightly defocused|3:defocused|4:heavily defocused|custom string]: ')
                    try:
                        focus = focus_options[int(focus_index)]
                    except ValueError:
                        focus = focus_index

                    l_list = exp_time_str(exp_df,ag)

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
                        'comments': f'{l_list}. {focus}. {comments}',
                    }
                    #print(obsdata)
                    print('_________________________________________________\n')
                    print('Registering... (takes about 10-15 seconds)')
                    print('_________________________________________________')
                    p = s.post('https://research.iac.es/proyecto/muscat/users/login', data=payload)
                    #print(p.status_code)

                    registration = s.post('https://research.iac.es/proyecto/muscat/observations/add', data=obsdata)
                    if registration.status_code == 404:
                        print(f'Registration failed. Please check your word count in comments. ({target}, {date_for_view})')
                    else:
                        print(f'\nRegistration complete! ({target}, {date_for_view})\n')
                        print(f'Check at https://research.iac.es/proyecto/muscat/stars/view/{star_id}\n')
                    return weather, comments, focus, int(ag), altitude_plot

            except requests.exceptions.ConnectionError:
                print('Bad connection with the server. A simple retry should fix the issue. Make sure that you are connected to VPN.')
                sys.exit(1)

        elif choice in ['n', 'no']:
            return "","Observation does not seem to be registered on wiki yet.","", None, altitude_plot

    return weather, comments, "", None, altitude_plot
