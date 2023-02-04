from flask import Flask, render_template, url_for, request, redirect, session
from pytube import YouTube
from datetime import date
from pysondb import getDb
import random
import string
import sys
import wget
import os

app = Flask(__name__)
musics_db = getDb('musics.json')

def randomstring(length):
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

app.config['SECRET_KEY'] = randomstring(64)

@app.route('/')
def index():
    return render_template('dashboard.html', music_list=musics_db.getAll())

#api routes

@app.route('/api/get/music', methods=['POST'])
def api_get_music():
    id = request.form.get('id')
    if id == None:
        return_data = {
            'status': 'error',
            'message': id
        }
        return return_data
    elif id == "all":
        return_data = {
            'status': 'success',
            'data': musics_db.getAll()
        }
        return return_data
    else: 
        try:
            db_result = musics_db.getById(id)
        except Exception as e:
            return_data = {
                'status': 'error',
                'message': 'File not found'
            }
            return return_data
        return db_result

@app.route('/api/delete/music', methods=['POST'])
def api_delete_music():
    id = request.form.get('id')
    if musics_db.deleteById(id):
        os.remove('static/musics/' + id + '.mp3')
        os.remove('static/thumbnails/' + id + '.jpg')
        return_data = {
            'status': 'success',
            'message': 'File deleted'
        }
        return return_data
    else:
        return_data = {
            'status': 'error',
            'message': 'File not found'
        }
        return return_data

@app.route('/api/import/music', methods=['POST'])
def api_import():
    url = request.form.get('link')
    if len(musics_db.getByQuery({"url": url})):
        return_data = {
            'status': 'error',
            'message': 'File already imported'
        }
        return return_data
    if request.form.get('source') == "youtube":
        yt = YouTube(url)
        data = {
            'title': yt.title,
            'thumbnail': yt.thumbnail_url,
            'minutes': yt.length // 60,
            'seconds': yt.length % 60,
            'duration': str( yt.length // 60) + ":" + str(yt.length % 60),
            'author': yt.author,
            'date': date.today().strftime("%b %d %Y"),
            'url': url,
        }
        musics_db.add(data)
        id = musics_db.getByQuery({"url": url})[0]['id']
        try:
            wget.download(yt.thumbnail_url, 'static/thumbnails/' + str(id) + '.jpg')
            yt.streams.filter(only_audio=True).first().download('static/musics', str(id) + '.mp3')
        except Exception as e:
            return_data = {
                'status': 'error',
                'message': str(e)
            }
            return return_data
        return_data = {
            'status': 'success',
            'message': 'File imported'
        }
        
        return return_data
    elif request.form.get('source') == "spotify":
        return_data = {
            'status': 'error',
            'message': 'This import method is not supported'
        }
        return return_data
    else: 
        return {
            'status': 'error',
            'message': 'Invalid import method'
        }

if '-d' in sys.argv:
    app.run(host="0.0.0.0", port=25565, debug=True)
else:
    app.run(host="0.0.0.0", port=80)