from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.db import get_db
import datetime
from myEmail import sendImportantEmail

bp = Blueprint('main_page', __name__)


@bp.route('/')
def index():
    now_time=datetime.datetime.now()
    target_day = now_time.strftime("%Y-%m-%d")
    db = get_db()
    posts = db.execute(
        'SELECT song_num, created, tag'
        ' FROM people_status'
        ' WHERE created >= datetime("now","localtime","start of day");'
    ).fetchall()
    res = get_show_table(posts)
    return render_template('main_page/index.html', res=res, time=target_day)


@bp.route('/history/<int:day>')
def history(day):
    now_time=datetime.datetime.now()
    target_day = now_time+datetime.timedelta(days=-day)
    target_day = target_day.strftime("%Y-%m-%d")
    db = get_db()
    sql = '''
    SELECT song_num, created, tag FROM people_status WHERE created >= datetime("now","localtime","start of day","%d day") AND created < datetime("now","localtime","start of day", "%d day");
    ''' % (-day, 1-day)
    status_date = db.execute(
        sql
    ).fetchall()
    res = get_show_table(status_date)
    return render_template('main_page/hist.html', res=res, time=target_day)

@bp.route('/listenwhat/<day>/<int:hour>/<int:min>')
def listenwhat(day, hour, min):
    '''
    eg:
    day = '2021-06-06'
    time = '17:56'
    '''
    db = get_db()
    sql = '''
    SELECT id FROM people_status WHERE created >= "%s %d:%d" and created < "%s %d:%d";
    ''' % (day, hour, min, day, hour, min+1)
    status_id = db.execute(
        sql
    ).fetchone()[0]
    status_id = int(status_id)
    sql1 = '''
    SELECT song_id  FROM music_his WHERE status_id == %d;
    ''' % (status_id-1)
    sql2 = '''
    SELECT song_id  FROM music_his WHERE status_id == %d;
    ''' % status_id
    last_song_list = db.execute(sql1).fetchall()
    now_song_list = db.execute(sql2).fetchall()
    last_song_list = [i[0] for i in last_song_list]
    now_song_list = [i[0] for i in now_song_list]
    listening_song_id = diff_two_list(last_song_list, now_song_list)
    sql3 = '''
    SELECT * FROM song_list WHERE id = %d;
    ''' % listening_song_id
    song_info = db.execute(sql3).fetchone()
    #song_code, author_code, song_name, author_name = 
    print(dict(song_info))
    html = '''
    <a href="https://music.163.com/#/song?id=%s"><b title="%s">%s</b></a>     <a href="https://music.163.com/#/artist?id=%s">%s</a>
    ''' % (song_info['song_code'], song_info['song_name'], song_info['song_name'], song_info['author_code'], song_info['author_name'])
    return(html)

@bp.route('/upload', methods=['POST'])
def upload():
    data = request.json
    db_insert(data)
    return "OK"

def get_show_table(time_data):
    res = []
    for data in time_data:
        song_num, created, tag = data['song_num'], data['created'], data['tag']
        h, m, s = str(created).split()[1].split(":")
        h, m, s = int(h), int(m), int(s)
        res.append([m, h, tag])
    return res


def check_song_dup(song_data):
    db = get_db()
    song_code, author_code = song_data['song_code'], song_data['author_code']
    song_id = db.execute(
        'SELECT id FROM song_list'
        ' WHERE song_code = ? AND author_code = ?',
        (song_code, author_code)
    ).fetchone()
    if song_id:
        return song_id['id']
    else:
        return

def insert_song(song_data):
    db = get_db()
    db.execute(
        'INSERT INTO song_list (song_code, author_code, song_name, author_name)'
        ' VALUES (?, ?, ?, ?)',
        (song_data['song_code'], song_data['author_code'], song_data['song_name'], song_data['author_name'])
    )
    db.commit()
    song_id = db.execute(
        'SELECT id FROM song_list'
        ' WHERE song_code = ?',
        (song_data['song_code'],)
    ).fetchone()
    return song_id['id']

def insert_status(song_num, tag):
    db = get_db()
    db.execute(
        'INSERT INTO people_status (song_num, tag)'
        ' VALUES (?, ?)',
        (song_num, tag)
    )
    db.commit()
    status_id = db.execute(
        'SELECT id FROM people_status'
        ' WHERE song_num = ?',
        (song_num,)
    ).fetchall()
    return status_id[-1]['id']

def insert_his(song_id, status_id, week_rank, width):
    db = get_db()
    db.execute(
        'INSERT INTO music_his (song_id, status_id, week_rank, width)'
        ' VALUES (?, ?, ?, ?)',
        (song_id, status_id, week_rank, width)
    )
    db.commit()
    return

def db_insert(data):
    db = get_db()
    song_num = data['song_num']
    song_data = data['song_data']
    people_status = db.execute(
        'SELECT song_num, tag, created FROM people_status'
        ' ORDER BY created DESC'
    ).fetchone()
    if people_status:
        if song_num == people_status['song_num']:
            # mang conditions need to conside
            # don't insert 0
            #tag = 0
            #_ = insert_status(song_num, tag)
            now = datetime.datetime.now()
            if now.hour == 10 and now.minute in [0,1,2,3]:
                tag = 0
                status_id = insert_status(song_num, tag)
                for data in song_data:
                song_id = check_song_dup(data)
                if song_id:
                    insert_his(song_id, status_id, data['week_rank'], data['width'])
                else:
                    song_id = insert_song(data)
                    insert_his(song_id, status_id, data['week_rank'], data['width'])
            return
        else:
            tag = 1
            status_id = insert_status(song_num, tag)
            # send mail
            now = datetime.datetime.now()
            last = people_status['created']
            #print("##################################")
            #print((now - last).total_seconds())
            if (now - last).total_seconds() > 600:
                sendImportantEmail()
            #
            for data in song_data:
                song_id = check_song_dup(data)
                if song_id:
                    insert_his(song_id, status_id, data['week_rank'], data['width'])
                else:
                    song_id = insert_song(data)
                    insert_his(song_id, status_id, data['week_rank'], data['width'])
    else:
        tag = 0
        status_id = insert_status(song_num, tag)
        for data in song_data:
            song_id = insert_song(data)
            insert_his(song_id, status_id, data['week_rank'], data['width'])
    return

def diff_two_list(listA, listB):
    for i in range(len(listA)):
        if listA[i] != listB[i]:
            return listB[i]
    return listB[i+1]
