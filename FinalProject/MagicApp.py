
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import *
import sqlalchemy
Base = declarative_base()

from sqlalchemy.orm import sessionmaker
import datetime
import numpy as np
import wordcloud
import pandas as pd
from IPython.display import HTML

import urllib2
import re
from bs4 import BeautifulSoup

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.dates as md

import Tkinter as tk
from Tkinter import *


from dateutil import rrule
import datetime 
from multiprocessing import Pool, cpu_count

#Make a database for the daily decklists
#one tournament -> multiple decks/cards
class Tournament(Base):
    '''
    Tournament objects holds information for a given magic tournament. Most tournament data is pulled from mtggofish. 
    It also pulls the tournament id which is used on the mtgo  website
    variables:
    id -- tournament id from the mtgo website (starts with a 6 and is a 7 digit number)
    mtggofish_id -- id that indexes mtggofish webpage (starts with a 1 and is a 5 digit number)
    tFormat -- tournament format -- deterines what cards can be played
    numPlayers -- number of players within tournament
    date -- date tournament was played

    Also conatins foreign keys for the decks and cards associated with the tournament

    '''
    __tablename__ = 'tournaments'
    id = Column(Integer, primary_key=True)
    mtggofish_id = Column(Integer)
    numPlayers = Column(Integer)
    tFormat =Column(String)
    date = Column(DateTime)
    
    decks = relationship("Deck", backref="tournaments")
    cards = relationship("Card", backref="tournaments")
    
    def __init__(self, id, mtggofish_id, tFormat, numPlayers, date):
        self.id = id
        self.mtggofish_id = mtggofish_id
        self.tFormat = tFormat
        self.numPlayers = numPlayers
        self.date = date
        
    def __repr_(self):
        return "<Tournament(id:#'%s' Format: '%s' '%d' Players Date: '%s')>" %(
                    self.id, self.tFormat, self.numPlayers, self.date)
    
#One Deck --> Multiple Cards
class Deck(Base):
    '''
    Deck objects holds information about a given deck and includes the following information:
    tourney_id -- mtgo id associated with the deck
    place -- what position the deck came in, generally only show the top 4 decks (pulled from mtgo online not mtggofish)
    wins -- the number of wins in the tournament
    losses -- the number of losses in the tournament
    dFormat -- tournament/deck format determins what cards are allowed in the deckID
    archetype -- mtggofish generated archetype
    pid -- player id associated with the deckID

    Has foreighn key of tournament and also is associated wtih the cards within the deck
    '''
    __tablename__ = 'decks'
    id = Column(Integer, primary_key=True)
    tourney_id = Column(Integer, ForeignKey('tournaments.id'))
    place = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    dFormat = Column(String)
    archetype = Column(String)
    pid = Column(String)
    
    cards = relationship("Card", backref="decks")
    #tournament = relationship("Tournament", backref=backref('decks', order_by=did))
    def __init__(self, id, tid, place, wins, losses, dFormat, pid, archetype):
        self.id = id
        self.tourney_id = tid
        self.place = place
        self.wins = wins
        self.losses = losses
        self.dFormat = dFormat
        self.pid = pid
        self.archetype = archetype
    
    def __repr__(self):
        #return "<Deck(id=%s)>" %(self.id)
        return "<Deck(id='%s',  format='%s', pid='%s', place='%d', wins:losses='%d':'%d')>" %(
                    self.id, self.dFormat, self.pid, self.place, self.wins, self.losses)
class Card(Base):
    '''
    Card object contains information about a given card. Makes up the decks. 
    variables:
    name -- magic card name
    deck_id -- foreign key referencing which deck the card is in
    tourney_id -- foreign key referencing in which tournament the card was used
    quanity -- how many copies of the card were used
    cost -- what mana was required to bring it into play
    cType -- card type (creatures, spells, sideboard land)
    '''
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    deck_id = Column(Integer, ForeignKey('decks.id'))
    tourney_id = Column(Integer, ForeignKey('tournaments.id'))
    quantity = Column(Integer)
    cost = Column(String)
    cType = Column(String)
    

    def __init__(self, name, DID, TID, cost, cType, quant):
        self.name = name
        self.deck_id = DID
        self.tourney_id = TID
        self.quantity = quant
        self.cost = cost
        self.cType = cType

    def __repr__(self):
        return "<Card(name='%s' DID='%d', TID='%d', Quantity='%d')>" %(
                        self.name, self.deck_id, self.tourney_id, self.quantity)

def split_seq(seq, size):
        '''
        Divides up large list into multiple small lists attempting to keep them all the same size used for extracting the basic features
        Used for parallelization to speed up deck pulls
        '''
        newseq = []
        splitsize = 1.0/size*len(seq)
        for i in range(size):
            newseq.append(seq[int(round(i*splitsize)):
                int(round((i+1)*splitsize))])
        return newseq

def update_dtf(q = "select * FROM tournaments JOIN decks ON tournaments.id = decks.tourney_id JOIN cards ON decks.id = cards.deck_id"):
    '''
    Updates the global dataframes that are used throughout the Applications
    dtf -- contains the queried database based on query criteria defined either at program opening or through the query pane 
    sortedByFreq -- groups by date and card name show the frequency of a given card accross time. It's sorted by the overall 
                    most used cards across the time period specified
    colorDict -- keeps associations between the card and colors used to display on the plots

    Should be called before any plot updates and after queriers/deck pulls to incorporate new information. If there is not query specification it pulls
    all data
    '''

    global dtf
    global sortedByFreq
    global colorDict

    #Retreive all deck information by querying existing dataframe
    rs = engine.execute(q)
    d = rs.fetchall()
    h = rs.keys()

    #returns pandas dataframe of results
    dtf = pd.DataFrame.from_records(d, columns=h)
    dtf['date'] = pd.to_datetime(dtf['date']) 
    dtf['name'] = dtf['name'].astype(str)   

    byFreq = dtf[(dtf['date']>=dtf['date'].min()) & (dtf['date']<=dtf['date'].max())].groupby([dtf['date'], dtf['name']]).size().unstack().fillna(0)
    sumsortedByFreq = dtf[(dtf['date']>=dtf['date'].min()) & (dtf['date']<=dtf['date'].max())].groupby([dtf['date'], dtf['name']]).size().unstack().fillna(0).sum().order(ascending=False)
    sortedByFreq = byFreq.reindex_axis(sumsortedByFreq.index, axis=1)

    colorDict = makeColor_Dict(sortedByFreq.columns[0:showN].values, colormap=plt.cm.jet_r)

def online_pull(mtggofish_list):
    '''
    webcrawler that iteratively pulls Tournament-->Deck-->Card information from a combination of mtggofish.com and mtgo (wizards.com/Magic)
    adds all resulting tourney, card and deck lists through one session.add_all() call. 
    '''
    cardList = []
    deckList = []
    tourneyList = []
    
    for mtggofish_TID in mtggofish_list: 
        #loop through tournaments
        url = 'http://www.mtggoldfish.com/tournament/%d' %mtggofish_TID
        response = urllib2.urlopen(url)
        tourneyText = response.read()
        soup =BeautifulSoup(tourneyText)
        
        if 'table' in tourneyText:
            #if the tournament exsists there should be a table to pull from if not pass over tourney number 
            #tournament __init__(self, id, numPlayers, date):
            
            mainCont = soup.find("div", attrs={"class":"content main-content"})
            mainContP = mainCont.find("p")
            
            wizards_tid = int(re.findall('#(.*?)</h2>', str(mainCont))[0]) #id used by wizard.com
            
            #get deck/tournement format information
            try:
                tFormat = re.findall('Format: (.*?)<br/>', str(mainContP))[0]
            except:
                tFormat = re.findall('Magic Online (.*?) #', str(mainCont))[0]
            
            #date the tournament was played    
            tDate = datetime.datetime.strptime(re.findall(' Date: (.*?)\n', str(mainContP))[0], "%Y-%m-%d")
            
            #get information about the decks which played in the tournament
            table = soup.find("table", attrs={"class":"table table-condensed table-striped table-bordered"})
            
            # The first tr contains the field names.
            headings = [th.get_text() for th in table.find("tr").find_all("th")]
            
            datasets = []
            
            #for each tournament grab decks
            for n, row in enumerate(table.find_all("tr")[1:]):
                #Deck __init__(self, id, tid, place, wins, losses, dFormat, pid):
                deckID = int(re.findall('/deck/(.*$)', str(row.find("a").get('href')))[0]) #mtggofish deck id
                
                #each deck is a row
                curRow = [td.get_text() for td in row.find_all("td")]
                wins = int(curRow[0])           #num wins
                losses = int(curRow[1])         #num losses
                archetype = str(curRow[2])      #mtggofish archetype
                player = str(curRow[3])         #associated player id
                
                #need to pull place from wizards event coverage
                wiz_url = 'http://www.wizards.com/Magic/Digital/MagicOnlineTourn.aspx?x=mtg/digital/magiconline/tourn/%d' %wizards_tid
                wiz_resp = urllib2.urlopen(wiz_url)
                wiz_Text = wiz_resp.read()
                try:
                    place = re.findall('<heading>' + player + ' \((\d).*\)</heading>', wiz_Text)[0]
                except:
                    place = "seeWinsLosses"
                    
                curDeck = Deck(deckID, wizards_tid, place, wins, losses, tFormat, player, archetype)
                deckList.append(curDeck)
                

                #For each Deck grab cards
                deck_url = 'http://www.mtggoldfish.com/deck/%d' %deckID
                deck_resp = urllib2.urlopen(deck_url)
                deck_Text = deck_resp.read()
                
                deck_soup = BeautifulSoup(deck_Text)
                
                for instance in deck_soup.find("table", attrs={"class":"deck"}).find_all("tr"):
                    
                    #print instance.find_all("td", attrs={"class":"header"}), 
                    #print instance.find_all("td", attr={"class":"frequency"})
                    rowText = [th.get_text() for th in instance.find_all("td")]
                    #print rowText
                    if len(rowText)==1:
                        curType = str(rowText[0])
                    else:
                        curFreq = int(rowText[1])
                        try:
                            curName = str(rowText[2])
                        except:
                            curName = 'NameError_fixLater'
                        mana = ''.join([re.findall('<img alt="(.*?)" src', str(img))[0] for img in instance.find_all("img")])
                        #__init__(self, name, DID, TID, cost, cType, quant)
                        curCard = Card(curName, deckID, wizards_tid, mana, curType, curFreq)
                        cardList.append(curCard)
                        #session.merge(curCard)
                        #to_commitList.append(curCard)
            curTourney = Tournament(wizards_tid, int(mtggofish_TID), tFormat, len(table.find_all("tr")[1:]), tDate)
            tourneyList.append(curTourney)
            #session.merge(curTourney)
            #to_commitList.append(curTourney)
            #change if not using parallelization
            #mtggofish_TID +=1
            #print mtggofish_TID, stopID
           
            
            #if mtggofish_TID > stopID:
            #    stop = True
            print '================id: %d Download Complete=================' %mtggofish_TID
        else:
            return (cardList, deckList, tourneyList)
       
    return (cardList, deckList, tourneyList)

    
def makeColor_Dict(catArray, colormap = plt.cm.jet_r):
    '''
    create dictionary for color assigment using inputed category array and color map
    input:
        catArray --     string array length of the incoming data which will determine categories and coloring 
    returns:
        d -- a color index to category dictionary using a given color map
    
    '''
          #find unique categories 
    inc = np.round(np.linspace(0, colormap.N, num=len(catArray))).astype(int)     #get evenly distributed colors from color map based on num categories
    d = dict((key, value) for (key, value) in zip(catArray, inc))           #dictionary of color to category assignments
    return d

def setColor(catArray, d, colormap = plt.cm.jet_r):
    '''
    generate color list to be used for plotting functions, keeps categories same consistant colors
    
    inputs:
        catArray --      string array the length of working dataset 
        d --             color index to category dictionary will be used for color assignment
        colormap --      desired colormap current working colormap is jet
    returns:
        colorLIst --    a list of tuples to be used for color assignment in plotting functions derived from colorDict
    '''    
    colorList = []
    for i in catArray:
        #print "%s %s %s" %(i, d[i], colormap(d[i]))
        colorList.append(colormap(d[i])) #desired rgba tuple for given category
    return colorList

class deckAnalysis:
    '''
    matplotlib event handler object
    creates an interactive window where you can drag rectangles to specify the duration of time to complete the analysis on. Contains two draggable rectangles
    whose position indicates the time limits by rounding to the closest date. A lighter grey rectangle shows the time period currently selected. Based on these 
    selections the bargraph plot of frequency will be updated to show the frequencies only for the selected time frame. 
    '''
    def __init__(self, startR, stopR, shadedRect, barAx, startTxt, endTxt, dtf):
        self.startR = startR    #left draggable rectanlge indicating the start date 
        self.stopR = stopR      #rigth draggable rectangle indicating the end date
        self.canvas = startR.figure.canvas #time plot associated canvas
        self.ax = barAx #axis associated wtih the bargraph, used for updating the bars
        self.startTxt = startTxt # text object for start date
        self.endTxt = endTxt #text object for end date
        self.dtf = dtf #dtf the current dataframe in use
        self.press = None        
        self.startorstop = None
        self.shadedRect = shadedRect #shadded grey rectangle indicating the time included in the analysis
        self.sortedByFreq = pd.DataFrame() #similar to the sortedByFreq which is updated globally, however once queried using the query pane it will remain 
                                            #the same and not be changed by dragging the start/stop bars

        print 'Deck Analysis tool initialized'

        #calculate full values for sorted by Freq for x-axis of plot
        byFreq = self.dtf[(self.dtf['date']>=self.dtf['date'].min()) & (self.dtf['date']<=self.dtf['date'].max())].groupby([self.dtf['date'], self.dtf['name']]).size().unstack().fillna(0)
        sumsortedByFreq = self.dtf[(self.dtf['date']>=self.dtf['date'].min()) & (self.dtf['date']<=self.dtf['date'].max())].groupby([self.dtf['date'], self.dtf['name']]).size().unstack().fillna(0).sum().order(ascending=False)
        self.sortedByFreqOrig = byFreq.reindex_axis(sumsortedByFreq.index, axis=1)
        self.dateRange = list(rrule.rrule(rrule.DAILY,count=(self.sortedByFreqOrig.index.max()-self.sortedByFreqOrig.index.min() + datetime.timedelta(days=1)).days,dtstart=self.sortedByFreqOrig.index.min()))
        self.origColumns = self.sortedByFreqOrig.columns

        
   
    def changeBars(self, startD, endD):
        ''' 
        update the bar graph to show new values from query
        '''
        self.ax.cla()
        self.ax.bar(np.arange(0, showN), sortedByFreq.iloc[((sortedByFreq.index>=startD) & (sortedByFreq.index<=endD)), 0:showN].sum(axis=0),  color=setColor(sortedByFreq.columns[0:showN].values, colorDict))
        self.ax.get_xaxis().tick_bottom()
        self.ax.get_yaxis().tick_left()
        self.ax.set_ylabel('Frequency of Occurance')
        self.ax.set_xticks(np.arange(0, showN)+.5)
        self.ax.set_xticklabels(sortedByFreq.columns[0:showN], rotation=90,  fontsize=15, va='bottom', y = .025)
        
        self.ax.figure.canvas.show()

        #newValues = self.sortedByFreq.iloc[:, 0:30].mean(axis=0)
        #for bar, newH in zip(self.barGraph, newValues):
        #    bar.set_height(newH)
                   
    def connect(self):
        '''
        connect rectangles for event handling
        '''

        self.cidpressStart = self.startR.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidreleaseStart = self.startR.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion_start = self.startR.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)
        
        self.cidpressStop = self.stopR.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidreleaseStop = self.stopR.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion_stop = self.stopR.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'determine which rectangle is being moved and store the information of original positions'
        if event.inaxes == self.startR.axes:
            contains, attrd = self.startR.contains(event)
            if contains:
                
                x0, y0 = self.startR.xy
                self.press = x0, y0, event.xdata, event.ydata
                self.startorstop = 0

                 
            contains, attrd = self.stopR.contains(event)
            if contains:
                
                x0, y0 = self.stopR.xy
                self.press = x0, y0, event.xdata, event.ydata
                self.startorstop = 1
        return

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over'
        if self.press is None: return
        if event.inaxes != self.startR.axes: return
        x0, y0, xpress, ypress = self.press
        dx = event.xdata - xpress
        #dy = event.ydata - ypress
        #print 'x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f'%(x0, xpress, event.xdata, dx, x0+dx)
        if self.startorstop == 0: #0 indicates that the start bar has moved
            self.startR.set_x(x0+dx)
            self.shadedRect.set_x(x0+dx)
            self.shadedRect.set_width(self.stopR.get_x()-self.startR.get_x())
            self.startTxt.set_text('Start: {:%m/%d/%Y}'.format(sortedByFreq.index[int(np.round(x0+dx))]))

            #get changed array for dates
            #print 'cur x: ' + str(self.dateRange[int(np.floor(x0+dx))]) + ' Length of dtf: ' + str(self.sortedByFreq.index)
            #self.getFreqs(self.dateRange[int(np.floor(x0+dx))], self.dateRange[int(np.floor(self.stopR.get_x()))-1])
            self.changeBars(self.dateRange[int(np.round(x0+dx))], self.dateRange[int(np.round(self.stopR.get_x()))]) #change barplot based on given time period
            self.canvas.show() 
            
                        
            
        if self.startorstop == 1: #1 indicates that the stop bar has moved
            if x0+dx>=len(self.dateRange):
                self.stopR.set_x(len(self.dateRange)-1)
            else:
                self.stopR.set_x(x0+dx)
            self.shadedRect.set_width(self.stopR.get_x()-self.startR.get_x())
            self.endTxt.set_text('End: {:%m/%d/%Y}'.format(sortedByFreq.index[int(np.round(x0+dx))]))

            self.changeBars(self.dateRange[int(np.round(self.startR.get_x()))], self.dateRange[int(np.round(self.stopR.get_x()))])
            self.canvas.show() #update the bargraph canvas
            
        self.startR.figure.canvas.draw() #update the time plot canvas
        
    def on_release(self, event):
        'on release we reset the press data'
        self.press = None
        self.startorstop = None
        #print 'cur xStart: ' + str(np.round(self.startR.get_x())) + ' cur xStop: ' + str(np.round(self.stopR.get_x()))
        #print 'cur start: ' + str(self.dateRange[int(np.floor(self.startR.get_x()))]) + ' cur stop: ' + str(self.dateRange[int(np.floor(self.stopR.get_x()))])
        #print sortedByFreq.iloc[((sortedByFreq.index>=self.dateRange[int(np.round(self.startR.get_x()))]) & (sortedByFreq.index<=self.dateRange[int(np.round(self.stopR.get_x()))])), 0:showN].mean(axis=0)

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.startR.figure.canvas.mpl_disconnect(self.cidpressStart)
        self.startR.figure.canvas.mpl_disconnect(self.cidpressStop)
        self.startR.figure.canvas.mpl_disconnect(self.cidreleaseStart)
        self.startR.figure.canvas.mpl_disconnect(self.cidreleaseStop)
        self.startR.figure.canvas.mpl_disconnect(self.cidmotionStart)
        self.startR.figure.canvas.mpl_disconnect(self.cidmotionStop)


TITLE_FONT = ("Helvetica", 16, "bold")
class magicApp(tk.Tk):
    '''
    Magic analysis GUI

    Left pannel contains Deck pull, query and deck list pannel
        Deck pull Frame-- The deck pull frame allows for pulling new decks off the internet. If just press the pull button without any input in the other frames
                    it will pull the newest decks not currently stored in the database. Can also specific start id (used from the mtggofish website) end ids and the 
                    number of items to pull. The default is to pull 100 enteries from the start. 
        Query Frame -- Allows you to query the given database to only show data by several deck components (e.g. date, card type, deck format etc.)
        Deck List Frame -- Lists the current decks that included in the analysis 
    
    Right Pannel contains the analysis visualizations
    including a wordle generated by card frequencies and an interactive window showing bargraphs and plots of card usage across time

    '''
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        '''
        Generate gui organization
        '''

        global img 
        global showN

        img = np.zeros((500, 700)) #initialize image which will be replaced by wordle after a query
        
        if len(sortedByFreq.columns)*.1>30:
            showN = 30
        else:
            showN = round(len(sortedByFreq.columns)*.1)

        #Set up left side of the GUI
        inputFrame = Frame(self, width=300, height=200)
        inputFrame.pack(side = LEFT, fill=BOTH, expand=1)

        #Top Left corner frame will initialize pull from website
        pullFrame = LabelFrame(inputFrame, width=300, height=10, text='Web Pull')
        pullFrame.pack(side=TOP, fill=BOTH, expand=1)

        labelText = Label(pullFrame, text='Please enter in the ids of decks you wolud like to pull from.\n' + 
                          'If you just want to update the existing, leave the text box empty.', justify='left')
        labelText.pack(side=TOP, fill=BOTH, expand=1)

        startFrame = Frame(pullFrame)
        startFrame.pack(side=TOP, fill=BOTH, expand=1)

        startID = Label(startFrame, textvariable="Query String:", text="Start ID:")
        startID.pack(side=LEFT, expand=1)

        self.startText = Entry(startFrame)
        self.startText.pack(side=RIGHT, expand=1)

        stopFrame = Frame(pullFrame)
        stopFrame.pack(side=TOP, fill=BOTH, expand=1)

        endID = Label(stopFrame, textvariable="Query String1:", text="End ID:")
        endID.pack(side=LEFT, expand=1)

        self.endText = Entry(stopFrame)
        self.endText.pack(side=RIGHT, expand=1)

        numtopullFame = Frame(pullFrame)
        numtopullFame.pack(side=TOP, fill=BOTH, expand=1)

        numtopulllabel = Label(numtopullFame, textvariable="Query String2:", text="Num to pull:")
        numtopulllabel.pack(side=LEFT, expand=1)

        self.numtopullentry = Entry(numtopullFame)
        self.numtopullentry.pack(side=RIGHT, expand=1)

        ent = Button(pullFrame, text='Pull', command=self.pull_decks)    
        ent.pack(side=TOP, expand=1)

        queryFrame = LabelFrame(inputFrame, width=300, height=200,  text='Query')
        queryFrame.pack(side=TOP, fill=BOTH, expand=1)


        #Deck Format selection
        dformatFrame = LabelFrame(queryFrame, text='Deck Format')
        dformatFrame.pack(side=TOP, fill=BOTH, expand=1)

        #if new database initialize basic formats
        try:
            self.curFormats = np.unique(np.array(dtf['dFormat'].values, dtype=str))
        except:
            self.curFormats = ['Standard', 'Pauper', 'Legacy', 'Block']
        self.dformatVar = StringVar(dformatFrame)
        self.dformatVar.set("Standard") # default value

        dformat_label = Label(dformatFrame, text='Deck/Tournament Format: ')
        dformat_label.pack(side=LEFT, expand=1)
                         
        dformat_pullDown = OptionMenu(dformatFrame, self.dformatVar, *self.curFormats)
        dformat_pullDown.pack(side=LEFT, fill=X, expand=1)

        #Date limitations
        dateFrame = LabelFrame(queryFrame, text='Date Restriction')
        dateFrame.pack(side=TOP, fill=BOTH, expand=1)


        dateLabel = Label(dateFrame, textvariable="Query String3:", text="Date: (excludes end Date)")
        dateLabel.pack(side=LEFT, expand=1)

        self.dateStartText = Entry(dateFrame)
        self.dateStartText.pack(side=LEFT, expand=1)
        try:
            self.dateStartText.insert(0, '%s' %'{:%Y-%m-%d}'.format(dtf['date'].min()))
        except:
            self.dateStartText.insert(0, 'YYYY-MM-DD')
            
        dateEndLable = Label(dateFrame, textvariable="Query String4:", text="to:")
        dateEndLable.pack(side=LEFT, expand=1)

        self.dateEndText = Entry(dateFrame)
        self.dateEndText.pack(side=LEFT, expand=1)
        try:
            self.dateEndText.insert(0, '%s' %'{:%Y-%m-%d}'.format(dtf['date'].max()+datetime.timedelta(days=1)))
        except:
            self.dateEndText.insert(0, 'YYYY-MM-DD')
        
        #Color limitations
        colorFrame = LabelFrame(queryFrame, text='Color')
        colorFrame.pack(side=TOP, fill=BOTH, expand=1)

        self.incRed = IntVar(value=1)
        self.incBlue = IntVar(value=1)
        self.incWhite = IntVar(value=1)
        self.incBlack = IntVar(value=1)
        self.incGreen = IntVar(value=1)
        self.incColorless = IntVar(value=1)


        redC = Checkbutton(colorFrame, text='Red', variable=self.incRed, \
                           onvalue=1, offvalue=0)
        greenC = Checkbutton(colorFrame, text='Green', variable=self.incGreen, \
                           onvalue=1, offvalue=0)
        blueC = Checkbutton(colorFrame, text='Blue', variable=self.incBlue, \
                           onvalue=1, offvalue=0)
        whiteC = Checkbutton(colorFrame, text='White', variable=self.incWhite, \
                           onvalue=1, offvalue=0)
        blackC = Checkbutton(colorFrame, text='Black', variable=self.incBlack, \
                           onvalue=1, offvalue=0)
        colorlessC = Checkbutton(colorFrame, text='Colorless', variable=self.incColorless, \
                           onvalue=1, offvalue=0)

        redC.pack(side=LEFT)
        greenC.pack(side=LEFT)
        blueC.pack(side=LEFT)
        whiteC.pack(side=LEFT)
        blackC.pack(side=LEFT)
        colorlessC.pack(side=LEFT)

        
        #Card Type Restrictions
        cTypeFrame = LabelFrame(queryFrame, text='Card Type')
        cTypeFrame.pack(side=TOP, fill=BOTH, expand=1)

        self.incCreatures = IntVar(value=1)
        self.incSpells = IntVar(value=1)
        self.incLands = IntVar(value=0)
        self.incSideboard = IntVar(value=0)

        creaturesC = Checkbutton(cTypeFrame, text='Creatures', variable=self.incCreatures, \
                                 onvalue=1, offvalue=0)
        spellsC = Checkbutton(cTypeFrame, text='Spells', variable=self.incSpells, \
                                 onvalue=1, offvalue=0)
        landsC = Checkbutton(cTypeFrame, text='Lands', variable=self.incLands, \
                                 onvalue=1, offvalue=0)
        sideboardC = Checkbutton(cTypeFrame, text='Sideboard', variable=self.incSideboard, \
                                 onvalue=1, offvalue=0)

        creaturesC.pack(side=LEFT)
        spellsC.pack(side=LEFT)
        landsC.pack(side=LEFT)
        sideboardC.pack(side=LEFT)

        query = Button(queryFrame, text='Query', command=self.query_decks)    
        query.pack(side=TOP, expand=1)

        #Deck List Frame
        deckFrame = LabelFrame(inputFrame, height=200, text='Deck List')
        deckFrame.pack(side=TOP, fill=BOTH, expand=1)

        scrollbar = Scrollbar(deckFrame)
        scrollbar.pack( side = RIGHT, fill=BOTH )

        self.mylist = Listbox(deckFrame, yscrollcommand = scrollbar.set, height=20)
        #for decknum in np.unique(reduced_dtf['deck_id']):
        #   mylist.insert(END, "Deck_ID: " + str(decknum) + "    Archetype: " +  str(reduced_dtf['archetype'][reduced_dtf['deck_id']==decknum].irow(0)))

        self.mylist.pack( side = TOP, fill = BOTH)
        scrollbar.config( command = self.mylist.yview )

        self.gen_deckList(dtf)

        # Stack two pages on top of eachother for toggling
        self.container = tk.Frame(self, width=500, height=700)
        self.container.pack(side=TOP, fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in ( StartPage, PageTwo):
            frame = F(self.container, self)
            self.frames[F] = frame

            # put all of the pages in the same location; 
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        self.make_wordle()

    def show_frame(self, c):
        '''Show a frame for the given class'''
        frame = self.frames[c]
        frame.tkraise()

    def pull_decks(self):
        '''
        Multiprocessing deck pull algorithm. First generates list of decks to pull, splits the list to number of cores-1 and performs the deck pull
        '''
        global dtf
        update_dtf()   

        #collect information about which decks to pull from GUI
        try:
            numToPull = int(self.numtopullentry.get())
        except:
            numToPull = 100 #default vaule to pull from start
            
            
        try:
            mtggofish_start = int(self.startText.get())
        except:
            mtggofish_start = dtf['mtggofish_id'].max()+1 #default is to pull newest decks
        
        try:
            mtggofish_end = int(self.endText.get())
        except:
            mtggofish_end = mtggofish_start + numToPull 
        
        #if database exists then remove entries of the pull that have already been completed
        try:
            mtggofish_list = list(set(np.arange(mtggofish_start, mtggofish_end, 1)) - set(dtf['mtggofish_id']))
            
        except:
            mtggofish_list = np.arange(mtggofish_start, mtggofish_end, 1)
        
        print 'Pulling the following decks: ' + str(np.min(mtggofish_list)) + ' to ' + str(np.max(mtggofish_list))
            
        #run parallel processing for deck pull
        if len(mtggofish_list) !=0:
            numprocessors = cpu_count()
            pool = Pool(numprocessors-1)
            chunkedList = split_seq(mtggofish_list, numprocessors)
            results = []
            r = pool.map_async(online_pull, chunkedList, callback=results.append)
            r.wait()
            results = results[0]
            #pooledResults = results.get()
            pool.close()
            #pool.close()
            for result in results:
                    for l in result:
                        print type(l), len(l)
                        if len(l)>0:
                            session.add_all(l)
                            #for i in l:
                            #    session.merge(i)
            
            session.commit()
        print 'pulling complete -- binding dataframe'
        #join tables together
        update_dtf()
        self.dateStartText.delete(0, END)
        self.dateStartText.insert(0, '%s' %'{:%Y-%m-%d}'.format(dtf['date'].min()))
        self.dateEndText.delete(0, END)
        self.dateEndText.insert(0, '%s' %'{:%Y-%m-%d}'.format(dtf['date'].max()))
        self.gen_deckList(dtf)


    def gen_deckList(self, selected_dtf):
        '''
        Inserts values into deck list based on current query
        '''
        self.mylist.delete(0, END)
        for decknum in np.unique(selected_dtf['deck_id']):
           self.mylist.insert(END, "Date: %s" %'{:%m-%d}'.format(selected_dtf['date'][selected_dtf['deck_id']==decknum].irow(0)) + "    Deck_ID: " + str(decknum) + "   TID: " + str(selected_dtf['mtggofish_id'][selected_dtf['deck_id']==decknum].irow(0))+ "    Archetype: " +  str(selected_dtf['archetype'][selected_dtf['deck_id']==decknum].irow(0)) )
        #canvas.show()


    def make_wordle(self):
            '''
            Generates a wordle based on how many decks the cards appear in (not based on how many cards are used total)

            '''
            global dtf
            global img
            #global self.frames[0]
            quant = np.array(dtf.groupby(dtf['name']).size().values, dtype=int)
            names = np.array(dtf.groupby(dtf['name']).size().index, dtype=str)
            if len(names)>200:
                img = wordcloud.make_wordcloud(names[:200], quant[:200], 'test.jpg', '/Applications/anaconda/lib/python2.7/site-packages/pytagcloud/fonts/DroidSans.ttf', width=700, height=500)
            else:
                img = wordcloud.make_wordcloud(names, quant, 'test.jpg', '/Applications/anaconda/lib/python2.7/site-packages/pytagcloud/fonts/DroidSans.ttf', width=700, height=500)
            self.frames[StartPage].ax.imshow(img)
            self.frames[StartPage].ax.set_xticklabels([]) 
            self.frames[StartPage].ax.set_yticklabels([])
            self.frames[StartPage].canvas.show()

    def query_decks(self):
        '''
        Reads in specifications from the GUI and queries the sql database based on restrictions. Updates the global dataframe when complete as well as 
        the data visuatlizations
        '''
        
        global dtf
        global showN 
        
        #Get deck Format specifications
        #deckformat
        dformat = self.dformatVar.get()
        dformatStr = "dFormat = '%s'" %dformat
        
        #Get date restrictions
        dateStart = self.dateStartText.get()    
        dateEnd = self.dateEndText.get()
        dStr = "date BETWEEN '%s' AND '%s'"  %(dateStart, dateEnd)
        
        #Get color restrictions
        colorList = ['r', 'g', 'u', 'w', 'b']
        incList = [self.incRed.get(), self.incGreen.get(), self.incBlue.get(), self.incWhite.get(), self.incBlack.get()]
        colorString = '' 
        for cInc, c in zip(incList, colorList):
            if not cInc:
                colorString += "AND cost NOT LIKE '%" + c + "%'"

        if not self.incColorless.get():
            colorString += "AND cost NOT IN ('', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15')"
        
        #card type
        typeList = ['Creatures', 'Spells', 'Land', 'Sideboard']
        incTList = [self.incCreatures.get(), self.incSpells.get(), self.incLands.get(), self.incSideboard.get()]
        typeString = ''
        for tInc, t in zip(incTList, typeList):
            if not tInc:
                typeString += " AND NOT cType = '" + t + "'"
        
        #card type
        q = "select * FROM tournaments JOIN decks ON tournaments.id = decks.tourney_id JOIN cards ON decks.id = cards.deck_id WHERE %s AND %s %s %s" %(dformatStr, dStr, colorString, typeString)
        update_dtf(q=q)
        self.gen_deckList(dtf)
        self.make_wordle()
        if showN>len(sortedByFreq.columns):
            showN = len(sortedByFreq.columns)
            self.frames[PageTwo].showNText.delete(0, END)
            self.frames[PageTwo].showNText.insert(0, str(showN))
        self.frames[PageTwo].update_pageTwo() #update visualizations based on new query
        

            
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent) 
        '''
        Generates the right hand side of the visualization panel with the wordle. 
        '''
        #Figure for incoming wordle
        fig = matplotlib.figure.Figure(figsize=(9, 9))
        figFrame = LabelFrame(self, text="Image Display:", width=700, height=700)
        figFrame.pack(side = TOP, fill=BOTH)

        figFrame.image = img 

        self.ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0, top=1, right=1, bottom=0)
        im = self.ax.imshow(figFrame.image)
        self.ax.set_xticklabels([]) 
        self.ax.set_yticklabels([])

        self.canvas = FigureCanvasTkAgg(fig, master=figFrame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP,fill=BOTH,expand=1)
        
        label = tk.Label(self, text="Wordle Page", font=TITLE_FONT)
        label.pack(side="top", fill="x")

        button2 = tk.Button(self, text="Visualization",
                            command=lambda: controller.show_frame(PageTwo))
        #button1.pack(side=LEFT)
        button2.pack(side=TOP)


class PageTwo(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        '''
        Visualization panel. Contains two plots, one a bargraph plotting the total number of decks
        each card is in during the time frame specified below. The second plot shows the Proportion
        of decks that contain the given card across time. This plot is interactive and includes two 
        draggable rectangles which set the time frame of interest


        '''
        global colorDict
        label = tk.Label(self, text="DataVisualization", font=TITLE_FONT)
        label.pack(side="top", fill="x")
        #showN = 30
        colorDict = makeColor_Dict(sortedByFreq.columns[0:showN].values, colormap=plt.cm.jet_r)


        graphFrame = Frame(self, width=500, height=700, bg='white')
        graphFrame.pack(side=LEFT, expand=1, fill=BOTH)

        buttonFrame = LabelFrame(graphFrame, width=500, height=50, bg='white')
        buttonFrame.pack(side=TOP, expand=1, fill=BOTH)


        barFrame = Frame(graphFrame, width=500, height=650, bg='white')
        barFrame.pack(side=TOP, expand=1, fill=BOTH)


        #fig and axis for the bar graph
        fig = matplotlib.figure.Figure(facecolor='white')
        self.ax = fig.add_subplot(111)
        fig.subplots_adjust(left = .1, top=.98, bottom=0, right=.98)

        #bargraphs howing how many decks the given card occurs in on the specific date
        freq_BarGraph = self.ax.bar(np.arange(0, showN), sortedByFreq.iloc[:, 0:showN].sum(axis=0),  color=setColor(sortedByFreq.columns[0:showN].values, colorDict), )

        #format axis for plot
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.get_xaxis().tick_bottom()
        self.ax.get_yaxis().tick_left()
        self.ax.set_ylabel('Frequency of Occurance')
        self.ax.set_xticks(np.arange(0, showN)+.5)
        self.ax.set_xticklabels(sortedByFreq.columns[0:showN], rotation=90,  fontsize=15, va='bottom', y=.025)
        self.ax.set_ylim(0, sortedByFreq.iloc[:, 0:showN].sum(axis=0).max()+2)
        #ax.set_xticks([])

        self.canvas = FigureCanvasTkAgg(fig, master=barFrame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP,fill=BOTH,expand=1)


        #bottom frame which will contain the proportion plot across time
        timeFrame = Frame(graphFrame, width=500, height=100, bg='white')
        timeFrame.pack(side=TOP, expand=1, fill=BOTH)

        fig2 = matplotlib.figure.Figure(facecolor='white')
        fig2.subplots_adjust(left=.1, top=.98, right=.98)

        self.canvasTime = FigureCanvasTkAgg(fig2, master=timeFrame)

        self.canvasTime.get_tk_widget().pack(side=TOP,fill=BOTH,expand=1)
        self.canvasTime._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)

        self.ax2 = fig2.add_subplot(111)

        self.ax2.set_color_cycle(setColor(sortedByFreq.columns[0:showN].values, colorDict))

        #format time plot
        timePlot = self.ax2.plot(sortedByFreq.iloc[:, 0:showN]/dtf.groupby([dtf['date'], dtf['deck_id']]).size().count(level='date'))
        self.ax2.spines['top'].set_visible(False)
        self.ax2.spines['right'].set_visible(False)
        self.ax2.set_xticks(np.arange(0, len(sortedByFreq.index)))
        self.ax2.set_xticklabels(['{:%m/%d/}'.format(d) for d in list(rrule.rrule(rrule.DAILY,count=(sortedByFreq.index.max()-sortedByFreq.index.min()+datetime.timedelta(days=1)).days,dtstart=sortedByFreq.index.min()))], fontsize=10)
        self.ax2.set_xlim(0, len(sortedByFreq.index))
        self.ax2.set_ylim(-.01, 1.1)
        self.ax2.set_ylabel('Proportion of Decks')
        self.ax2.set_xlabel('Time')
        self.ax2.set_xticks([])

        #initialize rectangles for interface
        self.rect1 = self.ax2.bar(0, self.ax2.get_ylim()[1]+.01, bottom=-.01, width=.02*len(np.unique(dtf['date'])), color='grey')
        self.rect2 = self.ax2.bar(len(sortedByFreq.index)-1, self.ax2.get_ylim()[1]+.01, bottom=-.01, width=.02*len(np.unique(dtf['date'])), color='grey')
        self.startTxt = self.ax2.annotate('Start: {:%m/%d/%Y}'.format(sortedByFreq.index[0]), xy=(.1*self.ax2.get_xlim()[1], .95), xytext=(.1*self.ax2.get_xlim()[1], .95))
        self.endTxt = self.ax2.annotate('End:   {:%m/%d/%Y}'.format(sortedByFreq.index[-1]), xy=(.1*self.ax2.get_xlim()[1], .90), xytext=(.1*self.ax2.get_xlim()[1], .90))
        self.shadedRect = self.ax2.bar(0, self.ax2.get_ylim()[1]+.01, bottom=-.01, width = len(sortedByFreq.index)-1, color='grey', alpha=.4)
        self.dr1 = deckAnalysis(self.rect1[0], self.rect2[0], self.shadedRect[0], self.ax, self.startTxt, self.endTxt, dtf)
        self.dr1.connect()
        
        self.canvasTime.show()

        #list of current cards displayed. WHen selected will display the card selected
        cardListFrame = Frame(self, width=300, height=500)
        cardListFrame.pack(side=LEFT, expand=1, fill=BOTH)
        self.cardList = Listbox(cardListFrame,  width=50, height=100, font=("Times", 12, "bold"), selectmode=EXTENDED)

        #display selected card image
        cardFrame = LabelFrame(cardListFrame, width=50, height=150, text='card frame')
        cardFrame.pack(side=BOTTOM, expand=1, fill=BOTH)
        self.curCard = 'unknown'
        self.gen_cardList()
        self.cardList.bind("<Key>", self.key)
        self.cardList.bind("<ButtonRelease-1>", self.onclick)
        cardImg = plt.imread('./assets/cards/' +str(self.curCard)+'.jpg')
        cardfig = matplotlib.figure.Figure()

        cardFrame.image = cardImg

        self.cardAx = cardfig.add_subplot(111)
        cardfig.subplots_adjust(left=0, top=1, right=1, bottom=0)
        im = self.cardAx.imshow(cardFrame.image)
        #self.ax = plt.gca()
        #plt.tight_layout(pad=0)
        self.cardAx.set_xticklabels([]) 
        self.cardAx.set_yticklabels([])

        self.cardCanvas = FigureCanvasTkAgg(cardfig, master=cardFrame)
        self.cardCanvas.show()
        self.cardCanvas.get_tk_widget().pack(side=TOP,fill=BOTH,expand=1)
 
        #CHange the number of bars on the graph
        setShowN = Label(buttonFrame, text="Num to show:", bg='white')
        setShowN.pack(side=LEFT)

        self.showNText = Entry(buttonFrame)
        self.showNText.pack(side=LEFT)
        self.showNText.insert(0, str(showN))

        self.showNent = Button(buttonFrame, text="Update",  command=self.updateN)
        self.showNent.pack(side=LEFT)

        #return to wordle button
        returnBut = tk.Button(buttonFrame, text="Return to wordle", 
                           command=lambda: controller.show_frame(StartPage))
        returnBut.pack(side=RIGHT)

    def onclick(self, event):
        '''
        On click select card within card list 
        '''
        #ind = self.cardList.curselection()
        ind = map(int, self.cardList.curselection())[0]
       
        self.curCard = sortedByFreq.columns[ind][:-1]
        try:
            im = plt.imread('./assets/cards/' +str(self.curCard)+'.jpg')
        except:
            im = plt.imread('./assets/cards/unknown.jpg')
        self.cardAx.imshow(im)
        self.cardCanvas.show()
        
    def key(self, event):
        '''
        update card displayed when using directional buttons 
        '''
        if (event.keysym == 'Down'):
            ind = map(int, self.cardList.curselection())[0]+1

        elif event.keysym=='Up':
            #ind = self.cardList.curselection()
            ind = map(int, self.cardList.curselection())[0]-1
            
        else:
            return 

        self.curCard = sortedByFreq.columns[ind][:-1]
        try:
            im = plt.imread('./assets/cards/' +str(self.curCard)+'.jpg')
        except:
            im = plt.imread('./assets/cards/unknown.jpg')
        self.cardAx.imshow(im)
        self.cardCanvas.show()

    
    def update_pageTwo(self):
        '''
        called when querying and when updating the number of bars to show. Specifically updates
        the bargraph, the time plot and the card list
        '''
        global showN
        
        #update bar graph
        self.ax.cla()
        freq_BarGraph = self.ax.bar(np.arange(0, showN), sortedByFreq.iloc[:, 0:showN].sum(axis=0),  color=setColor(sortedByFreq.columns[0:showN].values, colorDict), )
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.get_xaxis().tick_bottom()
        self.ax.get_yaxis().tick_left()
        self.ax.set_ylabel('Frequency of Occurance')
        self.ax.set_xticks(np.arange(0, showN)+.5)
        self.ax.set_xticklabels(sortedByFreq.columns[0:showN], rotation=90,  fontsize=15, va='bottom', y=.025)
        self.ax.set_ylim(0, sortedByFreq.iloc[:, 0:showN].sum(axis=0).max()+2)
        #ax.set_xticks([])


        #update time plot
        self.ax2.cla()
        self.ax2.set_color_cycle(setColor(sortedByFreq.columns[0:showN].values, colorDict))
        #timePlot = self.ax2.plot(sortedByFreq.iloc[:, 0:showN]/sortedByFreq.sum(axis=1), '-')
        timePlot = self.ax2.plot(sortedByFreq.iloc[:, 0:showN]/dtf.groupby([dtf['date'], dtf['deck_id']]).size().count(level='date'))

        self.ax2.set_xticks(np.arange(0, len(sortedByFreq.index)))
        self.ax2.set_xticklabels(['{:%m/%d/}'.format(d) for d in list(rrule.rrule(rrule.DAILY,count=(sortedByFreq.index.max()-sortedByFreq.index.min()+datetime.timedelta(days=1)).days,dtstart=sortedByFreq.index.min()))], fontsize=10)
        self.ax2.set_xlim(0, len(sortedByFreq.index))
        #self.ax2.set_ylim(-.01, .10)
        self.ax2.set_ylim(-.01, 1.1)
        self.ax2.spines['top'].set_visible(False)
        self.ax2.spines['right'].set_visible(False)
        self.ax2.set_ylabel('Proportion of Decks')
        self.ax2.set_xlabel('Time')
        self.ax2.set_xticks([])

        #self.ax2.set_yticks([])

        self.rect1 = self.ax2.bar(0, self.ax2.get_ylim()[1]+.01, bottom=-.01, width=.02*len(np.unique(dtf['date'])), color='grey')
        self.rect2 = self.ax2.bar(len(sortedByFreq.index)-1, self.ax2.get_ylim()[1]+.01, bottom=-.01, width=.02*len(np.unique(dtf['date'])), color='grey')
        self.startTxt = self.ax2.annotate('Start: {:%m/%d/%Y}'.format(sortedByFreq.index[0]), xy=(.1*self.ax2.get_xlim()[1], .95), xytext=(.1*self.ax2.get_xlim()[1], .95))
        self.endTxt = self.ax2.annotate('End:   {:%m/%d/%Y}'.format(sortedByFreq.index[-1]), xy=(.1*self.ax2.get_xlim()[1], .90), xytext=(.1*self.ax2.get_xlim()[1], .90))
        
        self.shadedRect = self.ax2.bar(0, self.ax2.get_ylim()[1]+.01, bottom=-.01, width = len(sortedByFreq.index)-1, color='grey', alpha=.4)
        #drs =[]
        self.dr1 = deckAnalysis(self.rect1[0], self.rect2[0], self.shadedRect[0], self.ax, self.startTxt, self.endTxt, dtf)
        self.dr1.connect()
        self.gen_cardList()
        self.ax.figure.canvas.show()
        self.ax2.figure.canvas.show()
    
    def gen_cardList(self):
        '''
        Fills list box with the current cards selected
        '''
        self.cardList.delete(0, END)
        for n, curCardName in enumerate(sortedByFreq.columns[0:showN]):
            self.cardList.insert(END, curCardName)
            curColor = colorDict[curCardName]
            colorTest = "#%02x%02x%02x" % (plt.cm.jet_r(curColor)[0]*255, plt.cm.jet_r(curColor)[1]*255, plt.cm.jet_r(curColor)[2]*255)
            self.cardList.itemconfig(n, fg=colorTest, bg='grey')
        self.cardList.pack( side = TOP, fill = BOTH)
        #self.scrollbar.config( command = self.cardList.yview ) #canvas.show()
    
    def updateN(self):
        '''
        Updates the number of cards displayed on the bargraph/timeplot
        '''
        global showN
        global colorDict
        showN = int(self.showNText.get())
        if showN>len(sortedByFreq.columns):
            showN = len(sortedByFreq.columns)
            self.showNText.delete(0, END)
            self.showNText.insert(0, str(showN))

        colorDict = makeColor_Dict(sortedByFreq.columns[0:showN].values, colormap=plt.cm.jet_r)

        #updatedtf
        self.update_pageTwo()

if __name__ == "__main__":
    #Generate engine
    global dtf
    global sortedByFreq
    global showN 
    showN= 5
    engine = create_engine('sqlite:///MagicGame.db', echo=False)
    Base = declarative_base()

    if len(engine.table_names())==0:
        Base.metadata.create_all(engine)
    
    #Create Session
    Session = sessionmaker(bind=engine)
    Session = sessionmaker()
    Session.configure(bind=engine)  # once engine is available
    session = Session()
    
    update_dtf()

    app = magicApp()
    app.mainloop()
    