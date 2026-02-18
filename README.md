# For trading College Basketball
Applies bias automatically.

# Basic Instructions:
* Download python, add python to your path. Add pip to your path. 
* Download VSCode
* Install the python extension for VSCode
* Run the following command in your terminal in the same folder as this. 
(Go to file explorer, right click, open with code, ctrl+`, paste the following)
```
pip install -r "requirements.txt"
```

If that doesn't work, ask a friend.

* Install Playwright. The instructions should appear in the terminal.

* Open 0main.py, change HOS_SCREEN_URL to your multiview URL. 

* Run 0main.py, instantly, press ctrl+c.
* Use the command that vs-code ran by ("  ctrl + `  " then press the up arrow). This is your "*base*" command. 

* Run your base command with the flags -g -c which stand for get and check respectively. These will get and check games and ensure that your HOS_SCREEN_URL  games and the optic odds equivalents are all there. When given three options, one of them to Quit, press (q + Enter) to do so.  

* Now, ensure you have all of your games in matched_games.json in the utils folder. If you do not see your game, find it in 1parsedOO.json and 1parsedHOS.json. Copy and paste them into matched_games.json. The formats are the same, so this should be self-explanitory. Please delete redundant or misleading games. All IDs should be unique. Also, feel free to delete any games with the optic ID not matching today's date. Games are denoted by {} and are comma seperated.

* Hopefully, when you ran the base program with -c -g, you were asked to login to optic odds and HOS. If that is the case, you can now run with the flag -n which means no log in. 

* Now, if everything went according to plan, run the base program with the flag -a -n which is -a auto and -n no login respectively. 

* When asked, press (m + Enter) to monitor the odds. 

* New : Further, add the -i flag to send everything in memory. The default is that you write to local storage which is slower and can cause bad memory blocks. Doing everything in memory is recommended 

* This process is prone to errors. Please rerun if errors occur.


## While Running With Auto Flags
* If there ever is a bad slider, go into ignore.txt, add a line like <hr>
USC spread <hr>
and the program won't send the USC Spread line. It will also display this message in the terminal. 

* As well, I've capped the bias or the slider value at +-5. If you see that the optimal bias is more than 5, slide at your will, but only more in the direction of the 5.

As a side note, if you're programatically inclined, 0.05 is the value of 5. Search the codebase for this and change it as you wish. 

## Warning:
Do not share the `credentials/` directory containing HOSauth.json and OOauth.json files. These are your credentials. If you'd like, delete them after running the program. Note that if you delete them, you'll have to run without the -n flag to save your credentials again. 

# Docs:

utils/Parsejss.py gives all the javascript used to get the data. 

utils/(all things with parsed.json) are used for storing the data from the apis. utilsIM does this in memory. 

utils(IM)/sendbias.py are used for sending the "bias" or slider values. 

utils(IM)/matched_games.json is a matcher from optic to HOS and vise versa.  

utils(IM)/final_stretch3qpartial is a bunch of data cleaning

utils(IM)/calcbias2parital calculates the "bias" or slider values. 


<!-- ## PyInstaller in beta -->
<!--
[link](https://medium.com/@animeshsingh161/how-to-convert-a-python-playwright-script-into-an-executable-app-playwright-with-python-b61d8ff0ca64)
$env:Path += ";C:\Users\mkane\Downloads\pypy3.11\pypy3.11-v7.3.20-win64" after you install pypy. 
% pypy -m pip install -r "requirements.txt"
Create the environment: pypy -m venv myenv
Activate it: .\myenv\Scripts\activate
% Install your stuff: pip install [package_name]
% Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
% Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope CurrentUser
powershell -ExecutionPolicy Bypass -File .\myenv\Scripts\Activate.ps1
.\myenv\Scripts\activate
-->



<!-- ## Making the executable: Not for regular use -->
<!-- python -m venv myvenv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser  
.\myvenv\Scripts\activate
Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope CurrentUser
pip install -r "requirements.txt"
pip install auto-py-to-exe
either
$env:PLAYWRIGHT_BROWSERS_PATH="0"
playwright install chromium --with-deps
or
set PLAYWRIGHT_BROWSERS_PATH=0 && playwright install chromium
auto-py-to-exe
-->
