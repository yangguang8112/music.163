
DROP TABLE IF EXISTS music_his;
DROP TABLE IF EXISTS song_list;
DROP TABLE IF EXISTS people_status;

CREATE TABLE music_his (
	  id INTEGER PRIMARY KEY AUTOINCREMENT,
	  song_id INTEGER,
	  status_id INTEGER,
	  week_rank INTEGER,
	  width INTEGER,
	  created TIMESTAMP DEFAULT (datetime('now','localtime'))
);

CREATE TABLE song_list (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	song_code TEXT NOT NULL,
	author_code TEXT NOT NULL,
	song_name TEXT NOT NULL,
	author_name TEXT NOT NULL
);

CREATE TABLE people_status(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	song_num INTEGER NOT NULL,
	created TIMESTAMP DEFAULT (datetime('now','localtime')),
	tag INTEGER NOT NULL
);