from facebook import FacebookService
from facebook import FacebookError, FbResult, DemographicsResult
from facebook import EVT_HAVE_FB_SESSION

from facebook import FacebookError, FbResult
from facebook import NOTES_MESSAGES, NOTES_WALL_COUNT, NOTES_POKES, NOTES_FRIEND_REQUESTS, NOTES_PHOTO_TAGS, NOTES_GROUP_INVITES, NOTES_EVENT_INVITES, NOTES_SHARES, NOTES_USER_DEMO
from facebook import NOTES_TO_METHOD, RESULTS_TO_NOTES

from views import FbResultViews
from events import *

import urlutil
import options
from adservice import AdService, AdDoUpdateEvent, AdDemographicsEvent
from fbqstream import FBQuickStream
from worker import WorkerThread

import wx
import wx.lib.newevent
import wx.lib.hyperlink as hyperlink
import sys
import optparse
import os.path
import shelve, dbhash, bsddb
import socket
#import downloadpics

ID_MENU_CONNECT  = wx.NewId()
ID_MENU_QUIT     = wx.NewId()
ID_MENU_WALL     = wx.NewId()
ID_MENU_POKES    = wx.NewId()
ID_MENU_MESSAGES = wx.NewId()
ID_MENU_CHECK    = wx.NewId()
ID_MENU_OPTIONS  = wx.NewId()
ID_MENU_TAGPHOTO = wx.NewId()
ID_MENU_DOWNLOADPICS = wx.NewId()
ID_MENU_FRIENDREQS = wx.NewId()
ID_MENU_SHARES = wx.NewId()
ID_MENU_GROUPS = wx.NewId()
ID_MENU_EVENTS = wx.NewId()
ID_MENU_LASTEVENTS = wx.NewId()

ID_TIMER_AD = wx.NewId()
ID_UPDATE_TIMER  = wx.NewId()
ID_TIMER_FACEBOOK = wx.NewId()

class FBQTaskBarIcon(wx.TaskBarIcon):

  def __init__(self, *args, **kargs):
    wx.TaskBarIcon.__init__(self, *args, **kargs)
    self.menuBuilder = self.buildOfflineMenu

  def setOnline(self):
    self.menuBuilder = self.buildMenu

  def setOffline(self):
    self.menuBuilder = self.buildOfflineMenu

  def setProcessing(self):
    self.menuBuilder = self.buildProcessingMenu

  def CreatePopupMenu(self):
    return self.menuBuilder()

  def buildProcessingMenu(self):
    self.buildMenu(self, True)

  def buildMenu(self, disableItems=False):
      menu = wx.Menu()
      #menu.Append(ID_MENU_DOWNLOADPICS,"  Download Pics")
      menu.Append(ID_MENU_WALL, "  Wall")
      menu.Append(ID_MENU_POKES, "  Pokes")
      menu.Append(ID_MENU_MESSAGES, "  Messages")
      menu.Append(ID_MENU_TAGPHOTO, "  Photos Tagged")
      menu.Append(ID_MENU_FRIENDREQS, "  Friend Requests")
      menu.Append(ID_MENU_SHARES, '  Shares')
      menu.Append(ID_MENU_GROUPS, '  Group Invites')
      menu.Append(ID_MENU_EVENTS, '  Event Invites')
      menu.Append(ID_MENU_LASTEVENTS, '  Last 5')

      if disableItems:
        for item in menu.GetItems():
          item.Enable(False)

      item = wx.MenuItem(menu,ID_MENU_CHECK,'Check All')
      font = item.GetFont()
      font.SetWeight(wx.BOLD)
      item.SetFont(font)
      menu.AppendItem(item)

      menu.AppendSeparator()
      menu.Append(ID_MENU_OPTIONS, "  Options")
      menu.AppendSeparator()
      menu.Append(ID_MENU_QUIT, "  Quit")
      return menu

  def buildOfflineMenu(self):
      menu = wx.Menu()
      menu.Append(ID_MENU_CONNECT, "Connect")
      menu.AppendSeparator()
      menu.Append(ID_MENU_OPTIONS, "Options")
      menu.AppendSeparator()
      menu.Append(ID_MENU_QUIT, "Quit")
      return menu

class FBQController(wx.Frame):
  def __init__(self, fbResultViews, facebookService, options, shelfdir=None):
    wx.Frame.__init__(self, None, -1, 'title', size = (1, 1),
      style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)
    self.popUpLinger    = None
    self.updateInterval = None
    self.failedCount = 0
    self.loginFirstCount = 0
    self.fbResultViews = fbResultViews
    self.facebookService = facebookService
    self.facebookService.sessionEvtHandler = self
    self.options = options
    self.shelfdir = shelfdir
    self.lastResults = []
    
    self.Bind(wx.EVT_CLOSE, self.onClose)

    self.worker = WorkerThread(self.checkWorker, self.checkCallback, self.checkErrback)
    self.worker.start()

  def onClose(self, evt):
    self.Destroy()

  def onLoginFirst(self, evt):
    if self.loginFirstCount > 0:
      wx.PostEvent(wx.GetApp(), FBQApp_StateOffline_Event())
    else:
      self.loginFirstCount = self.loginFirstCount + 1

      db = shelve.open(self.shelfdir and os.path.join(self.shelfdir,'session') or 'session')
      if db.has_key('sessionKey') and db.has_key('sessionSecret'):
        self.facebookService.sessionKey = db['sessionKey']
        self.facebookService.sessionSecret = db['sessionSecret']
      db.close()
      db = None

      if self.facebookService.sessionKey == '':
        try:
          self.facebookService.auth_createToken()
        except FacebookError, e:
          self.fbResultViews.result_view(e)
          return

        self.fbResultViews.login_first_view(self.facebookService.loginUrl)
      else:
        try:
          self.facebookService.users_getLoggedInUser()
        except FacebookError, e:
          self.facebookService.sessionKey = ''
          self.facebookService.sessionSecret = ''
          try:
            self.facebookService.auth_createToken()
          except FacebookError, e:
            self.fbResultViews.result_view(e)
            return
          self.fbResultViews.login_first_view(self.facebookService.loginUrl)
      
  def onFacebookSession(self, evt):
    self.failedCount = 0
    self.loginFirstCount = 0

  def onFailedServiceCall(self, evt):
    if self.failedCount > 0:
      wx.PostEvent(wx.GetApp(), FBQApp_StateOffline_Event())
    else:
      self.failedCount = self.failedCount + 1

  def check(self, requestList, showNoChangeMessage=True):
    print 'adding work'
    self.worker.addWork([requestList, showNoChangeMessage])

  def checkOptionsFiltered(self, showNoChangeMessage=True):
    rl = [NOTES_USER_DEMO]
    if self.options.messageCheck:
      rl.append(NOTES_MESSAGES)
    if self.options.pokeCheck:
      rl.append(NOTES_POKES)
    if self.options.friendCheck:
      rl.append(NOTES_FRIEND_REQUESTS)

    if self.options.wallCheck:
      rl.append(NOTES_WALL_COUNT)
    if self.options.photoTagCheck:
      rl.append(NOTES_PHOTO_TAGS)

    if self.options.shareCheck:
      rl.append(NOTES_SHARES)
    if self.options.groupCheck:
      rl.append(NOTES_GROUP_INVITES)
    if self.options.eventCheck:
      rl.append(NOTES_EVENT_INVITES)

    self.worker.addWork([rl, showNoChangeMessage])

  def checkWorker(self, work):
    print 'in checkworker'

    requestList, showNoChangeMessage = work

    facebookMethods = []
    for request in requestList:
      method = getattr(self.facebookService, NOTES_TO_METHOD[request])
      facebookMethods.append(method)
    facebookMethods = list(set(facebookMethods))

    results = []
    for method in facebookMethods:
      try:
        result = method()
        if isinstance(result, list):
          for x in result:
            if RESULTS_TO_NOTES[x.__class__] in requestList:
              results.append(x)
        elif RESULTS_TO_NOTES[result.__class__] in requestList:
          results.append(result)
      except FacebookError, e:
        results.append(e)

    return (results, showNoChangeMessage)

  def checkCallback(self, workResult):
    print 'callback'

    resultList, showNoChangeMessage = workResult
    errors = []
    changed = False

    # remove demographics result
    resultList = [ x for x in resultList if isinstance(x,DemographicsResult) == False ]

    for result in resultList:
      if isinstance(result, FacebookError):
        errors.append(result)
      elif isinstance(result, FbResult):
        if result.has_changed() or (showNoChangeMessage and result.has_unread()):
          self.fbResultViews.result_view(result)
          if result not in self.lastResults:
            self.lastResults.append(result)
          if len(self.lastResults) > 5:
            self.lastResults.pop(0)
          changed = True

    print 'with %s errors' % len(errors)
    print 'with %s results' % len(resultList)
    print 'with %s last results' % len(self.lastResults)

    if len(errors) > 0 and len(errors) >= len(resultList):
      self.fbResultViews.showError(errors[0], showNoChangeMessage)
    elif not changed and showNoChangeMessage:
      # show no change message
      self.fbResultViews.result_view(None)

    changed = reduce(lambda x,y: x or y,[ x.has_changed() for x in resultList if isinstance(x, FacebookError) == False ], False)
    unread = reduce(lambda x,y: x or y,[ x.has_unread() for x in resultList if isinstance(x, FacebookError) == False ], False)

    if changed or unread:
      wx.PostEvent(wx.GetApp(), FBQApp_StateIconNew_Event())
    else:
      wx.PostEvent(wx.GetApp(), FBQApp_StateIconDefault_Event())

  def checkErrback(self, workResult):
    print "ERROR?", workResult

  def checkLastResults(self):
    if len(self.lastResults) > 0:
      for result in self.lastResults:
        self.fbResultViews.result_view(result)
    else:
      self.fbResultViews.result_view(None)

# this is global so that FBQuick.OnInit can see it
shelfdir = None

class FBQuick(wx.App):

  def OnInit(self):
    # Initialize our GUI and Service objects; glue them together;
    # then start the application running.

    # --- START CONFIGURATION ---
    buildnumber = '8'
    appName = 'fbQuick %s' % buildnumber
    # Production AdServ feed
    # Old: http://purl.org/net/7017ea47-b0f0-4b32-9cee-44698070916c
    adServiceFeedUri = 'http://x.onedaymarketing.com/x/ads?aff=1&type=text'

    adServiceLocaterUri = 'http://fbquick.com/x/loc'

    #'http://kourier.org/oneday/ads/?aff=2&type=text&o=anaheim,%20ca'
    #adServiceTestUri = 'http://kourier.org/oneday/ads/?aff=2&type=text'

    apiKey = '45df3b00f7ef971f90f2987b1d7033b0'
    secret = 'a76a9e7e61f771281c69cb576360d21f'
    # --- END CONFIGURATION ---

    self.ICONS = {
      'default': wx.Icon('fbquickIcon.ico', wx.BITMAP_TYPE_ICO),
      'new': wx.Icon('fbquickIconNew.ico', wx.BITMAP_TYPE_ICO),
      'offline': wx.Icon('fbquickOffline.ico', wx.BITMAP_TYPE_ICO)
    }

    checkOptionsFilteredSilent = lambda evt: fbqController.checkOptionsFiltered(False)
    checkOptionsFiltered = lambda evt: fbqController.checkOptionsFiltered(True)  
    self.Bind(EVT_FBQA_STATEONLINE, self.onStateOnline)
    self.Bind(EVT_FBQA_STATEOFFLINE, self.onStateOffline)
    self.Bind(EVT_FBQA_STATEICONNEW, self.onStateIconNew)
    self.Bind(EVT_FBQA_STATEICONDEFAULT, self.onStateIconDefault)

    self.adservice = AdService(adServiceFeedUri, adServiceLocaterUri, appName)

    self.optionsPersister= options.OptionsPersistence()
    self.options = self.optionsPersister.load('settings.xml')

    fbResultViews = FbResultViews(self.adservice, self.options)
    self.fbResultViews = fbResultViews

    facebookService = FacebookService(apiKey, secret, shelfdir)
    self.facebookService = facebookService

    fbqController = FBQController(fbResultViews, facebookService, self.options, shelfdir)
    self.fbqController = fbqController
    self.Bind(EVT_FBQC_LOGINFIRST,  fbqController.onLoginFirst)
    self.Bind(EVT_HAVE_FB_SESSION, fbqController.onFacebookSession)
    self.Bind(EVT_FBQC_FAILEDSERVICECALL, fbqController.onFailedServiceCall)

    taskbarIcon = FBQTaskBarIcon()
    self.taskbarIcon = taskbarIcon
    taskbarIcon.SetIcon(self.ICONS['default'], 'fbQuick Online')
    taskbarIcon.Bind(wx.EVT_MENU, self.onQuit, id=ID_MENU_QUIT)
    taskbarIcon.Bind(wx.EVT_MENU, self.onStateOnline, id=ID_MENU_CONNECT)

    taskbarIcon.Bind(wx.EVT_MENU,
      checkOptionsFiltered,
      id=ID_MENU_CHECK) 

    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_WALL_COUNT]), id=ID_MENU_WALL)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_MESSAGES]),
      id=ID_MENU_MESSAGES )
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_POKES]),
      id=ID_MENU_POKES)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_PHOTO_TAGS]),
      id=ID_MENU_TAGPHOTO)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_FRIEND_REQUESTS]),
      id=ID_MENU_FRIENDREQS)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_SHARES]),
      id=ID_MENU_SHARES)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_GROUP_INVITES]),
      id=ID_MENU_GROUPS)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.check([NOTES_USER_DEMO,NOTES_EVENT_INVITES]),
      id=ID_MENU_EVENTS)
    taskbarIcon.Bind(wx.EVT_MENU,
      lambda evt: fbqController.checkLastResults(),id=ID_MENU_LASTEVENTS)
    taskbarIcon.Bind(wx.EVT_MENU, self.onShowOptions, id=ID_MENU_OPTIONS)
    taskbarIcon.Bind(wx.EVT_MENU, self.onDownloadPictures, id=ID_MENU_DOWNLOADPICS)

    # The AdService Timer
    self.adTimer = wx.Timer(self, id=ID_TIMER_AD)
    self.Bind(wx.EVT_TIMER, self.adservice.update_ads, id=ID_TIMER_AD)

    # The FacebookService Timer
    self.facebookTimer = wx.Timer(self, id=ID_TIMER_FACEBOOK)
    self.Bind(wx.EVT_TIMER, checkOptionsFilteredSilent, id=ID_TIMER_FACEBOOK)

    # Bind an event to do the poll check. Mainly for use by double click on the taskbar icon.
    self.Bind(EVT_FBQA_TRIGGERPOLL, checkOptionsFiltered)

    if self.options.startConnected:
      wx.PostEvent(wx.GetApp(), FBQApp_StateOnline_Event())

    return True


  def onStateOnline(self, evt):
    self.taskbarIcon.SetIcon(self.ICONS['default'], 'fbQuick Online')
    self.taskbarIcon.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, lambda evt: wx.PostEvent(wx.GetApp(), FBQApp_TriggerPoll_Event()))
    self.taskbarIcon.setOnline()

    self.Bind(EVT_FBQA_SETTIMERINTERVAL, self.onSetTimerInterval)

    self.adTimer.Start(60000*60)
    self.facebookTimer.Start(60000 * self.options.interval)
    self.fbqController.loginFirstCount = 0

    # tell the Controller to really start processing
    wx.PostEvent(wx.GetApp(), FBQController_LoginFirst_Event())
    wx.PostEvent(self.adservice, AdDoUpdateEvent())

  def onStateOffline(self, evt):
    self.adTimer.Stop()
    self.facebookTimer.Stop()
    self.taskbarIcon.SetIcon(self.ICONS['offline'], 'fbQuick Offline')
    self.taskbarIcon.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.onStateOnline)
    self.taskbarIcon.setOffline()
    self.Unbind(EVT_FBQA_SETTIMERINTERVAL)

  def onShowOptions(self, evt):
    self.frame = options.OptionsFrame(None, self.options, -1, "FBQuick Options", size=(400,400))
    self.frame.button.Bind(wx.EVT_BUTTON, self.onOptionsUpdate) 
    self.frame.CenterOnScreen()
    self.frame.Show()

  def onStateIconNew(self, evt):
    self.taskbarIcon.SetIcon(self.ICONS['new'],'New Notifications')

  def onStateIconDefault(self, evt):
    self.taskbarIcon.SetIcon(self.ICONS['default'],'fbQuick Online')

  def onDownloadPictures(self, evt):
    #self.frame = downloadpics.DownloadPicturesFrame(None, self.facebookService, -1, "FBQuick Options", size=(600,600))
    #self.frame.button.Bind(wx.EVT_BUTTON, self.onOptionsUpdate) 
    #self.frame.CenterOnScreen()
    #self.frame.Show()  
    pass

  def onOptionsUpdate(self, evt):
    self.frame.OnUpdate(evt)
    self.optionsPersister.save(self.options, "settings.xml")
    self.frame.Destroy()
    wx.PostEvent(wx.GetApp(), FBQApp_SetTimerInterval_Event())

  def onSetTimerInterval(self, evt):
    self.facebookTimer.Stop()
    self.facebookTimer.Start(60000 * self.options.interval)

  def onQuit(self, evt):
    self.fbqController.Close(True)
    self.fbResultViews.Close(True)
    self.taskbarIcon.Destroy()
    self.facebookTimer.Stop()
    self.adTimer.Stop()


def main():
  # Set a shorter socket timeout for feedparser.
  # We want feedparser to not hang forever.
  # setdefaulttimeout's parameter is in seconds.
  socket.setdefaulttimeout(7)
  app = FBQuick(0)
  app.MainLoop()


if __name__ == '__main__':

  parser = optparse.OptionParser()

  parser.add_option('--debug', action='store_true', dest='debug', help='output stdout to a debug file (when exe)')
  parser.add_option('--data-dir', dest='datadir', help='set data directory location')
  parser.set_defaults(debug=False,datadir=None)

  opts, args = parser.parse_args()

  if sys.executable.lower().endswith('fbquick.exe'):
    sys.stderr = FBQuickStream()
    if opts.debug:
      sys.stdout = FBQuickStream()

  shelfdir = opts.datadir
  main()

