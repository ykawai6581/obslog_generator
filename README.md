# obslog_generator for MuSCAT2

## usage: python obslog_generator.py [-h] --obsdate=int --obj=str --jd --bypass

### 1: to generate obslog for a specific date and register on wiki (eg. Nov 19, 2022)

	python obslog_generator.py --obsdate=221119
	
example output will look like this.

	_________________________________________________
	TOI05543.01
	Obs: 22:17 - 23:02 UT
	Exp: 15.0, 15.0, 15.0, 10.0
	Focus:  662961.0
	Weather: Humid
	Humidity: 61.4% (max), 32.7% (min)
	Comments: It's hard to keep track of the observation due to ds9 problems (lag, closing from time to time, etc.). In order to have better comparison stars, we moved the field (offset 150 in RA). We had to stop the observation at 23:00 UT due to a humidity

	Altitude plot: https://tinyurl.com/2e4z3ea7
	Humidity plot: https://tinyurl.com/2gqx2wm4
	_________________________________________________

altitude plots and humidity plots are retrieved from TTF and STELLA respectively. following each link, you should find something like this.

![altitude and humidity plots](/sample_altitude_humidity_plots.png)

for observations unregistered on wiki, something like this will come up.

	____NEW OBSERVATION______________________________

	The following observation of TOI05933.01 has not been recorded on wiki yet.

	Register TOI05933.01's observation on November 12, 2022 to wiki [y/N]: 
	_________________________________________________
	
simply follow the prompt and enter the required information to complete the registration.

### 2: to generate obslog for a specific target (eg. KELT-19)**

	python obslog_generator.py --obj="KELT-19"
	
	* variations of names (eg: TOI0XXXX and TOI-XXXX) are treated 
	equally for most cases. planet identifiers (eg: -b, b, .01, .1 etc.) 
	are not necessary because it is difficult to account for the 
	inconsistencies and query may return empty results. case insensitive.
	
this will search the MuSCAT2 wiki for all observations previously conducted for the specific object. it will return something like this.

	_____________________________________________
	2 observation(s) for KELT-19 are found on: (yymmdd)

	['181129', '200201']

	If no obslogs are returned with the above dates, this may be due to the observation date wrongly entered on MuSCAT2 wiki.           
	eg: Observations past midnight are registered with the date before midnight.           
	In that case, obslog can be found on the next day. [ie: /obs_log_formatter.py --obsdate=221114 -> 221115]
	_____________________________________________
	Download all [y/N]: n
	Obsdate(s) to download in yymmdd [int or list(int)]: 181129
	
you can either download obslog for all observations or choose a specific date.

### 3: to quickly generate obslog for a specific date

	python obslog_generator.py --obsdate=221121 --bypass

this will bypass the login to MuSCAT2 wiki, which can be slow sometimes. (just retrieving the obslog is much quicker) <br/> 
so running this version of the command will be much quicker but at the expense of weather information and comments. example output looks like this.

	_________________________________________________
	TOI05543.01
	Obs: 22:17 - 23:02 UT
	Exp: 15.0, 15.0, 15.0, 10.0
	Focus:  662961.0
	Comments:
	_________________________________________________

### 4: to generate obslog for a specific target on a specific date**

	python obslog_generator.py --obj="KELT-19" --obsdate=181129

same thing as #3, but this is quicker if you know what date the observation was on.

**arguments:

  -h, --help              : show this help message and exit

  --obsdate        	  : date of observation in yymmdd format

  --obj			  : if given, only the log for that object will be returned.

  --jd 			  : if provided, will return time stamps in jd instead of ut

  --bypass 		  : if provided, data download from wiki is bypassed. may be useful for 
			    quickly checking tonight's obslog

notes:
metadata (obj_name, obstime, exp, focus) are taken from obslog, weather and comments are taken from MuSCAT2 wiki.<br/>

- whenever a new observation (observation not found on wiki) is loaded, the script will prompt users to register the obslog to the wiki. this is easily achieved by simply following the command line, without the need to access the webpage. the console output can be also copied for end of night reports. (kill two birds with one stone!)

***requirements***
numpy,pandas,requests,tqdm,astropy,pyshorteners

Author: Yugo Kawai (The University of Tokyo)
(Email: yugo6581 @ g.ecc.u-tokyo.ac.jp)

Last update: November 21, 2022
