
# TamarawTunes

A simple music player application built using Python and Flask.

## Requirements
- Python
- Flask
- mysql-connector-python
- Pytube
- Pywget

## Installation

__Clone repository__
```
  git clone https://github.com/tadiyusss/tamarawtunes
  cd tamarawtunes
```
__Install requirements__
```
    pip3 install -r requirements.txt
```

before running the script you should edit the config.json file into your mysql credentials

__Run script__
```
    python3 app.py
```

__Run in gunicorn__
```
    gunicorn --bind 0.0.0.0 app:app --timeout 200
```
