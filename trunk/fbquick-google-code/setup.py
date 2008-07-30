from distutils.core import setup
import py2exe

setup(windows=[
        {
         'script': 'fbquick.py',
          'icon_resources': [(1, 'fbquickIcon.ico')]
        }]
    )

