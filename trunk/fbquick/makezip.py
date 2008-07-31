# make the zip file for autoupdate downloads
import glob
import os
import os.path
import zipfile

if __name__ == '__main__':

  b = 'fbquick'
  
  z = zipfile.ZipFile(b + '.zip','w',zipfile.ZIP_DEFLATED)

  p = os.path.join('dist')

  for f in os.listdir(p):
    z.write(os.path.join(p,f),os.path.join(b,f))

  p = 'fbquick'

  for f in glob.glob(os.path.join('*.ico')):
    h, t = os.path.split(f)
    z.write(f,os.path.join(b,t))

  for f in glob.glob(os.path.join('*.jpg')):
    h, t = os.path.split(f)
    z.write(f,os.path.join(b,t))

  z.write(os.path.join('settings.xml'),os.path.join(b,'settings.xml'))
  z.write(os.path.join('ToasterBox.py'),os.path.join(b,'ToasterBox.py'))
  z.write(os.path.join('README.txt'),os.path.join(b,'README.txt'))
  z.write(os.path.join('gpl.txt'),os.path.join(b,'gpl.txt'))
  
  p = os.path.join('\\','Python25','lib','site-packages','wx-2.8-msw-unicode','wx')
  z.write(os.path.join(p,'MSVCP71.dll'),os.path.join(b,'MSVCP71.dll'))
  z.write(os.path.join(p,'gdiplus.dll'),os.path.join(b,'gdiplus.dll'))

  z.close()
