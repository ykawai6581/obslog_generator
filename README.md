# [MuSCAT2] obslog_generator
obslog generation/registration tool for MuSCAT2

![demo](/img/obslog_generator_demo.gif)

## installation:

	git clone https://github.com/ykawai6581/obslog_generator.git

you can run the above command or also choose to download the zip file.<br/>
once that is done, cd into /obslog_generator and run

	pip install -r requirements.txt

to download the required modules, which include astropy, numpy, pandas, pyshorteners, requests and tqdm.

additionally, you can prepare your own cred.json file under /obslog_generator so that you don't have to type in usernames and passwords everytime you try to login to MuSCAT2 wiki. in that case, your json file should look something like

#### **`cred.json`**
``` json
{"username": ******,
 "password": ******
}
```

## usage: 

	python obslog_generator.py [-h] --obsdate=int --obj=str --jd --bypass

run the above command with arguments that fit your needs! below are some examples.

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

	_________________________________________________
	2 observation(s) for KELT-19 are found on: (yymmdd)

	['181129', '200201']

	If no obslogs are returned with the above dates, this may be due to the observation date wrongly entered on MuSCAT2 wiki.           
	eg: Observations past midnight are registered with the date before midnight.           
	In that case, obslog can be found on the next day. [ie: /obslog_generator.py --obsdate=181129 -> 181130]
	_________________________________________________
	Download all [y/N]: n
	Obsdate(s) to download in yymmdd [int or list(int)]: 181129
	
you can either download obslog for all observations or choose a specific date.

### 3: generate simplified obslog

	python obslog_generator.py --obsdate=221211 --bypass

this will only retrieve obstimes, exptimes and focus from the obslog. <br/>
this is much quicker because login to MuSCAT2 wiki is bypassed, which can be slow sometimes. <br/> this might be useful when checking obslog during observations. example output looks like this.

	_________________________________________________
	TOI02742.01
	Obs: 01:13 - 04:51 UT
	Exp: 30.0, 15.0, 30.0, 30.0
	Focus:  658021.0
	Humidity: 66.6% (max), 33.8% (min)
	
	Altitude plot: https://tinyurl.com/2guzn357
	Humidity plot: https://tinyurl.com/2zf5ygye
	_________________________________________________

### arguments:

  -h, --help              : show this help message and exit

  --obsdate        	  : date of observation in yymmdd format

  --obj			  : if given, only the log for that object will be returned

  --jd 			  : if provided, will return time stamps in jd instead of ut

  --bypass 		  : if provided, data download from wiki is bypassed. may be useful for 
			    quickly checking obslog during observation

### notes:
metadata (obj_name, obstime, exp, focus) are taken from obslog, weather and comments are taken from MuSCAT2 wiki.<br/>
if nothing about the weather is registered on wiki, archival data is retrieved from telescope.org/weather.php.<br/>

ra and dec are retrieved from wiki in regular mode, and from exofop in bypass mode.

### requirements:
numpy,pandas,requests,tqdm,astropy,pyshorteners

Author: Yugo Kawai (The University of Tokyo)
(Email: yugo6581 @ g.ecc.u-tokyo.ac.jp)

Last update: Dec 12, 2022
