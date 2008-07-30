# --------------------------------------------------------------------------- #
# TOASTERBOX wxPython IMPLEMENTATION
# Ported And Enhanced From wxWidgets Contribution (Aj Bommarito) By:
#
# Andrea Gavana, @ 16 September 2005
# Latest Revision: 06 Nov 2005, 11.30 CET
#
#
# TODO/Caveats List
#
# 1. Any Idea?
#
#
# For All Kind Of Problems, Requests Of Enhancements And Bug Reports, Please
# Write To Me At:
#
# andrea.gavana@agip.it
# andrea_gavan@tin.it
#
# Or, Obviously, To The wxPython Mailing List!!!
#
#
# End Of Comments
# --------------------------------------------------------------------------- #


"""Description:

ToasterBox Is A Cross-Platform Library To Make The Creation Of MSN Style "Toaster"
Popups Easier. The Syntax Is Really Easy Especially If You Are Familiar With The
Syntax Of wxPython.

It Has 2 Main Styles:

- TB_SIMPLE:  Using This Style, You Will Be Able To Specify A Background Image For
              ToasterBox, Text Properties As Text Colour, Font And Label.
             
- TB_COMPLEX: This Style Will Allow You To Put Almost Any Control Inside A
              ToasterBox. You Can Add A Panel In Which You Can Put All The Controls
              You Like.
              
Both Styles Support The Setting Of ToasterBox Position (On Screen Coordinates),
Size, The Time After Which The ToasterBox Is Destroyed (Linger), And The Scroll
Speed Of ToasterBox.

ToasterBox Has Been Tested On The Following Platforms:

Windows (Verified on Windows XP, 2000)


Latest Revision: Andrea Gavana @ 06 Nov 2005, 11.30 CET

"""

import textwrap
import wx

from wx.lib.statbmp import GenStaticBitmap as StaticBitmap

# Define Window List, We Use It Globally
winlist = []

TB_SIMPLE = 1
TB_COMPLEX = 2

DEFAULT_TB_STYLE = wx.SIMPLE_BORDER | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR
TB_CAPTION = DEFAULT_TB_STYLE | wx.CAPTION | wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.FRAME_TOOL_WINDOW 

TB_ONTIME = 1
TB_ONCLICK = 2

# ------------------------------------------------------------------------------ #
# Class ToasterBox
#    Main Class Implementation. It Is Basically A wx.Timer. It Creates And
#    Displays Popups And Handles The "Stacking".
# ------------------------------------------------------------------------------ #

class ToasterBox(wx.Timer):

    def __init__(self, parent, tbstyle=TB_SIMPLE, windowstyle=DEFAULT_TB_STYLE,
                 closingstyle=TB_ONTIME):
        """Deafult Class Constructor.

        ToasterBox.__init__(self, tbstyle=TB_SIMPLE, windowstyle=DEFAULT_TB_STYLE)

        Parameters:
        
        - tbstyle: This Parameter May Have 2 Values:
          (a) TB_SIMPLE: A Simple ToasterBox, With Background Image And Text
              Customization Can Be Created;
          (b) TB_COMPLEX: ToasterBoxes With Different Degree Of Complexity Can
              Be Created. You Can Add As Many Controls As You Want, Provided
              That You Call The AddPanel() Method And Pass To It A Dummy Frame
              And A wx.Panel. See The Demo For Details.

        - windowstyle: This Parameter Influences The Visual Appearance Of ToasterBox:
          (a) DEFAULT_TB_STYLE: Default Style, No Caption Nor Close Box;
          (b) TB_CAPTION: ToasterBox Will Have A Caption, With The Possibility To
              Set A Title For ToasterBox Frame, And A Close Box;

        - closingstyle: Set This Value To TB_ONCLICK If You Want To Be Able To Close
          ToasterBox By A Mouse Click Anywhere In The ToasterBox Frame.
          
        """                         

        self._parent = parent
        self._sleeptime = 10
        self._pausetime = 1700
        self._popuptext = ' '
        self._adtext = ''
        self._popupposition = wx.Point(100,100)
        self._popuptop = wx.Point(0,0)
        self._popupsize = wx.Size(150, 170)

        self._backgroundcolour = wx.WHITE
        self._foregroundcolour = wx.BLACK
        self._adcolor = wx.BLUE
        self._textfont = wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self._adfont = wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self._bitmap = None
         
        self._tbstyle = tbstyle
        self._windowstyle = windowstyle
        self._closingstyle = closingstyle
        
        self._panel = None

        self._bottomright = wx.Point(wx.GetDisplaySize().GetWidth(),
                                     wx.GetDisplaySize().GetHeight())
                                     
        parent.Bind(wx.EVT_ICONIZE, lambda evt: [w.Hide() for w in winlist])

        self._tb = ToasterBoxWindow(self._parent, self, self._tbstyle, self._windowstyle, self._closingstyle)
        

    def SetPopupPosition(self, pos):
        """ Sets The ToasterBox Position On Screen. """

        self._popupposition = pos


    def SetPopupPositionByInt(self, pos):
        """ Sets The ToasterBox Position On Screen, At One Of The Screen Corners. """
        
        self._bottomright = wx.Point(wx.GetDisplaySize().GetWidth(),
                                     wx.GetDisplaySize().GetHeight())

        # top left
        if pos == 0:
            popupposition = wx.Point(0,0)
        # top right
        elif pos == 1:
            popupposition = wx.Point(wx.GetDisplaySize().GetWidth() -
                                     self._popupsize[0], 0)
        # bottom left
        elif pos == 2:
            popupposition = wxPoint(0, wx.GetDisplaySize().GetHeight() -
                                    self._popupsize[1])
        # bottom right
        elif pos == 3:
            popupposition = wx.Point(self._bottomright.x - self._popupsize[0],
                                     self._bottomright.y - self._popupsize[1])

        self._bottomright = wx.Point(popupposition.x + self._popupsize[0],
                                     popupposition.y + self._popupsize[1])


    def SetPopupBackgroundColor(self, colour=wx.WHITE):
        """ Sets The ToasterBox Background Colour. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        self._backgroundcolour = colour


    def SetPopupTextColor(self, colour=wx.BLACK):
        """ Sets The ToasterBox Foreground Colour. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """

        self._foregroundcolour = colour     

    def SetAdTextColor(self, color=wx.BLUE):
        self._adcolor = color

    def SetPopupTextFont(self, font=None):
        """ Sets The ToasterBox Text Font. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """

        self._textfont = font

    def SetAdTextFont(self, font=None):
        self._adfont = font


    def SetPopupSize(self, size):
        """ Sets The ToasterBox Size. """

        self._popupsize = size


    def SetPopupPauseTime(self, pausetime):
        """ Sets The Time After Which The ToasterBox Is Destroyed (Linger). """
        
        self._pausetime = pausetime


    def SetPopupBitmap(self, bitmap=None):
        """ Sets The ToasterBox Background Image. Use It Only For ToasterBoxes
        Created With TB_SIMPLE Style. """
        
        if bitmap is not None:
            """bitmap = wx.Bitmap(bitmap, wx.BITMAP_TYPE_BMP)"""
            bitmap = bitmap
        self._bitmap = bitmap

        if self._bitmap is not None:
            self._tb.SetPopupBitmap(self._bitmap)

    def SetPopupScrollSpeed(self, speed):
        """ Sets The ToasterBox Scroll Speed. The Speed Parameter Is The Pause
        Time (In ms) For Every Step In The ScrollUp() Method."""
        
        self._sleeptime = speed


    def SetPopupText(self, text):
        """ Sets The ToasterBox Text. Use It Only For ToasterBoxes Created With
        TB_SIMPLE Style. """

        self._popuptext = text


    def SetAdText(self, text):
        self._adtext = text


    def AddPanel(self, panel):
        """ Adds A Panel To The ToasterBox. Use It Only For ToasterBoxes Created
        With TB_COMPLEX Style. """

        if not self._tbstyle & TB_COMPLEX:
            raise "\nERROR: Panel Can Not Be Added When Using TB_SIMPLE ToasterBox Style"
            return
        
        self._panel = panel


    def Play(self):
        """ Creates The ToasterBoxWindow, That Does All The Job. """

        # create new window
        self._tb.SetPopupSize((self._popupsize[0], self._popupsize[1]))
        self._tb.SetPopupPosition((self._popupposition[0], self._popupposition[1]))
        self._tb.SetPopupPauseTime(self._pausetime)
        self._tb.SetPopupScrollSpeed(self._sleeptime)

        if self._tbstyle == TB_SIMPLE:
            self._tb.SetPopupTextColor(self._foregroundcolour)
            self._tb.SetPopupBackgroundColor(self._backgroundcolour)
            self._tb.SetAdTextColor(self._adcolor)
            self._tb.SetPopupTextFont(self._textfont)
            self._tb.SetAdTextFont(self._adfont)

            if self._bitmap is not None:
                self._tb.SetPopupBitmap(self._bitmap)

            self._tb.SetPopupText(self._popuptext)  
            self._tb.SetAdText(self._adtext)

        if self._tbstyle == TB_COMPLEX:
            if self._panel is not None:
                self._tb.AddPanel(self._panel)

        # clean up the list
        self.CleanList()

        # check to see if there is already a window displayed
        # by looking at the linked list
        if len(winlist) > 0:
            # there ARE other windows displayed already
            # reclac where it should display
            self.MoveAbove(self._tb)

        # shift new window on to the list
        winlist.append(self._tb)

        if not self._tb.Play():
            # if we didn't show the window properly, remove it from the list
            winlist.remove(winlist[-1])
            # delete the object too
            self._tb.Destroy()
            return


    def MoveAbove(self, tb):
        """ If A ToasterBox Already Exists, Move The New One Above. """
        
        # recalc where to place this popup

        self._tb.SetPopupPosition((self._popupposition[0], self._popupposition[1] -
                                   self._popupsize[1]*len(winlist)))


    def GetToasterBoxWindow(self):
        """ Returns The ToasterBox Frame. """
        
        return self._tb


    def SetTitle(self, title):
        """ Sets The ToasterBox Title If It Was Created With TB_CAPTION Window Style. """
        
        self._tb.SetTitle(title)
        

    def Notify(self):
        """ It's Time To Hide A ToasterBox! """
        
        if len(winlist) == 0:
            return

        # clean the window list
        self.CleanList()

        # figure out how many blanks we have
        try:
            node = winlist[0]
        except:
            return
        
        if not node:
            return

        # move windows to fill in blank space
        for i in xrange(node.GetPosition()[1], self._popupposition[1], 4):
            if i > self._popupposition[1]:
                i = self._popupposition[1]
                
            # loop through all the windows    
            for j in xrange(0, len(winlist)):
                ourNewHeight = i - (j*self._popupsize[1] - 8)
                tmpTb = winlist[j]
                # reset where the object THINKS its supposed to be
                tmpTb.SetPopupPosition((self._popupposition[0], ourNewHeight))
                # actually move it
                tmpTb.SetDimensions(self._popupposition[0], ourNewHeight, tmpTb.GetSize().GetWidth(),
                                    tmpTb.GetSize().GetHeight())

            wx.Usleep(self._sleeptime)


    def CleanList(self):
        """ Clean The Window List. """
        
        if len(winlist) == 0:
            return
        
        node = winlist[0]
        while node:
            if not node.IsShown():
                winlist.remove(node)
                try:
                    node = winlist[0]
                except:
                    node = 0
            else:
                indx = winlist.index(node)
                try:
                    node = winlist[indx+1]
                except:
                    node = 0


# ------------------------------------------------------------------------------ #
# Class ToasterBoxWindow
#    This Class Does All The Job, By Handling Background Images, Text Properties
#    And Panel Adding. Depending On The Style You Choose, ToasterBoxWindow Will
#    Behave Differently In Order To Handle Widgets Inside It.
# ------------------------------------------------------------------------------ #

# panel to hold image and text, repaints itself
class ToasterBoxPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent, -1)
    self.text = ''
    self.adtext = ''
    self.color = wx.BLACK
    self.adcolor = wx.BLUE
    self.font = None
    self.adfont = None
    self.bitmap = None
    self.size = None
    self.Bind(wx.EVT_PAINT, self.OnPaint)

  def OnPaint(self, event):
    dc = wx.PaintDC(self)
    dc.DrawBitmap(self.bitmap, 0, 0)
    self.DrawText(dc)

  def DrawText(self, dc):
      tw, th = self.size

      dc.SetFont(self.font)
      w, h = dc.GetTextExtent(self.text)

      dc.SetTextForeground(self.color)
      dc.DrawText(self.text, 101, th/2 - h +9)

      dc.SetFont(self.adfont)
      aw, ah = dc.GetTextExtent(self.adtext)

      dc.SetTextForeground(self.adcolor)
      dc.DrawText(self.adtext, tw - aw - 1, th - ah - 1)

class ToasterBoxWindow(wx.Frame):

    def __init__(self, parent, parent2, tbstyle, windowstyle, closingstyle):
        """Default Class Constructor.

        Used Internally. Do Not Call Directly This Class In Your Application!
        """

        wx.Frame.__init__(self, parent, wx.ID_ANY, "window", wx.DefaultPosition,
                          wx.DefaultSize, style=windowstyle | wx.CLIP_CHILDREN)

        self._starttime = wx.GetLocalTime()
        self._parent2 = parent2
        self._parent = parent
        self._sleeptime = 10
        self._step = 4
        self._pausetime = 1700
        self._textcolour = wx.BLACK
        self._popuptext = "Change Me!"
        self._adtext = ''
        self._count = 1
        self._tbstyle = tbstyle
        self._windowstyle = windowstyle
        self._closingstyle = closingstyle

        if tbstyle == TB_COMPLEX:
            self.sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self._staticbitmap = None

        if self._windowstyle == TB_CAPTION:
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            self.SetTitle("")

        if self._closingstyle & TB_ONCLICK and self._windowstyle != TB_CAPTION:
            self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
            
        self._bottomright = wx.Point(wx.GetDisplaySize().GetWidth(),
                                     wx.GetDisplaySize().GetHeight())

        # the size we want the dialog to be
        framesize = wx.Size(150, 170)
        self.SetDimensions(self._bottomright.x, self._bottomright.y,
                           framesize.GetWidth(), framesize.GetHeight())

        self.panel = ToasterBoxPanel(self)

    def OnClose(self, event):

        self.NotifyTimer(None)
        event.Skip()


    def OnMouseDown(self, event):

        self.NotifyTimer(None)
        event.Skip()
        

    def SetPopupBitmap(self, bitmap):
        """ Sets The ToasterBox Background Image. Use It Only For ToasterBoxes
        Created With TB_SIMPLE Style. """
        
        bitmap = bitmap.ConvertToImage()
        xsize, ysize = self.GetSize()
        bitmap = bitmap.Scale(xsize, ysize)
        bitmap = bitmap.ConvertToBitmap()

        self.panel.bitmap = bitmap

        #self._staticbitmap = StaticBitmap(self, -1, bitmap, pos=(0,0))
        
        #if self._closingstyle & TB_ONCLICK and self._windowstyle != TB_CAPTION:
        #    self._staticbitmap.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)


    def SetPopupSize(self, size):
        """ Sets The ToasterBox Size. """
        
        self.SetDimensions(self._bottomright.x, self._bottomright.y, size[0], size[1])
        self.panel.size = size


    def SetPopupPosition(self, pos):
        """ Sets The ToasterBox Position On Screen. """
        
        self._bottomright = wx.Point(pos[0] + self.GetSize().GetWidth(),
                                     pos[1] + self.GetSize().GetHeight())
        self._dialogtop = pos


    def SetPopupPositionByInt(self, pos):
        """ Sets The ToasterBox Position On Screen, At One Of The Screen Corners. """
        
        self._bottomright = wx.Point(wx.GetDisplaySize().GetWidth(),
                                     wx.GetDisplaySize().GetHeight())

        # top left
        if pos == 0:
            popupposition = wx.Point(0,0)
        # top right
        elif pos == 1:
            popupposition = wx.Point(wx.GetDisplaySize().GetWidth() -
                                     self._popupsize[0], 0)
        # bottom left
        elif pos == 2:
            popupposition = wx.Point(0, wx.GetDisplaySize().GetHeight() -
                                    self._popupsize[1])
        # bottom right
        elif pos == 3:
            popupposition = wx.Point(self._bottomright.x - self._popupsize[0],
                                     self._bottomright.y - self._popupsize[1])

        self._bottomright = wx.Point(popupposition.x + self._popupsize[0],
                                     popupposition.y + self._popupsize[1])

        self._dialogtop = popupposition
        

    def SetPopupPauseTime(self, pausetime):
        """ Sets The Time After Which The ToasterBox Is Destroyed (Linger). """
        
        self._pausetime = pausetime


    def SetPopupScrollSpeed(self, speed):
        """ Sets The ToasterBox Scroll Speed. The Speed Parameter Is The Pause Time (In ms) For Every Step In The ScrollUp() Method."""
        
        self._sleeptime = speed


    def AddPanel(self, panel):
        """ Adds A Panel To The ToasterBox. Use It Only For ToasterBoxes Created With TB_COMPLEX Style. """

        if not self._tbstyle & TB_COMPLEX:
            raise "\nERROR: Panel Can Not Be Added When Using TB_SIMPLE ToasterBox Style"
            return
        
        self.sizer.Add(panel, 1, wx.EXPAND)
        self.sizer.Layout()
        self.SetSizer(self.sizer)

        if self._closingstyle & TB_ONCLICK and self._windowstyle != TB_CAPTION:
            panel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)        


    def SetPopupText(self, text):
        """ Sets The ToasterBox Text. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        
        self._popuptext = text 
        self.panel.text = text

    def SetAdText(self, text):
        self._adtext = text 
        self.panel.adtext = text

    def GetAdTextBox(self):
        if self.panel is not None:
            dc = wx.ClientDC(self.panel)
        else:
            dc = wx.ClientDC(self)
        dc.SetFont(self._adfont)

        tw, th = self._parent2._popupsize
        w, h = dc.GetTextExtent(self._adtext)

        # with one pixel margin
        return (tw - w - 1, th - h - 1, w + 1, h + 1)


    def SetPopupTextFont(self, font):
        """ Sets The ToasterBox Text Font. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        
        self._textfont = font
        self.panel.font = font

    def SetAdTextFont(self, font):
        self._adfont = font
        self.panel.adfont = font
        

    def GetPopupText(self):
        """ Returns The ToasterBox Text. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        
        return self._popuptext
    

    def GetAdText(self):
        """ Returns The ToasterBox Ad Text. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        
        return self._adtext
    

    def Play(self):
        """ Creates The ToasterBoxWindow, That Does All The Job. """
        
        # do some checks to make sure this window is valid
        if self._bottomright.x < 1 or self._bottomright.y < 1:
            return False
        
        if self.GetSize().GetWidth() < 50 or self.GetSize().GetWidth() < 50:
            # toasterbox launches into a endless loop for some reason
            # when you try to make the window too small.
            return False

        self.ScrollUp()
        timerid = wx.NewId()
        self.showtime = wx.Timer(self, timerid)
        self.showtime.Start(self._pausetime)
        self.Bind(wx.EVT_TIMER, self.NotifyTimer, id=timerid)

        return True


    def NotifyTimer(self, event):
        """ Hides Gradually The ToasterBoxWindow. """
        
        self.showtime.Stop()
        del self.showtime
        self.ScrollDown()
        

    def SetPopupBackgroundColor(self, colour):
        """ Sets The ToasterBox Background Colour. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        
        self.SetBackgroundColour(colour)


    def SetPopupTextColor(self, colour):
        """ Sets The ToasterBox Foreground Colour. Use It Only For ToasterBoxes Created With TB_SIMPLE Style. """
        
        self._textcolour = colour
        self.panel.color = colour

    def SetAdTextColor(self, color):
        self._adcolor = color
        self.panel.adcolor = color

    def ScrollUp(self):
        """ Scrolls The ToasterBox Up, Which Means Gradually Showing The ToasterBox. """
        
        self.Show(True)

        # walk the Y value up in a raise motion
        xpos = self.GetPosition().x
        ypos = self._bottomright[1]
        windowsize = 0
        
        for i in xrange(ypos, self._dialogtop[1], -self._step):
            if i < self._dialogtop[1]:
              i = self._dialogtop[1]
              
            windowsize = windowsize + self._step
            self.SetDimensions(self._dialogtop[0], i, self.GetSize().GetWidth(),
                               windowsize)

            if self._tbstyle == TB_SIMPLE:
                self.DrawText()
                
            wx.Usleep(self._sleeptime)
            self.Update()
            self.Refresh()

        self.Update()

        if self._tbstyle == TB_SIMPLE:
            self.DrawText()

        self.SetFocus()

        
    def ScrollDown(self):
        """ Scrolls The ToasterBox Down, Which Means Gradually Hiding The ToasterBox. """
        
        # walk down the Y value
        windowsize = self.GetSize().GetHeight()
        
        for i in xrange(self._dialogtop[1], self._bottomright.y, self._step):
            if i > self._bottomright.y:
                i = self._bottomright.y
                
            windowsize = windowsize - self._step
            self.SetDimensions(self._dialogtop[0], i, self.GetSize().GetWidth(),
                               windowsize)    
            wx.Usleep(self._sleeptime)
            self.Refresh()

        self.Hide()
        if self._parent2:
            self._parent2.Notify()


    def DrawText(self):
        if self._staticbitmap is not None:
            dc = wx.ClientDC(self._staticbitmap)
        else:
            dc = wx.ClientDC(self)

        tw, th = self._parent2._popupsize

        dc.SetFont(self._textfont)
        w, h = dc.GetTextExtent(self._popuptext)

        dc.SetTextForeground(self._textcolour)
        dc.DrawText(self._popuptext, 101, th/2 - h + 9)

        dc.SetFont(self._adfont)
        aw, ah = dc.GetTextExtent(self._adtext)

        dc.SetTextForeground(self._adcolor)
        dc.DrawText(self._adtext, tw - aw - 1, th - ah - 1)

