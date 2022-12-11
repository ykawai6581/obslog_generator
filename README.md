# obslog_generator
## obslog generator for MuSCAT2

usage: python obslog_generator.py [-h] --obsdate=int --obj=str --jd --bypass

examples:

**to generate obslog for a specific date (eg. Nov 21, 2022)**

	python obslog_generator.py --obsdate=221121


**to quickly generate obslog for a specific date**

	python obslog_generator.py --obsdate=221121 --bypass

	* this will bypass the post request to the wiki, 
	so the operation will be much quicker at the expense of 
	weather information and comments


**to generate obslog for a specific target (eg. KELT-9)**

	python obslog_generator.py --obj="KELT-9"
	
	* variations of names (eg: TOI0XXXX and TOI-XXXX) are treated 
	equally for most cases. planet identifiers (eg: -b, b, .01, .1 etc.) 
	are not necessary because it is difficult to account for the 
	inconsistencies and query may return empty results. case insensitive.

**to generate obslog for a specific target on a specific date**

	python obslog_generator.py --obj="KELT-9" --obsdate=221121

arguments:

  -h, --help              : show this help message and exit

  --obsdate        	  : date of observation in yymmdd format

  --obj			  : if given, only the log for that object will be returned.

  --jd 			  : if provided, will return time stamps in jd instead of ut

  --bypass 		  : if provided, data download from wiki is bypassed. may be useful for 
			    quickly checking tonight's obslog

notes:
- this script downloads and prints MuSCAT2 observation log for a specific obsdate or target. 
metadata (obj_name, obstime, exp, focus) are taken from obslog and other variables (weather and comments) are taken from MuSCAT2 wiki.

- whenever a new observation (observation not found on wiki) is loaded, the script will prompt users to register the obslog to the wiki. this is easily achieved by simply following the command line, without the need to access the webpage. the console output can be also copied for end of night reports. (kill two birds with one stone!)

***requirements***
numpy,pandas,requests,tqdm,astropy,pyshorteners

Author: Yugo Kawai (The University of Tokyo)
(Email: yugo6581 @ g.ecc.u-tokyo.ac.jp)

Last update: November 21, 2022
