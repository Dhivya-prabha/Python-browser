#!/usr/bin/env python

#############################################################################
## Copyright 2009 0xLab  
## Authored by Erin Yueh <erinyueh@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
#############################################################################

import sqlite3

def connect():
    #try:            
    db = sqlite3.connect('bookmark.db')            
    #db.execute("CREATE TABLE IF NOT EXISTS history(title text, url text, epoch int)")
    #db.commit()
    #except IOError:
    #print "cannot connect DB"    
    #db = None
    return db
        
def read(db):
    #print "hi welcome"
    dbb = sqlite3.connect('bookmark.db')
    booklist = []
    booklist = dbb.execute("select title,url from bookmark").fetchall()
    #print booklist
    return booklist

def readHistory(db):
    #print "hi welcome"
    dbb = sqlite3.connect('bookmark.db')
    booklist = []
    booklist = dbb.execute("select title,url from history order by epoch desc").fetchall()
    #print booklist
    return booklist

def readLastHistory(db):
    #print "hi welcome"
    dbb = sqlite3.connect('bookmark.db')
    booklist = []
    booklist = dbb.execute("select title, url from history order by epoch desc limit 1").fetchall()
    #print booklist
    return booklist

def add(db,data):
    #print data
    dbb=sqlite3.connect('bookmark.db')
    dbb.execute("INSERT INTO bookmark(title, url) VALUES(?,?)",data)
    dbb.commit()
    
def addHistory(db,data):
    #print data
    dbb=sqlite3.connect('bookmark.db')
    dbb.execute("INSERT INTO history(title, url, epoch) VALUES(?,?,?)",data)
    dbb.commit()
        
def delete(db,data):
    dbb = sqlite3.connect('bookmark.db')
    if data.has_key('title') and data.has_key('url'):
        dbb.execute("delete from bookmark where title=:title and url=:url",data)
        dbb.commit()
        
def deleteHistory(db,data):
    dbb = sqlite3.connect('bookmark.db')
    if data.has_key('title') and data.has_key('url'):
        dbb.execute("delete from history where title=:title and url=:url",data)
        dbb.commit()
        
def refresh(db):
     dbb = sqlite3.connect('bookmark.db')
     booklist = dbb.execute("select title,url from bookmark").fetchall()
     return booklist
 
def refreshHistory(db):
    dbb = sqlite3.connect('bookmark.db')
    booklist = dbb.execute("select title,url from history order by epoch desc").fetchall()
    return booklist
    
def close(db):
    dbb = sqlite3.connect('bookmark.db')
    dbb.close()
        
     
