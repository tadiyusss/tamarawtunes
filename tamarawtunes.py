from flask import Flask, render_template, request
from pytube import YouTube
import datetime
from colorama import Fore, Back, Style
import mysql.connector
import random
import string
import json
import wget
import os

app = Flask(__name__)
mysql_details = json.load(open('config.json'))
try:
    mysql_hander  = mysql.connector.connect(host=mysql_details['host'],user=mysql_details['user'],password=mysql_details['password'],database=mysql_details['database'])
except mysql.connector.Error as error:
    print("Failed to connect to database: {}".format(error))
    exit()


def debug(message):
    print(Fore.YELLOW + f"{Fore.YELLOW}[{datetime.datetime.now().strftime('%m-%d-%y %I:%M:%S')}] [ DEBUG ] {Style.RESET_ALL} {str(message)}")

def randomstring(length):
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

app.config['SECRET_KEY'] = randomstring(64)

@app.route('/')
def index():
    if os.path.isdir('static/musics') != True:
        os.mkdir('static/musics')
    if os.path.isdir('static/thumbnails') != True:
        os.mkdir('static/thumbnails')
    return render_template('dashboard.html')

#api routes

@app.route('/api/get/music', methods=['POST'])
def api_get_music():
    try:
        mysql_cursor = mysql_hander.cursor()
        search_query = request.form.get('search_query')
        mode = request.form.get('mode')
        if search_query == None:
            return_data = {
                'status': 'error',
                'message': 'Invalid id'
            }
            return return_data
        elif search_query == "all":
            debug("Fetching all musics")
            music_list = []
            mysql_cursor.execute("SELECT * FROM tamarawtunes_musics")
            rows = mysql_cursor.fetchall()
            for row in rows:
                data = {
                    'id': row[0],
                    'title':row[1],
                    'thumbnail': row[2],
                    'minutes': row[3],
                    'seconds': row[4],
                    'duration': row[5],
                    'author': row[6],
                    'date': row[7],
                    'identifier': row[8],
                    'url': row[9]
                }
                music_list.append(data)
            return_data = {
                'status': 'success',
                'data': music_list
            }
            return return_data
        elif mode == "title_search" and search_query != "":
            debug('Searching for title: ' + search_query)
            mysql_cursor.execute('SELECT * FROM tamarawtunes_musics WHERE title LIKE %s OR author LIKE %s', ('%' + search_query + '%', '%' + search_query + '%'))
            mysql_result = mysql_cursor.fetchall()
            if len(mysql_result) == 0:
                return_data = {
                    'status': 'error',
                    'message': 'File not found'
                }
                return return_data
            else:
                music_list = []
                for row in mysql_result:
                    data = {
                        'id': row[0],
                        'title':row[1],
                        'thumbnail': row[2],
                        'minutes': row[3],
                        'seconds': row[4],
                        'duration': row[5],
                        'author': row[6],
                        'date': row[7],
                        'identifier': row[8],
                        'url': row[9]
                    }
                    music_list.append(data)
                return_data = {
                    'status': 'success',
                    'data': music_list
                }
                return return_data
        elif mode == "id_search" and search_query != "":
            debug('Searching for id: ' + search_query)
            mysql_cursor.execute("SELECT * FROM tamarawtunes_musics WHERE identifier=%s", (search_query,))
            mysql_result = mysql_cursor.fetchall()
            if len(mysql_result) == 0:
                return_data = {
                    'status': 'error',
                    'message': 'File not found'
                }
                return return_data
            else:
                return_data = {
                    'status': 'success',
                    'data': {
                        'id': mysql_result[0][0],
                        'title': mysql_result[0][1],
                        'thumbnail': mysql_result[0][2],
                        'minutes': mysql_result[0][3],
                        'seconds': mysql_result[0][4],
                        'duration': mysql_result[0][5],
                        'author': mysql_result[0][6],
                        'date': mysql_result[0][7],
                        'identifier': mysql_result[0][8],
                        'url': mysql_result[0][9]
                    }
                }
                return return_data
        else: 
            mysql_cursor.execute("SELECT * FROM tamarawtunes_musics")
            mysql_result = mysql_cursor.fetchall()
            if len(mysql_result) == 0:
                return_data = {
                    'status': 'error',
                    'message': 'File not found'
                }
                return return_data
            else:
                return_data = {
                    'status': 'success',
                    'data': {
                        'id': mysql_result[0][0],
                        'title': mysql_result[0][1],
                        'thumbnail': mysql_result[0][2],
                        'minutes': mysql_result[0][3],
                        'seconds': mysql_result[0][4],
                        'duration': mysql_result[0][5],
                        'author': mysql_result[0][6],
                        'date': mysql_result[0][7],
                        'identifier': mysql_result[0][8],
                        'url': mysql_result[0][9]
                    }
                }
                return return_data
    except mysql.connector.errors.DatabaseError:
        return_data = {
            'status': 'error',
            'message': 'Flooding detected, skipping this request'
        }
        return return_data
@app.route('/api/delete/music', methods=['POST'])
def api_delete_music():
    
    mysql_cursor = mysql_hander.cursor()
    id = request.form.get('id')
    debug('Deleting music with id: ' + id)
    mysql_cursor.execute("SELECT identifier FROM tamarawtunes_musics WHERE identifier = %s", (id,))
    mysql_result = mysql_cursor.fetchall()
    
    if len(mysql_result) == 0:
        return_data = {
            'status': 'error',
            'message': 'File not found'
        }
        return return_data
    else:
        try:
            mysql_cursor.execute("DELETE FROM tamarawtunes_musics WHERE identifier = %s", (id,))
            mysql_hander.commit()
            os.remove('static/musics/' + id + '.mp3')
            os.remove('static/thumbnails/' + id + '.jpg')
            return_data = {
                'status': 'success',
                'message': 'File deleted'
            }
            return return_data
        except Exception as e:
            return_data = {
                'status': 'error',
                'message': str(e)
            }
            return return_data

@app.route('/api/import/music', methods=['POST'])
def api_import():
    mysql_cursor = mysql_hander.cursor()
    url = request.form.get('link')
    debug('Importing music with url: ' + url)
    #check for mysql duplicates
    mysql_cursor.execute("SELECT identifier FROM tamarawtunes_musics WHERE url = %s", (url,))
    mysql_result = mysql_cursor.fetchall()
    if len(mysql_result) > 0:
        return_data = {
            'status': 'error',
            'message': 'File already exists'
        }
        return return_data
    if request.form.get('source') == "youtube":
        yt = YouTube(url)
        identifier = randomstring(16)
        seconds = yt.length % 60
        if seconds < 10:
            seconds = "0" + str(seconds)
        try:
            debug('Downloading audio file: ' + yt.title)
            yt.streams.filter(file_extension='mp4').first().download('static/musics', identifier + '.mp3')
            debug('Downloading thumbnail: ' + yt.thumbnail_url)
            wget.download(yt.thumbnail_url, 'static/thumbnails/' + identifier + '.jpg')
            debug('Importing youtube data to mysql server')
            mysql_cursor.execute("INSERT INTO tamarawtunes_musics (title, thumbnail, minutes, seconds, duration, author, date, identifier, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (yt.title, yt.thumbnail_url, yt.length // 60, int(seconds), str(yt.length // 60) + ":" + str(seconds), yt.author, datetime.datetime.now().strftime("%b %d %Y"), identifier, url))
            mysql_hander.commit()
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


if __name__ == '__main__':
    app.run(host="0.0.0.0")