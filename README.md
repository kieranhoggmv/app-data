# Install
1. In VSCode, hit Ctrl + Shift + B to set up requirements
2. Copy .env-example to .env and fill in values
3. Grab the correct version of chromedriver from here: https://googlechromelabs.github.io/chrome-for-testing/, currently https://storage.googleapis.com/chrome-for-testing-public/129.0.6668.89/win64/chromedriver-win64.zip
4. Unzip, rename it to chromedriver_win64 (no .exe extension) then copy to .venv\Lib\site-packages\chromedriver_py\ (you can right click the folder in VSCode > Reveal in File Explorer)

# Setup
To use to run on a schedule
1. Copy run-example.bat to run.bat and change the paths to the correct locations
2. Open Task Scheduler in Windows
3. Create Basic Task > Add a name > Daily or When I log on > Specify time > Browse to run.bat

# Notes
* It looks possible to a) open a new Chrome window alongside existing windows and b) reuse that window for all the scraping, but neither is currently working so it will close existing Chrome sessions first
* It currently uses a mis-mash of a sqlite database for internal storage and .csv for exports, at some point it will support both properly
* As it's a scraper there's loads of flakiness, workarounds and bodges so it may well break often
* Detected when a project is a resubmission is to be added
* Grabbing the feedback review link is to be added
* Progress reviews are to be added