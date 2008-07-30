from xml.dom import minidom
import urllib, urllib2, urlparse, time, md5, sha, re
import base64
import wx
import wx.lib.newevent
import shelve
import os.path
from xml.etree import ElementTree
from xml.sax import saxutils

HaveFacebookSessionEvent, EVT_HAVE_FB_SESSION = wx.lib.newevent.NewEvent()


NOTES_MESSAGES = 1
NOTES_WALL_COUNT = 2
NOTES_POKES = 3
NOTES_FRIEND_REQUESTS = 4
NOTES_PHOTO_TAGS = 5
NOTES_GROUP_INVITES = 6
NOTES_EVENT_INVITES = 7
NOTES_SHARES = 8
NOTES_USER_DEMO = 9


NOTES_TO_METHOD = {
  NOTES_MESSAGES: 'notifications_get',
  NOTES_WALL_COUNT: 'wall_getCount',
  NOTES_POKES: 'notifications_get',
  NOTES_FRIEND_REQUESTS: 'notifications_get',
  NOTES_PHOTO_TAGS: 'photos_getOfUser',
  NOTES_GROUP_INVITES: 'notifications_get',
  NOTES_EVENT_INVITES: 'notifications_get',
  NOTES_SHARES: 'notifications_get',
  NOTES_USER_DEMO: 'demographics'
}

# Pre declared mapping
RESULTS_TO_NOTES = {}

class FacebookError(Exception):
  def __init__(self, errorCode, errorMsg):
    self.errorCode = errorCode
    self.errorMsg  = errorMsg


class FbResult(dict):

  def __getattr__(self, item):
    try:
      return self.__getitem__(item)
    except KeyError:
      raise AttributeError(item)

  def __setattr__(self, item, value):
    if self.has_key(item):
      return self.__setitem__(item, value)
    else:
      raise AttributeError(item)

  def has_changed(self):
    return False

  def has_unread(self):
    return False

  def message(self):
    return ''

  def __eq__(self,other):
    scopy = self.copy()
    if isinstance(other,FbResult):
      ocopy = other.copy()
      if scopy.has_key('changed'):
        scopy.pop('changed')
      if ocopy.has_key('changed'):
        ocopy.pop('changed')
      return scopy == ocopy
    else:
      return scopy == other

  def __ne__(self,other):
    return self.__eq__(other) == False

RESULTS_TO_NOTES[FbResult] = None


class MessagesResult(FbResult):
  def __init__(self, unseen=None, recent=0, changed=False, popup_link=None):
    FbResult.__init__(self)
    self.__setitem__('unseenMessages', unseen)
    self.__setitem__('messageChanged', changed)
    self.__setitem__('messageRecent', recent)
    self.__setitem__('popUpLink', popup_link)

  def has_changed(self):
    return self.messageChanged

  def has_unread(self):
    return self.unseenMessages > 0

RESULTS_TO_NOTES[MessagesResult] = NOTES_MESSAGES


class PokesResult(FbResult):
  def __init__(self, unseen=0, changed=None, recent=0):
    FbResult.__init__(self)
    self.__setitem__('unseen', unseen)
    self.__setitem__('changed', changed)
    self.__setitem__('recent',recent)
 
  def has_changed(self):
    return self.changed

  def has_unread(self):
    return self.unseen > 0

RESULTS_TO_NOTES[PokesResult] = NOTES_POKES


class SharesResult(FbResult):
  def __init__(self, unseen=0, changed=None, recent=0):
    FbResult.__init__(self)
    self.__setitem__('unseen', unseen)
    self.__setitem__('changed', changed)
    self.__setitem__('recent',recent)
 
  def has_changed(self):
    return self.changed

  def has_unread(self):
    return self.unseen > 0

RESULTS_TO_NOTES[SharesResult] = NOTES_SHARES


class FriendRequestsResult(FbResult):
  def __init__(self, change=None, user=None, pic=None, popup_link=None):
    FbResult.__init__(self)
    self.__setitem__('changed', change)
    self.__setitem__('user', user)
    self.__setitem__('picLink',pic)
    self.__setitem__('popUpLink', popup_link)

  def has_changed(self):
    return self.changed
  
  def has_unread(self):
    return True

RESULTS_TO_NOTES[FriendRequestsResult] = NOTES_FRIEND_REQUESTS


class GroupInviteResult(FbResult):
  def __init__(self, change=None, group=None, pic=None, popup_link=None):
    FbResult.__init__(self)
    self.__setitem__('changed', change)
    self.__setitem__('group', group)
    self.__setitem__('picLink',pic)
    self.__setitem__('popUpLink', popup_link)

  def has_changed(self):
    return self.changed
  
  def has_unread(self):
    return True

RESULTS_TO_NOTES[GroupInviteResult] = NOTES_GROUP_INVITES


class EventInviteResult(FbResult):
  def __init__(self, change=None, event=None, pic=None, popup_link=None):
    FbResult.__init__(self)
    self.__setitem__('changed', change)
    self.__setitem__('event', event)
    self.__setitem__('picLink',pic)
    self.__setitem__('popUpLink', popup_link)

  def has_changed(self):
    return self.changed
  
  def has_unread(self):
    return True

RESULTS_TO_NOTES[EventInviteResult] = NOTES_EVENT_INVITES

class PhotoTagsResult(FbResult):
  def __init__(self, tag_count=0, tag_change=None, pic_link=None, popup_link=None):
    FbResult.__init__(self)
    self.__setitem__('photoTagCount', tag_count)
    self.__setitem__('photoTagChange', tag_change)
    self.__setitem__('picLink', pic_link)
    self.__setitem__('popUpLink', popup_link)
    self.__setitem__('changed', tag_change is not None and tag_change != 0)

  def has_changed(self):
    return self.changed

RESULTS_TO_NOTES[PhotoTagsResult] = NOTES_PHOTO_TAGS


class WallResult(FbResult):
  def __init__(self, count=0, change=None, popup_link=None):
    FbResult.__init__(self)
    self.__setitem__('wallCount', count)
    self.__setitem__('wallChange', change)
    self.__setitem__('popUpLink', popup_link)
    self.__setitem__('changed', change is not None and change != 0)

  def has_changed(self):
    return self.changed

RESULTS_TO_NOTES[WallResult] = NOTES_WALL_COUNT


class DemographicsResult(FbResult):
  def __init__(self, changed=False, uidHash=None, birthday=None, sex=None, affiliations=None, location=''):
    FbResult.__init__(self)
    self.__setitem__('changed', changed)
    self.__setitem__('uidHash', uidHash)
    self.__setitem__('birthday', birthday)
    self.__setitem__('sex', sex)
    self.__setitem__('affiliations', affiliations)
    if len(location.replace(',  0 ','')) > 0:
      self.__setitem__('location', location)

  def has_changed(self):
    return self.changed

RESULTS_TO_NOTES[DemographicsResult] = NOTES_USER_DEMO



def insertFbNS(s):
  return re.sub('{}','{http://api.facebook.com/1.0/}',s,0)



class FacebookService:
  FACEBOOK_NS = 'http://api.facebook.com/1.0/'
  LOGIN_URI = 'http://api.facebook.com/login.php?v=1.0&api_key=%s&auth_token=%s'
  PROFILE_URI = 'http://www.facebook.com/profile.php?uid=%s&api_key=%s'
  MAILBOX_URI = 'http://www.facebook.com/mailbox.php'
  CONF_REQ_URI = 'http://www.facebook.com/reqs.php'

  def __init__(self, apiKey, secret, shelfdir=None):
    self.apiKey = apiKey
    self.secret = secret
    self.shelfdir = shelfdir

    #Session Variables
    self.sessionKey = ''
    self.authToken = ''
    self.sessionSecret = ''
    self.__uid = ' ' 
    #Wall variables
    self.wallCount = None
    #Messages
    self.messagesUnread = None
    self.messagesRecent = 0
    #Pokes
    self.pokesUnread = None
    self.pokesRecent = 0
    #Shares
    self.sharesUnread = None
    self.sharesRecent = 0
    #PhotoTags
    self.photoTagTotal = None
    #Friends
    self.friendRequests = []
    #Groups
    self.groupInvites = []
    #Events
    self.eventInvites = []
    #User info
    self.sentDemos = False
    self.userPic = ''
    self.userName = ''
    self.userAffiliationNames = []
    self.userAffiliationKeys = []

  def _get_loginUrl(self):
    url = self.LOGIN_URI % (self.apiKey, self.authToken)
    return url
  loginUrl = property(_get_loginUrl)

  def errorCheck(self, xml):

    try:
      et = ElementTree.ElementTree(ElementTree.XML(xml))
    except Exception, e:
      raise FacebookError('FBQ-E2','error:%s xml:%s' % (e, base64.encodestring(xml) ))

    if et.getroot().tag == insertFbNS('{}error_response'):
      errorCode = int(et.findtext(insertFbNS('{}error_code')))
      if errorCode == 1:
        return True
      errorMsg = et.findtext(insertFbNS('{}error_msg')) 
      raise FacebookError(errorCode, errorMsg)
    elif et.getroot().tag == 'fbQuick_error':
      raise FacebookError('FBQ-E1', et.getroot().text)
    return False

  def generateSig(self, params, secretnum):
    keys = params.keys()
    keys.sort()
    m = md5.new()
  
    for key in keys:
      if key!='sig':
        m.update(key+'='+params[key])
  
    m.update(secretnum)
  
    return m.hexdigest()

  def postRequest(self, method, params, resubmit=0):
    params['method'] = method
    params['session_key'] = str(self.sessionKey)
    params['api_key'] = self.apiKey
    params['call_id'] = (str(time.time())+'0').replace('.','')[:12]
    
    print "Call ID: " + params['call_id']
  
    if (method == 'facebook.auth.getSession'):
      params['auth_token'] = str(self.authToken)  
  
    if(method != 'facebook.auth.getSession' and method!='facebook.auth.createToken'):
      secreT = str(self.sessionSecret)
    else:
      secreT = self.secret
    
    params['sig'] = self.generateSig(params, secreT)

    data = urllib.urlencode(params)
  
    # No-timeout so https url calls do not return immediately with
    # a read error, reset when done. This is a WORKAROUND.
    import socket
    oldTimeout = socket.getdefaulttimeout()

    url = 'http://api.facebook.com/restserver.php'
    if (method == 'facebook.auth.getSession'):
      url = 'https://api.facebook.com/restserver.php'
      socket.setdefaulttimeout(None)

    try:
      f = urllib2.urlopen(url, data)
      xml = f.read()
    except Exception, e:
      xml = '<fbQuick_error>%s</fbQuick_error>' % (saxutils.escape(str(e)),)
    socket.setdefaulttimeout(oldTimeout)
    
    if self.errorCheck(xml) and resubmit < 2:
      return self.postRequest(method, params, resubmit+1)
    elif resubmit >= 2:
      raise FacebookError("4", "Facebook is busy, try again in a few seconds")
  
    return xml 

  def callFacebookMethod(self, method, params={}):
    if(self.sessionKey=='' and method!='facebook.auth.createToken' and method!='facebook.auth.getSession'):
      self.auth_getSession()
      if params.has_key("id"):
        params['id']=self.__uid
    
    if not params.has_key('uids') and method!='facebook.users.getLoggedInUser':
      params['uids']=self.__uid

    params['v'] = '1.0'

    xml = self.postRequest(method, params)
    return xml

  def auth_createToken(self):
    self.sessionKey = ''
    xml = self.callFacebookMethod('facebook.auth.createToken')
    et = ElementTree.ElementTree(ElementTree.XML(xml))

    self.authToken = et.findtext('/')

  def auth_getSession(self):
    xml = self.callFacebookMethod('facebook.auth.getSession')
    et = ElementTree.ElementTree(ElementTree.XML(xml))

    self.__uid = et.findtext(insertFbNS('{}uid'))
    self.uidHash = sha.new(self.__uid).hexdigest()
    self.sessionSecret = et.findtext(insertFbNS('{}secret'))
    self.sessionKey = et.findtext(insertFbNS('{}session_key'))
    expires = int(et.findtext(insertFbNS('{}expires')))

    if expires == 0:
      db = shelve.open(self.shelfdir and os.path.join(self.shelfdir,'session') or 'session')
      db['sessionKey'] = self.sessionKey
      db['sessionSecret'] = self.sessionSecret
      db.close()
      db = None

    if hasattr(self, 'sessionEvtHandler'):
      wx.PostEvent(self.sessionEvtHandler, HaveFacebookSessionEvent())

  def notifications_get(self):
    xml = self.callFacebookMethod('facebook.notifications.get')
    et = ElementTree.ElementTree(ElementTree.XML(xml))

    notifications = []

    # messages
    messagesUnread = int(et.findtext(insertFbNS('{}messages/{}unread'),0))
    messagesRecent = int(et.findtext(insertFbNS('{}messages/{}most_recent'),0))

    changed = messagesUnread > 0 and messagesRecent > self.messagesRecent
    notifications.append(MessagesResult(unseen=messagesUnread, recent=messagesRecent, changed=changed, popup_link=self.MAILBOX_URI))

    self.messagesUnread = messagesUnread
    self.messagesRecent = messagesRecent

    # pokes
    pokesUnread = int(et.findtext(insertFbNS('{}pokes/{}unread'),0))
    pokesRecent = int(et.findtext(insertFbNS('{}pokes/{}most_recent'),0))

    changed = pokesUnread > 0 and pokesRecent > self.pokesRecent
    notifications.append(PokesResult(unseen=pokesUnread, recent=pokesRecent, changed=changed))

    self.pokesUnread = pokesUnread
    self.pokesRecent = pokesRecent

    # shares
    sharesUnread = int(et.findtext(insertFbNS('{}shares/{}unread'),0))
    sharesRecent = int(et.findtext(insertFbNS('{}shares/{}most_recent'),0))

    changed = sharesUnread > 0 and sharesRecent > self.sharesRecent
    notifications.append(SharesResult(unseen=sharesUnread, recent=sharesRecent, changed=changed))

    self.sharesUnread = sharesUnread
    self.sharesRecent = sharesRecent

    # friends
    friends = et.findall(insertFbNS('{}friend_requests/{}uid'))
    fids = [ x.text for x in friends ]
    users = []

    if len(friends) > 0:
      xmlf = self.user_getInfo(ids=fids, fields=['first_name','last_name','pic'])
      etf = ElementTree.ElementTree(ElementTree.XML(xmlf))
      users = [(i.text,' '.join([f.text,l.text]),p.text) for i,f,l,p in zip(etf.findall(insertFbNS('{}user/{}uid')),etf.findall(insertFbNS('{}user/{}first_name')),etf.findall(insertFbNS('{}user/{}last_name')),etf.findall(insertFbNS('{}user/{}pic')))]

    for fid,user,pic in users:
      notifications.append(FriendRequestsResult(fid not in self.friendRequests,user,pic,self.CONF_REQ_URI))

    self.friendRequests = fids

    # group invites
    invites = et.findall(insertFbNS('{}group_invites/{}gid'))
    gids = [ x.text for x in invites ]
    groups = []

    if len(invites) > 0:
      xmlg = self.groups_get(ids=gids)
      etg = ElementTree.ElementTree(ElementTree.XML(xmlg))
      groups = [(i.text,n.text,p.text) for i,n,p in zip(etg.findall(insertFbNS('{}group/{}gid')),etg.findall(insertFbNS('{}group/{}name')),etg.findall(insertFbNS('{}group/{}pic')))]

    for gid,group,pic in groups:
      notifications.append(GroupInviteResult(gid not in self.groupInvites,group,pic))

    self.groupInvites = gids

    # event invites
    invites = et.findall(insertFbNS('{}event_invites/{}eid'))
    eids = [ x.text for x in invites ]
    events = []

    if len(invites) > 0:
      xmle = self.events_get(ids=eids)
      ete = ElementTree.ElementTree(ElementTree.XML(xmle))
      events = [(i.text,n.text,p.text) for i,n,p in zip(ete.findall(insertFbNS('{}event/{}eid')),ete.findall(insertFbNS('{}event/{}name')),ete.findall(insertFbNS('{}event/{}pic')))]

    for eid,event,pic in events:
      notifications.append(EventInviteResult(eid not in self.eventInvites,event,pic))

    self.eventInvites = eids

    return notifications


  def wall_getCount(self):
    xml = self.user_getInfo(fields=['wall_count'])
    et = ElementTree.ElementTree(ElementTree.XML(xml))

    count = int(et.findtext(insertFbNS('{}user/{}wall_count')))

    if self.wallCount is None:
      self.wallCount = count
      return WallResult(self.wallCount, None)

    difference = int(count) - int(self.wallCount)

    self.wallCount = count

    return WallResult(self.wallCount, difference, self.PROFILE_URI % (self.__uid,self.apiKey))

  def photos_getOfUser(self):
    xml = self.callFacebookMethod('facebook.photos.get',{'subj_id':self.__uid}) 
    et = ElementTree.ElementTree(ElementTree.XML(xml))

    photos = et.findall(insertFbNS('{}photo'))

    count = len(photos)

    picLink   = None
    popUpLink = None
   
    if self.photoTagTotal is None:
      self.photoTagTotal = count
      return PhotoTagsResult(self.photoTagTotal, None, picLink, None)
    
    difference = count - int(self.photoTagTotal)
    
    if difference != 0 and count > 0:
      picLink = photos[0].findtext(insertFbNS('{}src'))
      popUpLink = photos[0].findtext(insertFbNS('{}link'))

    self.photoTagTotal = count

    return PhotoTagsResult(count, difference, picLink, popUpLink)

  def demographics(self):
    if self.sentDemos == False:
      xml = self.user_getInfo(fields=['affiliations','birthday', 'sex', 'current_location'])
      et = ElementTree.ElementTree(ElementTree.XML(xml))

      birthday = et.findtext(insertFbNS('{}user/{}birthday'))
      sex = et.findtext(insertFbNS('{}user/{}sex'))
      location = '%s, %s %s %s' % ( et.findtext(insertFbNS('{}user/{}current_location/{}city')), et.findtext(insertFbNS('{}user/{}current_location/{}state')), et.findtext(insertFbNS('{}user/{}current_location/{}zip')), et.findtext(insertFbNS('{}user/{}current_location/{}country')) )

      nodes = et.findall(insertFbNS('{}user/{}affiliations/{}affiliation'))

      nid = insertFbNS('{}nid')
      name = insertFbNS('{}name')
      type = insertFbNS('{}type')

      affiliations = [(x.findtext(nid),x.findtext(name),x.findtext(type)) for x in nodes]

      self.sentDemos = True

      return DemographicsResult(self.sentDemos,self.uidHash,birthday,sex,affiliations,location)

    return DemographicsResult()

  def groups_get(self, ids=[]):
    idstr = ','.join(ids)
    return self.callFacebookMethod('facebook.groups.get', {'gids':idstr})

  def events_get(self, ids=[]):
    idstr = ','.join(ids)
    return self.callFacebookMethod('facebook.events.get', {'eids':idstr})

  def users_getLoggedInUser(self):
    xml = self.callFacebookMethod('facebook.users.getLoggedInUser')
    et = ElementTree.ElementTree(ElementTree.XML(xml))
    self.__uid = et.getroot().text
    self.uidHash = sha.new(self.__uid).hexdigest()
    if hasattr(self, 'sessionEvtHandler'):
      wx.PostEvent(self.sessionEvtHandler, HaveFacebookSessionEvent())

  def user_getInfo(self, ids=[], fields=[]):
    fieldstr = ','.join(fields)

    if len(ids)!=0:
      idstr = ','.join(ids)
      return self.callFacebookMethod('facebook.users.getInfo', {'uids':idstr,'fields':fieldstr})        

    return self.callFacebookMethod('facebook.users.getInfo',{'fields':fieldstr})

