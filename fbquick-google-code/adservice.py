
import feedparser
import datetime
import urlutil
import urllib
import urllib2

import  wx
import  wx.lib.newevent

import defaultads

from worker import *

AdImpressionEvent, EVT_AD_IMPRESSION = wx.lib.newevent.NewEvent()
AdDoUpdateEvent, EVT_AD_DOUPDATE = wx.lib.newevent.NewEvent()
AdDemographicsEvent, EVT_AD_DEMOGRAPHICS = wx.lib.newevent.NewEvent()

def print_err(e):
  print e

class AdService(wx.EvtHandler):
  API_VER_USER_AGENT = 'AdServ/0.2'

  def __init__(self, feedUri, locUri, appName='Unknown'):
    wx.EvtHandler.__init__(self)
    self.demographics = {}

    self._adList = []

    self.locUri = locUri
    self.feedUri = feedUri
    self.appName = appName

    self.lat = None
    self.lng = None

    self.worker = WorkerThread(self.update_ads_worker, self.update_ads_accumulator, print_err)
    self.worker.start()

    self.impression_worker = WorkerThread(self.signal_server_worker, None, print_err)
    self.impression_worker.start()

    self.Bind(EVT_AD_DOUPDATE, self.update_ads)
    self.Bind(EVT_AD_IMPRESSION, self._signal_server)
    self.Bind(EVT_AD_DEMOGRAPHICS, self._user_demographics)


  def update_ads(self, evt=None):
    print "adding update ads work"
    self.worker.addWork([
      self.feedUri, self.locUri, self.demographics, self.lat, self.lng])

  def update_ads_worker(self, input):
    print "updating ads"
    feedUrl, locUri, demographics, lat, lng = input
    if lat and lng:
      feedUrl = urlutil.addQueryParamsToUri(
          feedUrl, {'lat' : lat, 'lng' : lng } )
    elif demographics and demographics.has_key('affiliations'):
      # use demographics to find the lat & lng
      # and set the lat and lng
      for affiliation in demographics['affiliations']:
        try:
          nid, name, type = affiliation
          tmp_uri = urlutil.addQueryParamsToUri(locUri,
            { 'nid': nid, 'name': name, 'type': type })
          resp = urllib2.urlopen(tmp_uri)
          body = resp.read()
          lat, lng = body.split(',')
          feedUrl = urlutil.addQueryParamsToUri(
            feedUrl, {'lat' : lat, 'lng' : lng } )
          break
        except Exception, e:
          # urlopen throws exception on 404, or any problems
          print e

    d = feedparser.parse(feedUrl)
    return [d.entries[:], lat, lng]

  def update_ads_accumulator(self, output):
    print "saving ads results"
    entries, lat, lng = output
    self._adList = entries
    self.lat = lat
    self.lng = lng

  def get_next_ad(self):
    if len(self._adList) > 0:
      entry = self._adList.pop()
      self._adList.insert(0,entry)
      evt = AdImpressionEvent(entry=entry, demographics=self.demographics)
      wx.PostEvent(self, evt)
      adlink = entry.get('link', '')
      if hasattr(self,'demographics') and hasattr(self.demographics,'location'):
        # We have the demographics, so pop it into the
        # current query, if it exists.
        adlink = urlutil.addQueryParamsToUri(
            adlink, {'o' : self.demographics.location } )
      desc = None
      for cont in entry.get('content', []):
        desc = cont.get('value', None)
        if desc:
          break
      if desc is None:
        desc = entry.get('summary', '')
      return {
        'title': entry.get('title', ''),
        'description': desc,
        'link': adlink
        }
    else:
      return defaultads.selectAd(defaultads.defaultAdList)

  def _signal_server(self, evt):
    self.impression_worker.addWork(evt)

  def signal_server_worker(self, evt):
    """ This method contacts the central server about impression
    """
    try:
      assert hasattr(evt,'entry')
      assert hasattr(evt,'demographics')
      hit_url = ''
      # Find the URI to which we POST a 'hit'
      for link in evt.entry.links:
        if(link.get('rel','') == 'adserv_impression'
          and link.get('href','') != ''):
          hit_url = link.get('href','')
          break
      if len(hit_url) <= 0:
        return
      postdata = urllib.urlencode({
        'uidhash': evt.demographics.get('uidHash',''),
        'birthday': evt.demographics.get('birthday', ''),
        'sex': evt.demographics.get('sex',''),
        'location': evt.demographics.get('location', ''),
        'affiliations': str(evt.demographics.get('affiliations', ''))
        })
      request = urllib2.Request(
        hit_url,
        data=postdata
        )
      request.add_header(
        'User-Agent', "%s (%s)" % (AdService.API_VER_USER_AGENT, self.appName))
      urllib2.urlopen(request)
    except Exception, e:
      print "AdService Signal Service: %s" % e

  def _user_demographics(self, evt):
    assert hasattr(evt, 'demographics')
    self.demographics = evt.demographics
    self.update_ads()

def main():
  adService = AdService('http://floppybit.com/fbe/items/')
  adService.update_ads()
  ad = adService.get_next_ad()
  print ad['title'], ad['summary'], ad['link']
  ad = adService.get_next_ad()
  print ad['title'], ad['summary'], ad['link']

if __name__ == '__main__':
  main()

