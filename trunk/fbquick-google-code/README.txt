This is fbquick, a desktop Facebook notification applet. This program allows you to receive Facebook notifications on your desktop even when your browser is closed. Currently fbquick runs on Microsoft Windows but as the code uses the wxWidgets library for drawing windows, it should be fairly trivial to run it on any operating system supported by wxWidgets. 

USAGE

If Python, simplejson, and wxwidgets for Python are installed, just run fbquick.py. Your browser will open and direct you to log in to Facebook. Once you've logged in once, your session will be saved and you will not have to log in again.

BUILDING

If you want a compiled EXE of fbquick, install py2exe, and from a command line run "python setup.py py2exe". This will place an EXE file in a new directory called "dist". We still need to automate certain parts of the packaging process, such as placing all the images and libraries in the same directory as the EXE. This will be taken care of soon.