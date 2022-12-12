# obslog_generator for MuSCAT2

automatically generate and register obslog on MuSCAT2 wiki

![demo](/img/obslog_generator_demo.gif)

## usage: python obslog_generator.py [-h] --obsdate=int --obj=str --jd --bypass

### 1: generate obslog and register on wiki (eg. Dec 10, 2022)

	python obslog_generator.py --obsdate=221210
	
example output will look like this.

	_________________________________________________
	TOI04659.01
	Obs: 21:34 - 01:48 UT
	Exp: 15.0, 20.0, [15.0], 20.0
	Focus: On focus, 660841.0
	Weather: Humid, Cloudy
	Humidity: 70.9% (max), 54.1% (min)
	Comments: The data is useless due to cloudy weather.

	Altitude plot: https://tinyurl.com/2nw3ztn6
	Humidity plot: https://tinyurl.com/2f2evscw
	_________________________________________________

for observations unregistered on wiki, something like this will come up.

	____NEW OBSERVATION______________________________

	The following observation of TOI04659.01 has not been recorded on wiki yet.

	Register TOI04659.01's observation on December 10, 2022 to wiki [y/N]: y
	_________________________________________________
	
simply follow the prompt and enter the required information to complete the registration. 

	Weather: Humid, Cloudy
	CCD for ag [0|1|2|3]: 2
	Focus [0:in focus|1:on focus|2:slightly defocused|3:defocused|4:heavily defocused]: 1
	Comments: The data is useless due to cloudy weather.
	Observers: Yugo
	_________________________________________________

	Registering... (takes about 10-15 seconds)
	_________________________________________________

	Registration complete! (TOI04659.01, December 10, 2022)

	Check at http://research.iac.es/proyecto/muscat/stars/view/990
	
registration can be checked by following the generated link.
	
![registration](/img/registration_demo.png)

the console output can be pasted directly to end of observation emails.

	_________________________________________________
	TOI04659.01
	Obs: 21:34 - 01:48 UT
	Exp: 15.0, 20.0, [15.0], 20.0
	Focus: On focus, 660841.0
	Weather: Humid, Cloudy
	Humidity: 70.9% (max), 54.1% (min)
	Comments: The data is useless due to cloudy weather.

	Altitude plot: https://tinyurl.com/2nw3ztn6
	Humidity plot: https://tinyurl.com/2f2evscw
	_________________________________________________

altitude plots and humidity plots are retrieved from TTF and STELLA respectively. following each link, you should find something like this.

![altitude and humidity plots](/img/sample_altitude_humidity_plots.png)

### 2: generate obslog for a specific object (eg. KELT-19)

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

### 3: generate simplified obslog

	python obslog_generator.py --obsdate=221121 --bypass

this will only retrieve obstimes, exptimes and focus from the obslog. <br/>
this is much quicker because login to MuSCAT2 wiki is bypassed, which can be slow sometimes. <br/> this might be useful when checking obslog during observations. example output looks like this.

	_________________________________________________
	TOI05543.01
	Obs: 22:17 - 23:02 UT
	Exp: 15.0, 15.0, 15.0, 10.0
	Focus:  662961.0
	Comments:
	_________________________________________________

### arguments:

  -h, --help              : show this help message and exit

  --obsdate        	  : date of observation in yymmdd format

  --obj			  : if given, only the log for that object will be returned.

  --jd 			  : if provided, will return time stamps in jd instead of ut

  --bypass 		  : if provided, data download from wiki is bypassed. may be useful for 
			    quickly checking tonight's obslog

### notes:
metadata (obj_name, obstime, exp, focus) are taken from obslog, weather and comments are taken from MuSCAT2 wiki.<br/>

### requirements
numpy,pandas,requests,tqdm,astropy,pyshorteners

Author: Yugo Kawai (The University of Tokyo)
(Email: yugo6581 @ g.ecc.u-tokyo.ac.jp)

Last update: Dec 12, 2022
