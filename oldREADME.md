# Basic Instructions:
* Download python, pip install -r "requirements.txt"
* Run 0matcher.py, save and quit. If your game isn't in matched_games.json, add it manually from 1parsedHOS and 1parsedOO. (ctrl+f to see if your game is there)
* Run 0main.py, if you get an error, try to rerun. After 3 failed attempts, idk. 
* Change HOS_SCREEN_URL to your multiview URL 
## When running
 
- When you're running 0main.py, after you log in, don't choose m for monitor. Just ctrl + c to quit the program. 

- Now, do the same but with the flags -g -c which stand for get and check ids respectively. For me, it's 
For me, it's
C:/Users/user/AppData/Local/Python/pythoncore-3.14-64/python.exe c:/Users/user/Downloads/CBBHelper2/0main.py -n -a
This will ensure everything is in matched_games.json. Again, when asked to monitor, ctrl + c to quit. 

- Now, rerun the program but with the flag -n -a at the end. 
For me, it's
C:/Users/user/AppData/Local/Python/pythoncore-3.14-64/python.exe c:/Users/user/Downloads/CBBHelper2/0main.py -n -a
To find how you called python, press the up arrow in the terminal.

- Now that you have ran it with flags, you might get an error. Rerun. 

## While Running With Flags
You're ready TO SEE THE POWER. 
If there ever is a bad slider, go into ignore.txt, add a line like

USC spread

and the program won't send the USC Spread line. 


## Warning:
Do not share your HOSauth.json, OOauth.json file. These are your credentials. If you'd like, delete them after running the program. Note that if you delete them, you'll have to run without flags to save your credentials again. 

## PyInstaller in beta
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

## Making the executable: Not for regular use
python -m venv myvenv
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
