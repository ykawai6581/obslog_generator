# [MuSCAT2] obslog_generator
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MuSCAT2用obslog取得/登録ツールです。

![demo](/img/obslog_generator_demo.gif)

## インストール方法:

	git clone https://github.com/ykawai6581/obslog_generator.git

上記コマンドをターミナル上にて走らせるか、右上のボタンからzipファイルでダウンロードできます。<br/>
ダウンロード後、/obslog_generator 内に移動し、

	pip install -r requirements.txt

を走らせることで、 astropy, numpy, pandas, pyshorteners, requests, tqdm を含む必要パッケージをインストールします。

また、/obslog_generator 内に以下のようなcred.jsonファイルを追加することで、MuSCAT2のwikiにサインインするためにusernameとpasswordを毎回入力する必要がなくなります。<br/>

``` python
#/obslog_generator/cred.json
{
 "username": ******,
 "password": ******
}
```

## 利用方法: 

	python obslog_generator.py [-h] --obsdate=int --obj=str --jd --bypass --edit

--obsdateなど、異なるargsを指定することで、以下のような使い方ができます。

### 1: obslogを取得し、wikiに登録する (eg. 2022年12月10日)

	python obslog_generator.py --obsdate=221210
	
既に登録済みの天体の場合、以下のような出力がされます。
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

wikiに未登録の天体は、以下のように登録するか聞かれます。

	____NEW OBSERVATION______________________________

	The following observation of TOI04659.01 has not been recorded on wiki yet.

	Register TOI04659.01's observation on December 10, 2022 to wiki [y/N]: y
	_________________________________________________
	
流れに沿って情報を入力していくと、登録が完了します。（wikiサイトへのアクセスは不要です。楽チン！）

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
	
最後にリンクが生成されるので、そこから登録を確認できます。<br/>
	
![registration](/img/registration_demo.png)

最終的な出力は、そのままend of night reportにコピペできます。（楽チン！！）
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

Altitude plotとHumidity plotは、それぞれTTFとStellaから取得しており、リンクから確認できます。（スゴイ！）

![altitude and humidity plots](/img/sample_altitude_humidity_plots.png)

### 2: 特定の天体のobslogを取得する (eg. KELT-19)

	python obslog_generator.py --obj="KELT-19"
	
	* variations of names (eg: TOI0XXXX and TOI-XXXX) are treated 
	equally for most cases. planet identifiers (eg: -b, b, .01, .1 etc.) 
	are not necessary because it is difficult to account for the 
	inconsistencies and query may return empty results. case insensitive.
	
このように天体名を指定すると、過去にwikiに登録されたその天体の全てのobslogを取得できます。（スゴイ！！）
	_________________________________________________
	2 observation(s) for KELT-19 are found on: (yymmdd)

	['181129', '200201']

	If no obslogs are returned with the above dates, this may be due to the observation date wrongly entered on MuSCAT2 wiki.           
	eg: Observations past midnight are registered with the date before midnight.           
	In that case, obslog can be found on the next day. [ie: /obslog_generator.py --obsdate=181129 -> 181130]
	_________________________________________________
	Download all [y/N]: n
	Obsdate(s) to download in yymmdd [int or list(int)]: 181129
	
特定の日付のobslogを取得するか、全てのobslogを取得するか選択できます。

### 3: 過去のobslogを修正する
	
	python obslog_generator.py --obsdate=221215 --edit

誤った情報を登録してしまった場合は、--editで編集モードに入り、過去のobslogを修正することができます。修正箇所を指定し、登録時と同じ要領で修正が可能です。

	____EDIT OBSERVATION_____________________________

	Edit TOI05109.01's observation on December 15, 2022 on wiki [y/N]: y

	____What would you like to edit?_________________

	*** separate integers with commmas if multiple **

	Options [0:start time|1:end time|2:weather|3:comments|4:observer]: 2
	Weather: Clear
	_________________________________________________

	Updating... (takes about 10-15 seconds)
	_________________________________________________

	Update complete! (TOI05109.01, December 15, 2022)

	Check at http://research.iac.es/proyecto/muscat/observations/view/2317 

リンクから、修正内容を確認することができます。

### 4: 簡易的なobslogを取得する

	python obslog_generator.py --obsdate=221211 --bypass

--bypassと付け足すことで、MuSCAT2 wikiにログインが必要なcommentsを除いたobslogを生成します。 <br/>
天気はtelescope.orgから取得しています。<br/> ログインがない分、幾分か速く、登録も促されないので、観測中にobslogを確認する際に便利かもしれないです。

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

  --obsdate        	  : 観測日をyymmddフォーマットで指定します。

  --obj			  : 特定の天体を指定します。

  --jd 			  : UTではなくJDでobslogを取得します。

  --bypass 		  : wikiにログインしなくても生成できる範囲のobslogを取得します。

  --edit		  : 登録済みのobslogを修正します。

### 備考:
天体名、観測時間、露光時間、フォーカスを含むメタデータは、shineのobslogから取得しています。天気とコメントはwikiから取得しています。<br/>
wikiに登録されていない場合及びbypassモードでは、telescope.orgから天気を取得しています。<br/>

bypassモードではwikiにログインしないため、ExoFOPからRA, Decを取得しています。

ご意見やバグなどがあれば、教えてください。

### 必要パッケージ:
numpy,pandas,requests,tqdm,astropy,pyshorteners

製作者: 河合優悟 (東京大学)
(eメール: yugo6581 @ g.ecc.u-tokyo.ac.jp)

Last update: Dec 12, 2022
