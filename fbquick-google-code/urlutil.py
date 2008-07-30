
import urlparse
import urllib

def addQueryParamsToUri(baseUri, params):
  splitUrl = [x for x in urlparse.urlsplit(baseUri)]
  oldQuery = splitUrl[3]
  newQuery = ((oldQuery[-1:] not in ['','&'] and '&') or '').join([
    oldQuery,
    urllib.urlencode(params)])
  splitUrl[3] = newQuery
  return urlparse.urlunsplit(splitUrl)

