import wx
import ToasterBox as TB
import time
import urllib
import urlparse
import webbrowser

from adservice import AdDemographicsEvent
from events import FBQController_FailedServiceCall_Event, FBQController_LoginFirst_Event

from facebook import FacebookError, FbResult
from facebook import MessagesResult, PokesResult, FriendRequestsResult, PhotoTagsResult, WallResult, GroupInviteResult, EventInviteResult, SharesResult, DemographicsResult

class MouseMotionEventHandler:
  def __init__(self, box=(0,0,0,0)):
    self.box = box
    self.cursor = wx.NullCursor

  def onMouseMotion(self, evt):
    x, y = evt.GetPosition()
    boxX, boxY, boxW, boxH = self.box
    if x >= boxX and x < (boxX + boxW) and y >= boxY and y < (boxY + boxH):
      self.cursor = evt.GetEventObject().GetCursor()
      evt.GetEventObject().SetCursor(wx.StockCursor(wx.CURSOR_HAND))
    else:
      evt.GetEventObject().SetCursor(self.cursor)
      self.cursor = wx.NullCursor

class MultiClickHandler:
  def __init__(self, fbClickHandler, adClickHandler):
    self.fbClickHandler = fbClickHandler
    self.adClickHandler = adClickHandler
    self.box = (0,0,0,0)

  def clickHandler(self, evt):
    x, y = evt.GetPosition()
    boxX, boxY, boxW, boxH = self.box
    if x >= boxX and x < (boxX + boxW) and y >= boxY and y < (boxY + boxH):
      self.adClickHandler(evt)
    else:
      self.fbClickHandler(evt)

def drawScaledPhoto(image, photo):
  dc = wx.MemoryDC()
  dc.SelectObject(image)
  scaledWidth = 86
  scaledHeight = 66
  if photo.GetHeight() >= photo.GetWidth():
    scaledWidth = scaledHeight * photo.GetWidth()/photo.GetHeight()
  else:
    scaledHeight = scaledWidth * photo.GetHeight() / photo.GetWidth()
  xpos = (90 - scaledWidth) / 2
  ypos = (70 - scaledHeight) / 2
  scPhoto = photo.Scale(scaledWidth,scaledHeight)
  dc.DrawBitmap(scPhoto.ConvertToBitmap(),xpos,ypos)

class FbResultViews(wx.Frame):
  DEFAULT_TOASTERBOX_CLICK_URI = "http://www.facebook.com/"
  DEFAULT_ERROR_URI = "http://purl.org/net/4da9333c-4fcb-4169-81f3-a7497177489f"

  def __init__(self, adservice, options):
    wx.Frame.__init__(self, None, -1, 'title', size = (1, 1),
      style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)
    self.adservice = adservice
    self.options = options
    self.IMAGES = {
      'login' : wx.Bitmap('login.jpg', wx.BITMAP_TYPE_JPEG),		    
      'error' : wx.Bitmap('error.jpg', wx.BITMAP_TYPE_JPEG),
      'poke' : wx.Bitmap('poke.jpg', wx.BITMAP_TYPE_JPEG),
      'message' : wx.Bitmap('message.jpg', wx.BITMAP_TYPE_JPEG),
      'wall' : wx.Bitmap('wall.jpg', wx.BITMAP_TYPE_JPEG),           
      'noChange' : wx.Bitmap('nothing.jpg', wx.BITMAP_TYPE_JPEG),
      'tag': wx.Bitmap('photoTagged.jpg', wx.BITMAP_TYPE_JPEG),
      'tagNoIcon' : wx.Bitmap('photoTaggedNoIcon.jpg', wx.BITMAP_TYPE_JPEG),
      'friend' : wx.Bitmap('friendRequest.jpg', wx.BITMAP_TYPE_JPEG),
      'friendNoIcon' : wx.Bitmap('friendRequestNoIcon.jpg', wx.BITMAP_TYPE_JPEG),
      'share' : wx.Bitmap('share.jpg', wx.BITMAP_TYPE_JPEG),
      'shareNoIcon' : wx.Bitmap('shareNoIcon.jpg', wx.BITMAP_TYPE_JPEG),
      'group' : wx.Bitmap('group.jpg', wx.BITMAP_TYPE_JPEG),
      'groupNoIcon' : wx.Bitmap('groupNoIcon.jpg', wx.BITMAP_TYPE_JPEG),
      'event' : wx.Bitmap('event.jpg', wx.BITMAP_TYPE_JPEG),
      'eventNoIcon' : wx.Bitmap('eventNoIcon.jpg', wx.BITMAP_TYPE_JPEG),
      'delete' : wx.Bitmap('delete.jpg', wx.BITMAP_TYPE_JPEG),  
      }

  def onClose(self, evt):
    self.Destroy()

  def login_first_view(self, url):
    self.showPopUp("Login into your account", image=self.IMAGES['login'])
    webbrowser.open_new(url)

  def result_view(self, result):
    if result is None:
      self.showPopUp('Nothing new', 'title', self.IMAGES['noChange'])
    elif isinstance(result, MessagesResult):
      self.messages_view(result)
    elif isinstance(result, PokesResult):
      self.pokes_view(result)
    elif isinstance(result, SharesResult):
      self.shares_view(result)
    elif isinstance(result, FriendRequestsResult):
      self.friend_requests_view(result)
    elif isinstance(result, PhotoTagsResult):
      self.photo_tags_view(result)
    elif isinstance(result, WallResult):
      self.wall_view(result)
    elif isinstance(result, GroupInviteResult):
      self.group_invite_view(result)
    elif isinstance(result, EventInviteResult):
      self.event_invite_view(result)
    elif isinstance(result, DemographicsResult):
      self.demographics_view(result)
    elif isinstance(result, FacebookError):
      self.showError(result)

  def demographics_view(self, result):
    if result.has_changed():
      evt = AdDemographicsEvent()
      evt.demographics = result
      wx.PostEvent(self.adservice, evt)

  def photo_tags_view(self, result):

    # seems to only be called if there was a some change so ...
    message = '%s untagged photo(s).' % (abs(result.photoTagChange))
    title   = 'Update: Tagged'
    image = self.IMAGES['tag']
    clickHandler = None

    if result.photoTagChange > 0:
      message = '%s new tagged photo(s).' % (result.photoTagChange)
      title = 'Update: Tagged'

      #facebook is dumb, word!
      checkUrl = urlparse.urlsplit(result.popUpLink)
      scheme, netplace,path, query, hostname = urlparse.urlsplit(result.popUpLink)
      if netplace == 'api.facebook.com':
        result.popUpLink = 'http://facebook.com' + path + "?" + query

      photoHandler = MultiClickHandler(lambda x: webbrowser.open_new(self.DEFAULT_TOASTERBOX_CLICK_URI), lambda x:webbrowser.open_new(result.popUpLink))

      clickHandler = photoHandler.clickHandler

      # just read the image from the url stream
      fp = urllib.urlopen(result.picLink)
      photo = wx.ImageFromStream(fp,wx.BITMAP_TYPE_JPEG)
      fp.close()

      # write a scaled version of the image onto a blank notification window
      image = self.IMAGES['tagNoIcon'].ConvertToImage().Copy().ConvertToBitmap()
      drawScaledPhoto(image, photo)

    self.showPopUp(message, title, image, clickHandler)


  def wall_view(self, result):
    if result.wallChange > 0:
      message = '%s new wall post(s).' % result.wallChange
      title = 'Update: Wall'
      image = self.IMAGES['wall']
    else:
      message = '%s deleted wall post(s).' % abs(result.wallChange)
      title = 'Update: Wall'
      image = self.IMAGES['delete']

    self.showPopUp(message, title, image, lambda x:webbrowser.open_new(result.popUpLink))


  def messages_view(self, result):
    message = """%s unread message(s). Last at %s""" % (result.unseenMessages, time.strftime('%I:%M:%S %p',time.localtime(result.messageRecent)))
    title = 'Update: Message'
    image = self.IMAGES['message']

    self.showPopUp(message, title, image, lambda x:webbrowser.open_new(result.popUpLink))

  def pokes_view(self, result):
    message = '%s unseen poke(s).' % (result.unseen)
    title = 'Update: Poke'
    image = self.IMAGES['poke']

    self.showPopUp(message, title, image)

  def shares_view(self, result):
    message = '%s unseen shares(s).' % (result.unseen)
    title = 'Update: Share'
    image = self.IMAGES['share']

    self.showPopUp(message, title, image)

  def friend_requests_view(self, result):
    message = '%s' % result.user
    title = 'Update: Friend Request'
    image = self.IMAGES['friend']

    if result.picLink is not None:
      fp = urllib.urlopen(result.picLink)
      photo = wx.ImageFromStream(fp,wx.BITMAP_TYPE_JPEG)
      fp.close()

      # write a scaled version of the image onto a blank notification window
      image = self.IMAGES['friendNoIcon'].ConvertToImage().Copy().ConvertToBitmap()
      drawScaledPhoto(image, photo)

    clickHandler = None

    if result.popUpLink is not None:
      clickHandler = lambda x:webbrowser.open_new(result.popUpLink)

    self.showPopUp(message, title, image, clickHandler)

  def group_invite_view(self,result):
    message = '%s' % result.group
    title = 'Update: Group Invite'
    image = self.IMAGES['group']

    if result.picLink is not None:
      fp = urllib.urlopen(result.picLink)
      photo = wx.ImageFromStream(fp,wx.BITMAP_TYPE_JPEG)
      fp.close()

      # write a scaled version of the image onto a blank notification window
      image = self.IMAGES['groupNoIcon'].ConvertToImage().Copy().ConvertToBitmap()
      drawScaledPhoto(image, photo)

    clickHandler = None

    if result.popUpLink is not None:
      clickHandler = lambda x:webbrowser.open_new(result.popUpLink)

    self.showPopUp(message, title, image, clickHandler)

  def event_invite_view(self,result):
    message = '%s' % result.event
    title = 'Update: Event Invite'
    image = self.IMAGES['event']

    if result.picLink is not None:
      fp = urllib.urlopen(result.picLink)
      photo = wx.ImageFromStream(fp,wx.BITMAP_TYPE_JPEG)
      fp.close()

      # write a scaled version of the image onto a blank notification window
      image = self.IMAGES['eventNoIcon'].ConvertToImage().Copy().ConvertToBitmap()
      drawScaledPhoto(image, photo)

    clickHandler = None

    if result.popUpLink is not None:
      clickHandler = lambda x:webbrowser.open_new(result.popUpLink)

    self.showPopUp(message, title, image, clickHandler)

  def showPopUp(self, message, title='', image=None, clickHandler=None):
    fbClickHandler = (
      (callable(clickHandler) and clickHandler) or
      (lambda x: webbrowser.open_new(self.DEFAULT_TOASTERBOX_CLICK_URI)))

    ad = self.adservice.get_next_ad()
    adClickHandler = lambda x: webbrowser.open_new(ad['link'])

    clickHandlerObject = MultiClickHandler(fbClickHandler, adClickHandler)
    clickHandler = clickHandlerObject.clickHandler

    tb = TB.ToasterBox(self, TB.TB_SIMPLE, wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR, TB.TB_ONTIME)

    width = 350
    height = 70

    #Set window location based on user's screen dimensions, minus 5 for best
    a, b, x, y = wx.GetClientDisplayRect()    
    popUpX =  x - width
    popUpY =  y - height - 5

    tb.SetPopupSize((width, height))
    tb.SetPopupPosition((popUpX,popUpY))    

    tb.SetPopupPauseTime(self.options.popUpLinger * 1000)
    tb.SetPopupScrollSpeed(1)
    tb.SetPopupBitmap(image)
    tb.SetPopupText((len(message) > 41 and message[:40]+'...' or message).center(44))
    font = wx.Font(8, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL)
    tb.SetPopupTextColor('#000000')
    tb.SetPopupTextFont(font)
    tb.GetToasterBoxWindow().SetPopupTextFont(font)
    adfont = wx.Font(7, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
    tb.SetAdTextColor('#575758')
    tb.SetAdTextFont(adfont)
    tb.GetToasterBoxWindow().SetAdTextFont(font)

    if ad is not None:
      adtext = "%s: %s" % (ad['title'], ad['description'])
      tb.SetAdText(adtext)
      tb.GetToasterBoxWindow().SetAdText(adtext)
      box = tb.GetToasterBoxWindow().GetAdTextBox()
      clickHandlerObject.box = box
      mouseMotionHandler = MouseMotionEventHandler(box)
      tb.GetToasterBoxWindow().panel.Bind(wx.EVT_MOTION, mouseMotionHandler.onMouseMotion)

    tb.GetToasterBoxWindow().panel.Bind(wx.EVT_LEFT_DOWN, clickHandler)
    tb.Play()
  
  ERRORMSGLIST = {
    2:"Facebook's webservice is currently unavaiable, try again later.",
    4:'Exceeded Facebook Request Rate. A Facebook Limitation, please try again in ten seconds.',
    100: 'Please login.',
    102: 'Please login.',
    'FBQ-E1': 'Connection to Facebook failed.',
    'FBQ-E2': 'Facebook Returned Suppect XML.',
    }
  EXCLUDEERRORREPORT = [2, 4, 100, 102]

  def showError(self, facebookError, showPopup=True):
    errorCode = facebookError.errorCode

    if errorCode == 'FBQ-E1':
      wx.PostEvent(wx.GetApp(), FBQController_FailedServiceCall_Event())

    if errorCode in [102, 100]:
      wx.PostEvent(wx.GetApp(), FBQController_LoginFirst_Event())
    else:
      errorMsg = self.ERRORMSGLIST.get(errorCode, facebookError.errorMsg)
      clickHandler = ((errorCode in self.EXCLUDEERRORREPORT and
        (lambda x: True))
        or (lambda x: webbrowser.open_new(
          urlutil.addQueryParamsToUri(
            self.DEFAULT_ERROR_URI, {'eCode': errorCode, 'eMsg': facebookError.errorMsg} ))))
      if(showPopup):
        self.showPopUp(
          errorMsg,
          'There Was An Error(%s)' % errorCode,
          self.IMAGES['error'],
          clickHandler=clickHandler)
