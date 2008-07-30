import random

defaultAdList = [
]

def selectAd(adlist):
  if adlist and len(adlist) > 0:
    return adlist[random.randint(0, max(0,len(adlist)-1))]
  else:
    return None
