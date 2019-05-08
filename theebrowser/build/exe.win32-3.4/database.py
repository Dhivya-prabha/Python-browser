#!/usr/bin/python
import sqlite3

def main():
    db=sqlite3.connect('bookmark.db')
    #db.execute("drop table if exists history")
    #db.execute("create table history(title text, url text, epoch text)")
    #db.execute("drop table history")
    #db.execute("insert into history values('Yahoo','http://www.yahoo.com','1424757190')")
    #db.execute("insert into history values('Facebook','https://www.facebook.com','1424757490')")
    rows=db.execute("select * from history order by epoch desc limit 1")
    for row in rows:
        print(row)
        
if __name__ == "__main__": main()