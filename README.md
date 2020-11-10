# Description
This is a helper tool for downloading files from ILIAS.

It also allows you to download video streams (like in Logik) and interactive videos (like in Machine Learning), 
which you can't download via ILIAS.
It works only for the University of Freiburg.

# Installation
Run the following to install the required python packages:
```bash
pip install -r requirements.txt
```

# Usage
Run the following to start the tool in normal mode:
```bash
python main.py
```
If you don't want the browser to open, run the following:
```bash
python main.py --headless
```

# Disclaimer
I am not responsible for any damage or unintended changes to your ILIAS account that could potentially happen.

The tool crawls through your ILIAS account and searches for files in your courses that are on your desk.

No login data, passwords or personal information are sent to anyone.

Only the ILIAS tree structure is saved locally in a json file in order to load the tree more quickly the next time the tool is started.
