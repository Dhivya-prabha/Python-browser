import os, sys

from PyQt4.QtCore import QObject, QTimer, QUrl, QVariant, SIGNAL
from PyQt4.QtGui import *
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QTcpSocket
from PyQt4.QtWebKit import QWebView
from ui_mainwindow import Ui_MainWindow
from flickcharm import *
import bookmark 
from ui_bookmark import *
from _ast import Str
from re import UNICODE
import webbrowser
try:
    from PyQt4.QtCore import QString
except ImportError:
    # we are using Python3 so QString is not defined
    QString = type("")

ITEM_WIDTH = 300
ITEM_HEIGHT = 30

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s
                  
class GraphicsView(QtGui.QGraphicsView):
    def __init__(self,mainwindow):
        QtGui.QGraphicsView.__init__(self)
        self.mainwindow = mainwindow
        self.reloadTimer = QtCore.QTimer(self)
        self.connect(self.reloadTimer, QtCore.SIGNAL("timeout()"),self.redisplayWindow)
        self.reloadTimer.setSingleShot(True)
        
    def mouseReleaseEvent(self, event):
        #print 'mouse Release event'
        QtGui.QGraphicsView.mouseReleaseEvent(self, event) 
    
    def redisplayWindow(self):
        #print 'reload URL'
        self.mainwindow.WebBrowser.load(QtCore.QUrl(self.reloadbookmark[1]))
        
    def mousePressEvent(self, event):
        print ('mouse Press event')
        item = self.itemAt(event.pos())
        #print 'bookmark: ',self.mainwindow.booklist[int(item.zValue())]
        bookmark = self.mainwindow.booklist[int(item.zValue())]
        self.reloadTimer.start(300)    
        self.reloadbookmark = bookmark
        QtGui.QGraphicsView.mousePressEvent(self, event)
        self.close()
        
    def mouseDoubleClickEvent(self, event):
        #print ('mouseDoubleClick event')
        if self.reloadTimer and self.reloadTimer.isActive():
            #print 'kill event'
            self.reloadTimer.stop()
        item = self.itemAt(event.pos())
        #print 'bookmark: ',self.mainwindow.booklist[int(item.zValue())]
        data = self.mainwindow.booklist[int(item.zValue())]
        # delete a bookmark
        del self.mainwindow.booklist[int(item.zValue())]
        bookmark.delete(self.mainwindow.db,{'title':data[0],'url':data[1]})
        for item in self.scene().items():
            self.scene().removeItem(item)
        i = 0
        for c in self.mainwindow.booklist:
            item = TextItem(c)
            self.scene().addItem(item)
            item.setPos(0, i * ITEM_HEIGHT)
            item.setZValue(i)
            item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
            i += 1
            
class GraphicsViews(QtGui.QGraphicsView):
    def __init__(self,mainwindow):
        QtGui.QGraphicsView.__init__(self)
        self.mainwindow = mainwindow
        self.reloadTimer = QtCore.QTimer(self)
        self.connect(self.reloadTimer, QtCore.SIGNAL("timeout()"),self.redisplayWindow)
        self.reloadTimer.setSingleShot(True)
        
    def mouseReleaseEvent(self, event):
        #print 'mouse Release event'
        QtGui.QGraphicsView.mouseReleaseEvent(self, event) 
    
    def redisplayWindow(self):
        #print 'reload URL'
        self.mainwindow.WebBrowser.load(QtCore.QUrl(self.reloadbookmark[1]))
        
    def mousePressEvent(self, event):
        #print 'mouse Press event'
        item = self.itemAt(event.pos())
        #print 'bookmark: ',self.mainwindow.booklist[int(item.zValue())]
        history = self.mainwindow.booklists[int(item.zValue())]
        self.reloadTimer.start(300)    
        self.reloadbookmark = history
        QtGui.QGraphicsView.mousePressEvent(self, event)
        self.close()
        
    def mouseDoubleClickEvent(self, event):
        #print ('mouseDoubleClick event')
        if self.reloadTimer and self.reloadTimer.isActive():
            #print 'kill event'
            self.reloadTimer.stop()
        item = self.itemAt(event.pos())
        #print 'bookmark: ',self.mainwindow.booklist[int(item.zValue())]
        hisdata = self.mainwindow.booklists[int(item.zValue())]
        # delete a bookmark
        del self.mainwindow.booklists[int(item.zValue())]
        bookmark.deleteHistory(self.mainwindow.db,{'title':hisdata[0],'url':hisdata[1]})
        for item in self.scene().items():
            self.scene().removeItem(item)
        j = 0
        for d in self.mainwindow.booklists:
            item = TextItem(d)
            self.scene().addItem(item)
            item.setPos(0, j * ITEM_HEIGHT)
            item.setZValue(j)
            item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
            j += 1
            
class parentalControl(QtGui.QMainWindow):
    def mainevent(self):
        print("parental control")
        QtGui.QMainWindow.__init__(self)
        self.addressEdit = QtGui.QLineEdit(self)

class Downloader(QObject):

    def __init__(self, parent = None):
    
        QObject.__init__(self, parent)
        self.path = u""
    
    def saveFile(self, reply):
 
        fileName = (reply.url().path()).split(u"/")[-1]
        if self.path:
            fileName = os.path.join(self.path, fileName)
        
        path = (QFileDialog.getSaveFileName(self.parent(),
            self.tr("Save File"), fileName))
        
        if path:
            try:
                open((path), "w").write(str(reply.readAll()))
                self.path = os.path.split(path)[0]
            except IOError:
                QMessageBox.warning(self.parent(), self.tr("Download Failed"),
                    self.tr("Failed to save the file."))

class GopherReply(QNetworkReply):

    def __init__(self, url):
    
        QNetworkReply.__init__(self)
        self.gopher = QTcpSocket()
        self.gopher.bytesWritten.connect(self.writeGopherData)
        self.gopher.readyRead.connect(self.readGopherData)
        self.gopher.connected.connect(self.getResource)
        self.gopher.disconnected.connect(self.setContent)
        
        self.input = ""
        self.output = ""
        
        self.content = ""
        self.offset = 0
        
        self.setUrl(url)
        self.gopher.connectToHost(url.host(), 70)
    
    def getResource(self):
    
        path = self.url().path()
        if path.isEmpty() or path == u"/":
            self.output = "\r\n"
        else:
            self.output = str(path) + "\r\n"
        
        self.writeGopherData()
    
    def readGopherData(self):
    
        self.input += str(self.gopher.readAll())
    
    def writeGopherData(self, written = 0):
    
        self.output = self.output[written:]
        if self.output:
            self.gopher.write(self.output)
    
    def html(self, text):
    
        return (text).replace(u"&", u"&amp;").replace(u"<", u"&lt;").replace(u">", u"&gt;")
    
    def setContent(self):
    
        if self.url().hasQueryItem(u"type"):
            self.setContentData()
        else:
            self.setContentList()
    
    def setContentData(self):
    
        self.open(self.ReadOnly | self.Unbuffered)
        if self.url().queryItemValue(u"type") == u"text":
            self.setHeader(QNetworkRequest.ContentTypeHeader,
                           QVariant("text/plain"))
        
        self.content = self.input
        self.setHeader(QNetworkRequest.ContentLengthHeader,
                       QVariant(len(self.content)))
        self.readyRead.emit()
        self.finished.emit()
    
    def setContentList(self):
    
        url = QUrl(self.url())
        if not url.path().endsWith(u"/"):
            url.setPath(url.path() + u"/")
        
        base_url = self.url().toString()
        base_path = (url.path())
        
        self.open(self.ReadOnly | self.Unbuffered)
        content = (
            u"<html>\n"
            u"<head>\n"
            u"  <title>" + self.html(base_url) + u"</title>\n"
            u'  <style type="text/css">\n'
            u"  th { background-color: #aaaaaa;\n"
            u"       color: black }\n"
            u"  table { border: solid 1px #aaaaaa }\n"
            u"  tr.odd { background-color: #dddddd;\n"
            u"           color: black\n }\n"
            u"  tr.even { background-color: white;\n"
            u"           color: black\n }\n"
            u"  </style>\n"
            u"</head>\n\n"
            u"<body>\n"
            u"<h1>Listing for " + base_path + u"</h1>\n\n"
            )
        
        lines = self.input.splitlines()
        
        for line in lines:
        
            pieces = line.split("\t")
            if pieces == ["."]:
                break
            try:
                type, path, host, port = pieces[:4]
            except ValueError:
                # This isn't a listing. Let's try returning data instead.
                self.setContentData()
                return
            
            if type[0] == "i":
                content += u"<p>" + self.html(type[1:]) + u"</p>"
            elif type[0] == "h" and path.startswith(u"URL:"):
                content += u"<p><a href=\""+path[4:]+u"\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "0":
                content += u"<p><a href=\"gopher://"+host+u":"+port+path+u"?type=text\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "1":
                content += u"<p><a href=\"gopher://"+host+u":"+port+path+u"\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "4":
                content += u"<p><a href=\"gopher://"+host+u":"+port+path+u"?type=binhex\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "5":
                content += u"<p><a href=\"gopher://"+host+u":"+port+path+u"?type=dos\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "6":
                content += u"<p><a href=\"gopher://"+host+u":"+port+path+u"?type=uuencoded\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "9":
                content += u"<p><a href=\"gopher://"+host+u":"+port+path+u"?type=binary\">"+self.html(type[1:])+u"</a></p>"
            elif type[0] == "g":
                content += u"<img src=\"gopher://"+host+u":"+port+path+u"?type=binary\">"+self.html(type[1:])+u"</img>"
            elif type[0] == "I":
                content += u"<img src=\"gopher://"+host+u":"+port+path+u"?type=binary\">"+self.html(type[1:])+u"</img>"
        
        content += (
            u"</body>\n"
            u"</html>\n"
            )
        
        self.content = content.encode("utf-8")
        
        self.setHeader(QNetworkRequest.ContentTypeHeader, QVariant("text/html; charset=UTF-8"))
        self.setHeader(QNetworkRequest.ContentLengthHeader, QVariant(len(self.content)))
        self.readyRead.emit()
        self.finished.emit()
    
    # QIODevice methods
    
    def abort(self):
        pass
    
    def bytesAvailable(self):
        return len(self.content) - self.offset
    
    def isSequential(self):
        return True
    
    def readData(self, maxSize):
    
        if self.offset < len(self.content):
            end = min(self.offset + maxSize, len(self.content))
            data = self.content[self.offset:end]
            self.offset = end
            return data

class NetworkAccessManager(QNetworkAccessManager):

    def __init__(self, old_manager):
    
        QNetworkAccessManager.__init__(self)
        self.setCache(old_manager.cache())
        self.setCookieJar(old_manager.cookieJar())
        self.setProxy(old_manager.proxy())
        self.setProxyFactory(old_manager.proxyFactory())
    
    def createRequest(self, operation, request, device):
    
        if request.url().scheme() != "gopher":
            return QNetworkAccessManager.createRequest(self, operation, request, device)
        
        if operation == self.GetOperation:
            # Handle gopher:// URLs separately by creating custom QNetworkReply
            # objects.
            reply = GopherReply(request.url())
            return reply
        else:
            return QNetworkAccessManager.createRequest(self, operation, request, device)
    
    @pyqtSlot()
    def slotFinished(self):
        filename = QtGui.QFileDialog.getSaveFileName(MainWindow(),MainWindow().tr("Choose a file name"), ".",MainWindow().tr("IMAGE (*.jpg *.png *.gif)"))
        file = QtCore.QFile(filename)
        if(file.open(QIODevice.WriteOnly)):
            file.write(self.messageBuffer)
            file.close()      
            #QMessageBox.information(None, "Hello!","File has been saved!") 
        else:
            QMessageBox.critical(None, "Hello!","Error saving file!")
    
    #Append current data to the buffer every time readyRead() signal is emitted
    @pyqtSlot()
    def slotReadData(self):
        self.messageBuffer += self.reply.readAll()
        
    def saveImageas(self, url):
        self.messageBuffer = QByteArray()
        #url   = QUrl("http://upload.wikimedia.org/wikipedia/commons/f/fe/Google_Images_Logo.png")
        req   = QNetworkRequest (url)
        self.reply = self.get(req)    
        
        QObject.connect(self.reply,SIGNAL("readyRead()"),self,SLOT("slotReadData()"))
        QObject.connect(self.reply,SIGNAL("finished()"), self,SLOT("slotFinished()"))                        
                                
class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    # Maintain the list of browser windows so that they do not get garbage
    # collected.
    _window_list = []
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        #MainWindow._window_list.append(self)
        # finger scrolling effect
        url='https://www.google.com'            
        self.callWindow(url)
        
    def callWindow(self, url):
            
        self.charm = FlickCharm()
        self.newindowcall=parentalControl()
                
        #CREATE BOOKMARK WINDOW
        self.db = bookmark.connect()
        if self.db:
            self.booklist = bookmark.read(self.db)
            self.booklists = bookmark.readHistory(self.db)

        self.bookview = GraphicsView(self)
        self.scene = QtGui.QGraphicsScene()
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        i = 0
        for c in self.booklist:
            item = TextItem(c)
            self.scene.addItem(item)
            item.setPos(0, i * ITEM_HEIGHT)
            item.setZValue(i)
            item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
            i += 1
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.BspTreeIndex)
        self.bookview.setScene(self.scene)
        self.bookview.setRenderHints(QtGui.QPainter.TextAntialiasing)
        self.bookview.setFrameShape(QtGui.QFrame.NoFrame)
        self.bookview.setWindowTitle("Bookmark List")
        self.charm.activateOn(self.bookview)
        
        self.bookviews = GraphicsViews(self)
        self.scene = QtGui.QGraphicsScene()
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        j = 0
        for d in self.booklists:
            item = TextItem(d)
            self.scene.addItem(item)
            item.setPos(0, j * ITEM_HEIGHT)
            item.setZValue(j)
            item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
            j += 1
                
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.BspTreeIndex)
        self.bookviews.setScene(self.scene)
        self.bookviews.setRenderHints(QtGui.QPainter.TextAntialiasing)
        self.bookviews.setFrameShape(QtGui.QFrame.NoFrame)
        self.bookviews.setWindowTitle("History")
        self.charm.activateOn(self.bookviews)
        
        #MENU ITEM
        self.newwtab = QtGui.QAction(QtGui.QIcon(''), '&New Tab', self)
        #newwtab.triggered.connect(self.createnewTab)
        newwina = QtGui.QAction(QtGui.QIcon(''), '&New Window', self)
        newwina.triggered.connect(self.createNewWindow)
        newpwina = QtGui.QAction(QtGui.QIcon(''), '&New Private Window', self)
        newpwina.triggered.connect(self.parentalControl)
        savea = QtGui.QAction(QtGui.QIcon(''), '&Save Page', self)
        savea.triggered.connect(self.save)
        
        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.newwtab)
        fileMenu.addAction(newwina)
        fileMenu.addAction(newpwina)
        fileMenu.addAction(savea)
        
        redoa = QtGui.QAction(QtGui.QIcon(''), '&Redo', self)
        undoa = QtGui.QAction(QtGui.QIcon(''), '&Undo', self)
        finda = QtGui.QAction(QtGui.QIcon(''), '&Find', self)
        finda.triggered.connect(self.Findtext)
        replacea = QtGui.QAction(QtGui.QIcon(''), '&Replace', self) 

        fileMenu = menubar.addMenu('&Edit')
        fileMenu.addAction(redoa)
        fileMenu.addAction(undoa)
        fileMenu.addAction(finda)
        fileMenu.addAction(replacea)
        
        devtola = QtGui.QAction(QtGui.QIcon(''), '&Developer Tool', self)
        devtola.triggered.connect(self.on_actionZoomOut_triggered) 
        secua = QtGui.QAction(QtGui.QIcon(''), '&Security', self) 
        priva = QtGui.QAction(QtGui.QIcon(''), '&Privacy', self)  
        gena = QtGui.QAction(QtGui.QIcon(''), '&General', self) 

        fileMenu = menubar.addMenu('&Settings')
        fileMenu.addAction(devtola)
        fileMenu.addAction(secua)
        fileMenu.addAction(priva)
        fileMenu.addAction(gena)
         
        #CREATE MAINWINDOW
        self.setupUi(self)
        self.charm.activateOn(self.WebBrowser)
        
        self.lblAddress = QtGui.QLabel("", self.tbAddress)
        self.tbAddress.insertWidget(self.actionGo, self.lblAddress)
        self.addressEdit = QtGui.QLineEdit(self.tbAddress)
        self.tbAddress.insertWidget(self.actionGo, self.addressEdit)
        #FIND TEXT ITEM
        self.search = QtGui.QLineEdit(visible=False, maximumWidth=500, returnPressed=lambda: self.WebBrowser.findText(self.search.text()), textChanged=lambda: self.WebBrowser.findText(self.search.text()))
        #self.closeFind = QtGui.QPushButton(self.WebBrowser)
        #self.closeFind.hide()
        #self.closeFind.setIcon(QtGui.QIcon(":icons/gtk-cancel.png"))
        #self.closeFind.setStyleSheet("width: 10px;position: absolute;margin: 1px 1px 1px 1px;")
        #self.closeFind.clicked.connect(self.hideFindText())
        #self.connect(self.closeFind, QtCore.SIGNAL("clicked()"),self.hideFindText)
        self.showSearch = QtGui.QShortcut("Ctrl+F", self, activated=lambda: self.search.show() or self.search.setFocus())
        #self.showclose = QtGui.QShortcut("Ctrl+F", self, activated=lambda: self.closeFind.show() or self.closeFind.setFocus())
        self.hideSearch = QtGui.QShortcut("Esc", self, activated=lambda: (self.search.hide(), self.setFocus()))
        self.search.setStyleSheet("border: 1px solid lightblue;height: 23px;width: 200px;")
        
        #self.connect(self.closeFind, QtCore.SIGNAL("triggered()"),self.WebBrowser, QtCore.SLOT("self.hideSearch"))
        self.WebBrowser.setLayout(QtGui.QVBoxLayout(spacing=0))
        self.WebBrowser.layout().addWidget(self.search, 0, QtCore.Qt.AlignRight)
        #self.WebBrowser.layout().addWidget(self.closeFind, 0, QtCore.Qt.AlignRight)
        self.WebBrowser.layout().addStretch()
        #self.WebBrowser.layout().addWidget(self.statusBar(), 0, QtCore.Qt.AlignRight)
        self.WebBrowser.layout().setContentsMargins(0, 0, 20, 0)
        
        self.addressEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        self.connect(self.addressEdit, QtCore.SIGNAL("returnPressed()"),self.actionGo, QtCore.SLOT("trigger()"))
                     
        self.connect(self.actionBack, QtCore.SIGNAL("triggered()"),self.WebBrowser, QtCore.SLOT("back()"))
        
        self.connect(self.actionForward, QtCore.SIGNAL("triggered()"),self.WebBrowser, QtCore.SLOT("forward()"))
        
        self.connect(self.actionStop, QtCore.SIGNAL("triggered()"),self.WebBrowser, QtCore.SLOT("stop()"))
        
        self.connect(self.actionRefresh, QtCore.SIGNAL("triggered()"),self.WebBrowser, QtCore.SLOT("reload()"))
        
        self.urlFocus = QtGui.QShortcut("Ctrl+l", self, activated=self.addressEdit.setFocus)
                  
        self.pb = QtGui.QProgressBar(self.statusBar())
        self.pb.setTextVisible(False)
        self.pb.hide()
        self.pb.setStyleSheet("max-width: 120px;float: left;")
        self.statusBar().addPermanentWidget(self.pb)
        
        #DOWNLOAD MANAGER        
        old_manager = self.WebBrowser.page().networkAccessManager()
        self.new_manager = NetworkAccessManager(old_manager)
        self.WebBrowser.page().setNetworkAccessManager(self.new_manager)
        
        self.WebBrowser.page().setForwardUnsupportedContent(True)
        self.downloader = Downloader(self)
        self.WebBrowser.page().unsupportedContent.connect(self.downloader.saveFile)
        
        
        #self.menu=QtGui.QMenu()
        #print(self.WebBrowser)        
        #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.connect(self,SIGNAL("customContextMenuRequested(QPoint)"),self,SLOT("contextMenuRequested(QPoint)"))
        self.WebBrowser.load(QtCore.QUrl(url))
        #WEB INSEPECT ELEMENT
        self.WebBrowser.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        self.inspect = QWebInspector()
        self.inspect.setPage(self.WebBrowser.page())       
        

        '''# CREATE CONTEXTMENU
        self.context_menu = QtGui.QMenu(self.WebBrowser)
        def open_context_menu(point):
            self.context_menu.exec_(self.WebBrowser.mapToGlobal(point))
        self.WebBrowser.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.WebBrowser.customContextMenuRequested.connect(open_context_menu)
  
        self.action = QtGui.QAction('&Back',self, shortcut=QtGui.QKeySequence.Back,statusTip="Click to go back",triggered=self.WebBrowser.back)
        self.action.setShortcut('Backspace')
        self.context_menu.addAction(self.action)
  
        self.action = QtGui.QAction('&Forward', self, shortcut=QtGui.QKeySequence.Forward, statusTip="Click to go forward", triggered=self.WebBrowser.forward)
        self.action.setShortcut('Shift + Backspace')
        self.context_menu.addAction(self.action)
  
        self.action = QtGui.QAction('&Reload', self, shortcut=QtGui.QKeySequence.Refresh, statusTip="Click to refresh", triggered=self.WebBrowser.reload)
        self.context_menu.addAction(self.action)
        self.context_menu.addSeparator()
        
        self.action = QtGui.QAction('&Save as', self, statusTip="Click to save as", triggered=self.save)
        self.action.setShortcut('Ctrl+s')
        self.context_menu.addAction(self.action)
        
        self.preview = QPrintPreviewDialog()
        self.preview.connect(self.preview,SIGNAL("paintRequested (QPrinter*)"),SLOT("print (QPrinter *)"))    
        self.action = QtGui.QAction('&Print', self,shortcut=QtGui.QKeySequence.Print,statusTip="Click to print", triggered=self.filePrintPreview)
        self.action.setShortcut('Ctrl+p')
        self.context_menu.addAction(self.action)
        
        self.action = QtGui.QAction('&View page source', self, statusTip="Click to view page source", triggered=self.callsavefileas)
        self.action.setShortcut('Ctrl+u')
        self.context_menu.addAction(self.action)'''
        
        '''action_copy = self.page().action(QtWebKit.QWebPage.InspectElement)
        action_copy.setEnabled(True)
        context_menu.addAction(action_copy)        
        # add view to_text if in dev mode
        action_page_to_stdout = QtGui.QAction(self.tr('log pageToText'),
                                          None)
        action_page_to_stdout.triggered.connect(self.page_to_stdout)
        context_menu.addAction(action_page_to_stdout)'''
        
        '''self.action = QtGui.QAction('&Inspect Element', self, statusTip="Click to Inspect", triggered=self.on_actionZoomOut_triggered)
        self.action.setShortcut('F12')
        self.context_menu.addAction(self.action)'''
        context_menu = QtGui.QMenu(self.WebBrowser)
        self.WebBrowser.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.WebBrowser.customContextMenuRequested.connect(self.contextMenuEvent)

    def contextMenuEvent(self, point):
        menu = QtGui.QMenu(self)        
        #menu = self.web.page().createStandardContextMenu()
        hit = self.WebBrowser.page().currentFrame().hitTestContent(point)
        url = hit.linkUrl()
        if not url.isEmpty():
            action = menu.addAction('Open link in New Tab')
            action.triggered.connect(lambda: self.WebBrowser.load(url))
            action = menu.addAction('Open link in New Window')
            action.triggered.connect(lambda: self.createNewWindowURL(url))
            action = menu.addAction('Save link as')
            action.triggered.connect(lambda: self.saveLinkas(url))
            action = menu.addAction(self.trUtf8('Copy link address'),self.copyLink)
            #action = menu.addAction('Copy link address')
            #action.triggered.connect(lambda: self.download(url))
            menu.addSeparator()
            action = menu.addAction(self.trUtf8('Inspect'),self.on_actionZoomOut_triggered)
            
        if not hit.imageUrl().isEmpty():
            '''action = menu.addAction('Open link in New Tab')
            action.triggered.connect(lambda: self.download(url))
            action = menu.addAction('Open link in New Window')
            action.triggered.connect(lambda: self.download(url))
            action = menu.addAction('Save link as')
            action.triggered.connect(lambda: self.download(url))
            action = menu.addAction('Copy link address')
            action.triggered.connect(lambda: self.download(url))'''
            self.urls=hit.imageUrl()
            menu.addSeparator()
            #action = menu.addAction(self.trUtf8('Save image as'),self.saveimageas)
            action = menu.addAction('Save image as')
            action.triggered.connect(lambda: self.new_manager.saveImageas(self.urls))
            action = menu.addAction(self.trUtf8('Copy image url'),self.copyImageURL)
            action = menu.addAction(self.trUtf8('Copy image'),self.copyImage)
            action = menu.addAction('Open image in New Tab')
            action.triggered.connect(lambda: self.WebBrowser.load(self.urls))            
            action = menu.addAction(self.trUtf8('Print'),self.filePrintPreview)
            menu.addSeparator()
            action = menu.addAction(self.trUtf8('Inspect'),self.on_actionZoomOut_triggered)
            
        if  menu.isEmpty():
            action = menu.addAction(self.trUtf8('Back'),self.WebBrowser.back)
            action = menu.addAction(self.trUtf8('Forward'),self.WebBrowser.forward)
            action = menu.addAction(self.trUtf8('Refresh'),self.WebBrowser.reload)
            menu.addSeparator()
            action = menu.addAction(self.trUtf8('Select All'),self.selectAll)            
            #action = menu.addAction(self.trUtf8('Select All'),self.WebBrowser.page().SelectAll)            
            action = menu.addAction(self.trUtf8('Save as'),self.callsavefileas)
            action = menu.addAction(self.trUtf8('Print'),self.filePrintPreview)
            action = menu.addAction(self.trUtf8('View Page Source'),self.callsavefileas)
            menu.addSeparator()
            action = menu.addAction(self.trUtf8('Inspect'),self.on_actionZoomOut_triggered)
           
        menu.exec_(self.WebBrowser.mapToGlobal(point))


    '''def findText(self, q, flags):
        if self.hyphenatable:
            #q = (q)
            hyphenated_q = self.javascript(
                'hyphenate_text(%s, "%s")' % (json.dumps(q, ensure_ascii=False), self.loaded_lang), typ='string')
            if QWebPage.findText(self, hyphenated_q, flags):
                return True
        return QWebPage.findText(self, q, flags)'''
    #def hideFindText(self):
        #self.search.hide()
        #self.closeFind.hide()
    #SELECT ALL
    def selectAll(self):
        self.WebBrowser.page().triggerAction(self.WebBrowser.page().SelectAll)
    #COPY LINK ADDRESS
    def copyLink(self):
        self.WebBrowser.pageAction(self.WebBrowser.page().CopyLinkToClipboard).trigger()
    #COPY IMAGE
    def copyImage(self):
        self.WebBrowser.pageAction(self.WebBrowser.page().CopyImageToClipboard).trigger()
    #COPY IMAGE URL
    def copyImageURL(self):
        QApplication.clipboard().setText(self.urls)
    #SAVE IMAGE AS
    '''def saveImageas(self):
        print("hi")
        self.WebBrowser.pageAction(self.WebBrowser.page().DownloadImageToDisk).trigger()'''
                    
    def Findtext(self):
        #FIND TEXT ITEM
        self.search.show()
            
    def createnewTab(self):
        # here put the code that creates the new window and shows it.
        #self.child = QCustomTabWidget()
        #print(self.child.count())
        #self.child.closeTab(self.child.count()-1)
        #maintab=MainWindow()
        QCustomTabWidget().addTab(QtGui.QWidget, "New Tab")
    
    def createNewWindowURL(self,url):
        # here put the code that creates the new window and shows it.
        self.child = QCustomTabWidget()
        #self.child.mainwindow.callWindow(url)
        self.child.show()
            
    def createNewWindow(self):
        # here put the code that creates the new window and shows it.
        self.child = QCustomTabWidget()
        self.child.show()
            
    def callsavefileas(self):
        #self.content = self.WebBrowser().toHtml()
        #self.texteEdit = QtGui.QLineEdit(self.WebBrowser)
        #self.texteEdit.setText(self.WebBrowser.page().mainFrame().toHtml())
        #self.titlel="View Source"
        #self.data = (str(self.titlel),self.WebBrowser.page().mainFrame().toHtml(),(QDateTime.currentMSecsSinceEpoch()))
        #bookmark.addHistory(self.db,self.data)
        #print("hi")
        #self.tabscontent=QCustomTabWidget()
        #self.tabscontent.createNewTab()
        #self.tabs=QtGui.QTabWidget()
        #self.tabs.addTab(MainWindow(), 'View Source')
        #print("bye")
        '''url1 = self.addressEdit.text()
        url2 = self.addressEdit.text()
        http = "view-source:"
        if http not in url1:
            url2="view-source:"+self.addressEdit.text()
        
        self.addressEdit.setText(url2)
        self.WebBrowser.load(QtCore.QUrl(url1))'''
        self.Browsercontent=self.WebBrowser.page().mainFrame().toHtml()
        #Browsercontent=u"<html><head></head><body><form>call me</form></body></html>"
        #.arg(u'\xc5\x9f')
        #self.WebBrowser.setContent(u"self.Browsercontent")
        self.WebBrowser.setContent(self.Browsercontent.encode('utf-8'))
    
    def save(self):
        filename = QtGui.QFileDialog.getSaveFileName(self,self.tr("Choose a file name"), ".",self.tr("HTML (*.html *.htm)"))
        #filename = QtGui.QFileDialog.getSaveFileName(self,"first", ".",self.tr("HTML (*.html *.htm)"))
        #if filename.isEmpty():
            #return
        #title = self.WebBrowser.title()
        #filename=title+".html"
        file = QtCore.QFile(filename)
        if not file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Dock Widgets"),
                                      self.tr("Cannot write file %1:\n%2.")
                                      .arg(filename)
                                      .arg(file.errorString()))
            return
  
        out = QtCore.QTextStream(file)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        out << self.WebBrowser.page().mainFrame().toHtml()
        QtGui.QApplication.restoreOverrideCursor()
        
    def saveLinkas(self, urlss):
        filename = QtGui.QFileDialog.getSaveFileName(self,self.tr("Choose a file name"), ".",self.tr("HTML (*.html *.htm)"))
        #filename = QtGui.QFileDialog.getSaveFileName(self,"first", ".",self.tr("HTML (*.html *.htm)"))
        #if filename.isEmpty():
            #return
        #title = self.WebBrowser.title()
        #filename=title+".html"
        url1=self.WebBrowser.url().toString()
        #print(url1)
        #self.WebBrowser.setUrl(url)
        #print(urlss)
        self.WebBrowser.load(urlss)
        file = QtCore.QFile(filename)
        if not file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Dock Widgets"),
                                      self.tr("Cannot write file %1:\n%2.")
                                      .arg(filename)
                                      .arg(file.errorString()))
            return
  
        out = QtCore.QTextStream(file)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        out << self.WebBrowser.page().mainFrame().toHtml()
        QtGui.QApplication.restoreOverrideCursor()
        self.WebBrowser.load(QtCore.QUrl(url1))
        
    def print_(self):
        self.printer = QtGui.QPrinter()
  
        self.dlg = QtGui.QPrintDialog(self.printer, self)
        if self.dlg.exec_() != QtGui.QDialog.Accepted:
            return  
        self.document.print_(self.printer)
  
        #self.statusBar().showMessage(self.tr("Ready"), 2000)
    def filePrintPreview(self):
        self.printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        self.preview = QtGui.QPrintPreviewDialog(self.printer, self)
        self.preview.paintRequested.connect(self.printPreview)
        self.preview.exec_()
  
    def printPreview(self, printer):
        self.WebBrowser.print_(self.printer)
        
    def page_to_stdout(self):
        """Print to console the current page contents as plain text."""
        #self.action_copy = self.WebBrowser.action(QtWebKit.QWebPage.InspectElement)
        print (self.WebBrowser.page())
        
    #def contextMenuEvent(self, event):
        #self.context_menu.exec_(event.globalPos())
                

    @QtCore.pyqtSignature("")
    def on_actionHome_triggered(self):
        self.WebBrowser.load(QtCore.QUrl("http://www.google.com"))

    def on_WebBrowser_urlChanged(self, url):
        #print (url)
        self.addressEdit.setText(url.toString())
        url = self.WebBrowser.url().toString()
        title = self.WebBrowser.title()
        data = (str(title),str(url),(QDateTime.currentMSecsSinceEpoch()))
        bookmark.addHistory(self.db,data)
        '''item = TextItem(data)
        item.setPos(0, len(self.booklists) * ITEM_HEIGHT)
        item.setZValue(len(self.booklists))
        item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.booklists.append(data)
        self.scene.addItem(item)    
        self.scene.update()'''
        
        self.db = bookmark.connect()
        if self.db:
            self.booklistss = bookmark.readLastHistory(self.db)
            #print("kill=")
            #print(self.booklistss)
        
        
    def on_WebBrowser_titleChanged(self, title):
        #print 'titleChanged',title.toUtf8()
        self.setWindowTitle(title)        

    def on_WebBrowser_loadStarted(self):
        #print 'loadStarted'
        self.pb.show()
        self.pb.setRange(0, 10)
        self.pb.setValue(1)
        
    def on_WebBrowser_loadFinished(self, flag):
        #print 'loadFinished'
        if flag is True:
            self.pb.hide()
            self.statusBar().removeWidget(self.pb)
            
    def on_WebBrowser_loadProgress(self, status):
        self.pb.show()
        self.pb.setRange(0, 100)
        self.pb.setValue(status)      
        
    def calhelpfunc(self):
        url1 = self.addressEdit.text()
        #print(url1)
        #print("hi welcome")    
    @QtCore.pyqtSignature("")
    def on_actionGo_triggered(self):
        #print ("on_actionGo_triggered")
        self.addressEdit.selectedText()
        url1 = self.addressEdit.text()
        http = "http://"
        https = "https://"
        www = "www"

        #if www not in url1 and http not in url1:
        if http in url1 or https in url1:
            url1=self.addressEdit.text()
            #url1="https://www.google.co.in/?#q="+self.addressEdit.text()
        else:
            #url1=self.addressEdit.text()
            url1="https://www.google.co.in/?#q="+self.addressEdit.text()
  
        self.WebBrowser.load(QtCore.QUrl(url1))
        #print ("welcome")
        self.addressEdit.setText(url1)
        #print(self.WebBrowser.title())
        self.tabwid=QCustomTabWidget()
        self.tabwid.setTabText (1, self.WebBrowser.title())
        self.WebBrowser.connect(self.WebBrowser, QtCore.SIGNAL('loadFinished(bool)'), self.checkLoadResult)
        #print("byewelcome")

    @QtCore.pyqtSignature("")
    def on_actionZoomIn_triggered(self):
        #print "on_actionZoomIn_triggered"
        #current = self.WebBrowser.textSizeMultiplier()
        #self.WebBrowser.setTextSizeMultiplier(current+0.2)
        self.bookviews.show()
        temp = bookmark.refreshHistory(self.db)
        
        '''item = TextItem(data)
        item.setPos(0, len(self.booklist) * ITEM_HEIGHT)
        item.setZValue(len(self.booklist))
        item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.booklist.append(data)
        self.scene.addItem(item)    
        self.scene.update()'''
        
    @QtCore.pyqtSignature("")
    def on_actionZoomOut_triggered(self):
        #print "on_actionZoomOut_triggered"
        #current = self.WebBrowser.textSizeMultiplier()
        #self.WebBrowser.setTextSizeMultiplier(current-0.2)
        #print("hi")
        #self.web = QWebView()        
        self.inspect.show()
        
    '''@QtCore.pyqtSignature("")
    def on_actionZoomNormal_triggered(self):
        #print "on_actionZoomNormal_triggered"
        self.WebBrowser.setTextSizeMultiplier(1.0)'''

    @QtCore.pyqtSignature("")
    def on_actionShowBookmark_triggered(self):
        #print "on_actionShowBookmark_triggered"
        self.bookview.show()
        self.db=bookmark.connect()
        self.temp = bookmark.refresh(self.db)
        
    @QtCore.pyqtSignature("")
    def on_actionAddBookmark_triggered(self):
        #print "on_actionAddBookmark_triggered"
        url = self.WebBrowser.url().toString()
        title = self.WebBrowser.title()
        data = (str(title),str(url))
        bookmark.add(self.db,data)
        item = TextItem(data)
        item.setPos(0, len(self.booklist) * ITEM_HEIGHT)
        item.setZValue(len(self.booklist))
        item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.booklist.append(data)
        self.scene.addItem(item)    
        self.scene.update()
    
    def checkLoadResult(self, result):
        #print("waiting")
        if (result == False):
            #self.WebBrowser.load('<html><head><h1>Not Found</h1></head><body><p> Search at  <a href="http://google.com"> google </a></p></body></html>') 
            #url2=self.addressEdit.text()
            self.WebBrowser.setHtml('<html><head><h1>Not Found</h1></head><body><p> Search at <a href="https://www.google.com/search?&q="> google </a></p></body></html>')
    def parentalControl(self):
        #doc = self.WebBrowser.page().mainFrame().documentElement
        #s = doc.findFirst("input[id=say_something]")
        #s.setAttribute("value", "Say Hello To My Little Friends")
        #self.WebBrowser.setHtml('<html><head><title>Parental Control</title><script></script><style>.commonwidth{width: 100%;float: left;}.container{width: 100%;float: left;}.innercontent{width: 98%;float: left;}.rowcount{width: 98%;float: left;}.rowcount div{width: 25%;float: left;}</style></head><body><div class="conrainer"><div class="innercontent"><div class="rowcount"><div><input type="text" name="address" size="50"></div><div><input type="radio" name="access" id="accesson" value="on">&nbsp;ON&nbsp;&nbsp;<input type="radio" name="access" id="accessoff" value="off">&nbsp;OFF</div><div><select name="time" id="time"><option>1 min</option><option>2 min</option><option>5 min</option><option>10 min</option><option>15 min</option><option>20 min</option><option>30 min</option><option>1 hour</option></select></div><div><input type="button" id="save1" class="saveaccess" value="Save"></div></div></div></div></body></html>')
        self.WebBrowser.load(QtCore.QUrl('https://www.google.com'))
        self.WebBrowser.loadFinished.connect(self.searchForm)
       
    def searchForm(self):
        # We landed here because the load is finished. Now, load the root document
        # element. It'll be a QWebElement instance. QWebElement is a QT4.6
        # addition and it allows easier DOM interaction.
        documentElement = self.WebBrowser.page().currentFrame().documentElement()
        # Let's find the search input element.
        inputSearch = documentElement.findFirst('input[title="Google Search"]')
        inputSearch.setAttribute('value', 'drupal')
        # Disconnect ourselves from the signal.
        self.WebBrowser.loadFinished.disconnect(self.searchForm)
        # And connect the next function.
        self.WebBrowser.loadFinished.connect(self.searchResults)
        documentElement.findFirst('input[name=btnG]').evaluateJavaScript('this.click()')
        print("searchform")
    
    def searchResults(self):
        # As seen above, first grab the root document element and then load all g
        # classed list items.
        results = self.WebBrowser.page().currentFrame().documentElement().findAll('li.g')
        # Change the resulting QWebElementCollection into a list so we can easily
        # iterate over it.
        for e in results.toList():
            # Just print the results.
            print (e.toOuterXml().toAscii())
        # We are inside a QT application and need to terminate that properly.
        self.exit()
    #@QtCore.pyqtSignature("")
    #def on_actionHome_triggered(self):
        #print "on_actionHome_triggered"
        #self.WebBrowser.load(QtCore.QUrl("http://www.youtube.com"))
        #self.addressEdit.setText("http://www.youtube.com")
style = """QTabWidget::pane { 
     border-top: 1px solid #C2C7CB;
     position: absolute;
     top: 0em;
 }
QTabWidget::tab-bar {
    alignment: left;
 }
 
 QTabBar::tab {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #E0E0E1, stop: 0.0 #DDDDDD,
                                 stop: 0.0 #D8D8D8, stop: 0.0 #D3D3D3);
    /*background: linear-gradient(#e0e0e0, #fafafa);*/
     border: 1px solid #C4C4C3;
     border-bottom-color: #C2C7CB; 
     border-top-left-radius: 5px;
     border-top-right-radius: 5px; 
     min-width: 150px;
     padding: 2px;
     height: 25px;
     margin-left: 2px;
 }

 QTabBar::tab:selected, QTabBar::tab:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #fafafa, stop: 0.5 #fafafa,
                                 stop: 0.1 #e0e0e0, stop: 0.1 #e0e0e0);
    
    /*background: linear-gradient(#e0e0e0, #fafafa);*/
    border-bottom: none;
 }
QTabBar::tab:last {
    width: 20px;
    min-width: 20px;
    max-width: 20px;
    max-height: 10px;
    margin-top: 15px;
    background: #f0f0f0;
    border: none;
 }
 QTabBar::tab:selected {
     border-color: #9B9B9B;
     border-bottom-color: #C2C7CB; 
 }"""

class QCustomTabWidget(QtGui.QTabWidget):
        
    def __init__ (self, parent = None):
        super(QCustomTabWidget, self).__init__(parent)
        
        self.mainwindow=MainWindow()
        #MainWindow().newwtab.connect(self.closeTab)
        #print("firstTab")
        self.setTabsClosable(True)
        self.setMovable(True)
        self.move(0,0)
        #self.resize(550,550)
        
        self.tabCloseRequested.connect(self.closeTab)
        self.setTabShape(self.Triangular)
        #self.setGeometry(QtCore.QRect(20, 70, 691, 371))
        #self.setElideMode(Qt.ElideNone)
        #self.setStyleSheet("{width: 300px;color: blue;background: black;}")
        self.addTab(MainWindow(), 'New Tab')
        self.setTabIcon(0, QtGui.QIcon("./icons/go-next.png"))
        #self.addTab(MainWindow(), 'Tab 2')
        #self.addTab(MainWindow(), 'Tab 3')
        self.addTab(QtGui.QWidget(), '')
        self.setStyleSheet(style)
        #self.mainwindow.newwtab.triggered.connect(self.closeTab(self.count()-1))       
        
    '''def tabInserted(self, index):
        self.tabBar().setVisible(self.count() > 1)

    def tabRemoved(self, index):
        self.tabBar().setVisible(self.count() > 1)'''
    
        
    def closeTab (self, currentIndex):
        self.db = bookmark.connect()
        if self.db:
            self.booklistss = bookmark.readLastHistory(self.db)
            #print("create=")
        currentQWidget = self.widget(currentIndex)
        numi=self.count()-1
        print(self.count())
            
        if self.count()<3:
            #print("close one")
            if currentIndex!=numi:
                print("close two")
                qApp.quit()
        else:
            #print("close three")
            currentQWidget.deleteLater()
            self.removeTab(currentIndex)
            self.setCurrentIndex(0)
                
        if currentIndex==numi:
            #print("close four")
            currentQWidget.deleteLater()
            self.addTab(MainWindow(), self.mainwindow.WebBrowser.title())
            self.setTabIcon(numi, QtGui.QIcon("./icons/go-next.png"))
            self.addTab(QtGui.QWidget(), '')
            self.setCurrentIndex(numi)

    def createNewTab(self):
        print("addtab")
        self.addTab(MainWindow(), 'New Tab')
        #print("finish")
 
               
if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    mainWindow = QCustomTabWidget()
    #mainwindows=MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

