from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.db import get_db

bp = Blueprint('main_page', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT song_num, created, tag'
        ' FROM people_status'
        ' WHERE created >= datetime("now","localtime","start of day");'
    ).fetchall()
    res = get_show_table(posts)
    return render_template('main_page/index.html', res=res)


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
        'SELECT song_num, tag FROM people_status'
        ' ORDER BY created DESC'
    ).fetchone()
    if people_status:
        if song_num == people_status['song_num']:
            # mang conditions need to conside
            # don't insert 0
            #tag = 0
            #_ = insert_status(song_num, tag)
            return
        else:
            tag = 1
            status_id = insert_status(song_num, tag)
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

