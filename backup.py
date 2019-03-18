import sqlite3
import sqlitebck

with sqlite3.connect('data.db') as conn:
    with sqlite3.connect('data_backup.db') as conn2:
        sqlitebck.copy(conn, conn2)
