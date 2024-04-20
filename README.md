# tourneypdf

A PDF generator for Scrabble tourneys. There must be an associated Woogles tournament.

See https://blog.woogles.io/posts/2023-04-02-running-an-irl-tournament-with-woogles-tournament-mode/ and https://blog.woogles.io/posts/2023-12-29-irl-tournaments-and-automated-score-entry/ for more info.


# Windows

Windows seems to tag the executable as a virus. Windows is an idiot. Typically this happens at the moment of download. See step 4 here for a solution that should work (fingers crossed):

https://www.makeuseof.com/windows-chrome-virus-detected-error/


## How to build on Windows

1) Create new release and download zip, unzip it
2) python -m virtualenv venv inside the folder
3) .\venv\Scripts\activate
4) pip install -r requirements.txt
5) pip install pyinstaller
6) flet pack main.py
7) main.exe is in `dist` folder, rename accordingly and upload

## How to build on Mac

1) `inv build-macos`