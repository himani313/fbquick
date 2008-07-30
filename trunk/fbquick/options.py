import wx
import wx.lib.hyperlink as hyperlink
from wx.lib.stattext import GenStaticText as StaticText
from wx.lib.buttons import GenBitmapButton as BitmapButton
import webbrowser
from xml.dom import minidom

class OptionsVaribles(dict):

  def __init__(self):
    self['messageCheck'] = True
    self['wallCheck'] = True
    self['pokeCheck'] = True
    self['startConnected'] = True
    self['friendCheck'] = True
    self['shareCheck'] = True
    self['groupCheck'] = True
    self['eventCheck'] = True
    self['interval'] = 1
    self['popUpLinger'] = 10

  def __getattr__(self, item):
    try:
      return self.__getitem__(item)
    except KeyError:
      raise AttributeError(item)

def booleanText(boolean):
  if boolean:
    return '1'
  else:
    return '0'

class OptionsPersistence:
  
  def SettingValueCheck(self, str):
    return str in [ '0', '1' ]
  
  def IntervalCheck(self, str):
    return str in ['1', '5', '10', '15']
  
  def PopUpLingerCheck(self, str):
    return str in ['5', '10', '15', '30', '45', '60']
    
  def load(self, filename):
    options = OptionsVaribles()
 
    try:
      dom = minidom.parse(filename)
      temp = dom.getElementsByTagName("messages")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.messageCheck = temp == '1'
      
      temp = dom.getElementsByTagName("wall")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.wallCheck  = temp == '1'
      
      temp = dom.getElementsByTagName("pokes")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.pokeCheck  = temp == '1'
      
      temp = dom.getElementsByTagName("phototag")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.photoTagCheck  = temp == '1'
          
      temp = dom.getElementsByTagName("friendCheck")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.friendCheck = temp == '1'
          
      temp = dom.getElementsByTagName("shareCheck")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.shareCheck = temp == '1'

      temp = dom.getElementsByTagName("groupCheck")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.groupCheck = temp == '1'

      temp = dom.getElementsByTagName("eventCheck")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.eventCheck = temp == '1'

      temp = dom.getElementsByTagName("startConnected")[0].firstChild.data
      if(self.SettingValueCheck(temp)):
          options.startConnected  = temp == '1'

      intervalTemp = dom.getElementsByTagName("updateInterval")[0].firstChild.data
      if(self.IntervalCheck(intervalTemp)):
        options.interval = int(intervalTemp)
      
      popUpLingerTemp = dom.getElementsByTagName("popUpLinger")[0].firstChild.data
      if(self.PopUpLingerCheck(popUpLingerTemp)):
        options.popUpLinger = int(popUpLingerTemp)
      
      return options 
    
    except:
      return options
  
  
  def save(self, options, filename):
    doc = minidom.Document()
    settings = doc.createElementNS("", "settings")
    
    #Messages
    element = doc.createElement("messages")
    text = doc.createTextNode(booleanText(options.messageCheck))
    element.appendChild(text)
    settings.appendChild(element)
    
    #Wall
    element = doc.createElement("wall")
    text = doc.createTextNode(booleanText(options.wallCheck))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("phototag")
    text = doc.createTextNode(booleanText(options.photoTagCheck))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("pokes")
    text = doc.createTextNode(booleanText(options.pokeCheck))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("friendCheck")
    text = doc.createTextNode(booleanText(options.friendCheck))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("shareCheck")
    text = doc.createTextNode(booleanText(options.shareCheck))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("groupCheck")
    text = doc.createTextNode(booleanText(options.groupCheck))
    element.appendChild(text)
    settings.appendChild(element)

    element = doc.createElement("eventCheck")
    text = doc.createTextNode(booleanText(options.eventCheck))
    element.appendChild(text)
    settings.appendChild(element)

    element = doc.createElement("startConnected")
    text = doc.createTextNode(booleanText(options.startConnected))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("updateInterval")
    text = doc.createTextNode(str(options.interval))
    element.appendChild(text)
    settings.appendChild(element)
    
    element = doc.createElement("popUpLinger")
    text = doc.createTextNode(str(options.popUpLinger))
    element.appendChild(text)
    settings.appendChild(element)
    
    doc.appendChild(settings)
    file_object = open(filename, "w")
    xml = doc.toxml()
    file_object.write(xml)
    file_object.close()

class OptionsFrame(wx.Frame):

    def __init__(self, parent, options, id=wx.ID_ANY, title="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self.options = options
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -1])
        # statusbar fields
        statusbar_fields = [("fbQuick"),
                            ("fbQuick Options")]
                            
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)

        #Set Icon
        icon =  wx.Icon('fbquickIcon.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self.SetMenuBar(self.CreateMenuBar())
              
        panel = wx.Panel(self, -1)
        sizerHorizontal = wx.BoxSizer(wx.HORIZONTAL)
        sizerVer0       = wx.BoxSizer(wx.VERTICAL)
	sizerVer1	= wx.BoxSizer(wx.VERTICAL)

        #Add Checkboxes for update criteria
        self.checkboxMessages = wx.CheckBox(panel, -1, "Messages", style=wx.CHK_2STATE)
        self.checkboxWall     = wx.CheckBox(panel, -1, "Wall", style=wx.CHK_2STATE)
        self.checkboxPokes    = wx.CheckBox(panel, -1, "Pokes", style=wx.CHK_2STATE)
        self.checkboxPhotoTag    = wx.CheckBox(panel, -1, "Tagged Photos", style=wx.CHK_2STATE)
        self.checkboxFriendCheck = wx.CheckBox(panel, -1, "Friend Requests", style=wx.CHK_2STATE)
        self.checkboxShareCheck = wx.CheckBox(panel, -1, "Shares", style=wx.CHK_2STATE)
        self.checkboxGroupCheck = wx.CheckBox(panel, -1, "Group Invites", style=wx.CHK_2STATE)
        self.checkboxEventCheck = wx.CheckBox(panel, -1, "Event Invites", style=wx.CHK_2STATE)


        self.checkboxStartConnected = wx.CheckBox(panel, -1, "Connect On Application Start", style=wx.CHK_2STATE)
           
        #Load Settings For Check Boxes
        if options.messageCheck:
          self.checkboxMessages.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxMessages.SetValue(wx.CHK_UNCHECKED)
        
        if options.wallCheck:
          self.checkboxWall.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxWall.SetValue(wx.CHK_UNCHECKED)
        
        if options.pokeCheck:
          self.checkboxPokes.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxPokes.SetValue(wx.CHK_UNCHECKED)
        
        if options.photoTagCheck:
          self.checkboxPhotoTag.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxPhotoTag.SetValue(wx.CHK_UNCHECKED)
        
        if options.startConnected:
          self.checkboxStartConnected.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxStartConnected.SetValue(wx.CHK_UNCHECKED)

        if options.friendCheck:
          self.checkboxFriendCheck.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxFriendCheck.SetValue(wx.CHK_UNCHECKED)
        
        if options.shareCheck:
          self.checkboxShareCheck.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxShareCheck.SetValue(wx.CHK_UNCHECKED)
        
        if options.groupCheck:
          self.checkboxGroupCheck.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxGroupCheck.SetValue(wx.CHK_UNCHECKED)
        
        if options.eventCheck:
          self.checkboxEventCheck.SetValue(wx.CHK_CHECKED)
        else:
          self.checkboxEventCheck.SetValue(wx.CHK_UNCHECKED)
        
        #Spacer
        sizerVer0.Add((0,5))
        sizerVer1.Add((0,30))

        statictext = StaticText(panel, -1, "Items checked on update")
        statictext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        statictext.SetForegroundColour("BLUE")
        sizerVer0.Add(statictext, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        
        sizerVer0.Add(self.checkboxMessages, 0, wx.EXPAND | wx.ALL, 5)
        sizerVer0.Add(self.checkboxWall,  0, wx.EXPAND | wx.ALL, 5)
        sizerVer0.Add(self.checkboxPokes, 0, wx.EXPAND | wx.ALL,5)
        sizerVer0.Add(self.checkboxPhotoTag, 0, wx.EXPAND | wx.ALL,5)
  
        sizerVer1.Add(self.checkboxFriendCheck, 0, wx.EXPAND | wx.ALL,5)
        sizerVer1.Add(self.checkboxShareCheck, 0, wx.EXPAND | wx.ALL,5)
        sizerVer1.Add(self.checkboxGroupCheck, 0, wx.EXPAND | wx.ALL,5)
        sizerVer1.Add(self.checkboxEventCheck, 0, wx.EXPAND | wx.ALL,5)
	

        #Update Interval choice box
        sizerVer0.Add((0,10))
        statictext = StaticText(panel, -1, "Update Interval(minutes)")
        statictext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        statictext.SetForegroundColour("BLUE")
        sizerVer0.Add(statictext, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        
        statictext = StaticText(panel, -1, "Current: " + str(options.interval) + " minutes")
        statictext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        statictext.SetForegroundColour("RED")
        sizerVer0.Add(statictext, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, 5)
        
    
        minuteList=['1', '5', '10', '15']
        self.choiceInterval = wx.Choice(panel, -1, choices = minuteList)
        x = minuteList.index(str(self.options.interval))
        self.choiceInterval.SetSelection(x)
        sizerVer0.Add(self.choiceInterval, 0, wx.EXPAND | wx.ALL, 5)
        
        #Pop up linger time
        sizerVer1.Add((0,9))
        statictext = StaticText(panel, -1, "Pop up linger(seconds)")
        statictext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        statictext.SetForegroundColour("BLUE")
        sizerVer1.Add(statictext, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        
        statictext = StaticText(panel, -1, "Current: " + str(options.popUpLinger) + " seconds")
        statictext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        statictext.SetForegroundColour("RED")
	sizerVer1.Add(statictext, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, 5)
    
        minuteList=['5', '10', '15', '30', '45', '60']
        self.choiceLinger = wx.Choice(panel, -1, choices = minuteList)
        x = minuteList.index(str(self.options.popUpLinger)) 
        self.choiceLinger.SetSelection(x)
        sizerVer1.Add(self.choiceLinger, 0, wx.EXPAND | wx.ALL, 5)

        # Other Stuff
        sizerVer0.Add((0,10))
        statictext = StaticText(panel, -1, "Other Stuff")
        statictext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        statictext.SetForegroundColour("BLUE")
        sizerVer0.Add(statictext, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        sizerVer0.Add(self.checkboxStartConnected, 0, wx.EXPAND | wx.ALL,5)

        hl = hyperlink.HyperLinkCtrl(panel, -1, 'More help at facebook group', URL='http://facebook.com/board.php?uid=2210484505')
        hl.SetUnderlines(True, True, True)
        hl.SetColours(wx.NamedColour("BLUE"))
        hl.SetBold(True)
        hl.UpdateLink()
	sizerVer1.Add((0,32))
        sizerVer1.Add(hl, 0, wx.EXPAND | wx.ALL, 5)

        #Add Update Button
   	sizerVer1.Add((0,10))
        self.button = wx.Button(panel, -1, "Update",(0,0),(120,30))
        self.button.Bind(wx.EVT_BUTTON, self.OnUpdate)
	
        sizerVer1.Add(self.button, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        sizerHorizontal.Add(sizerVer0, 0, wx.EXPAND | wx.ALL, 5)
        sizerHorizontal.Add(sizerVer1, 0, wx.EXPAND | wx.ALL, 5)
	panel.SetSizer(sizerHorizontal)
  

    def CreateMenuBar(self):

        # Make a menubar
        file_menu = wx.Menu()
        help_menu = wx.Menu()
        
        #MENU_FILE_SAVE  = wx.NewId()
        MENU_FILE_QUIT  = wx.NewId()
        MENU_HELP_ABOUT = wx.NewId()
        MENU_HELP_FAQ   = wx.NewId()
        
        #file_menu.Append(MENU_FILE_SAVE, "&Save")
        file_menu.Append(MENU_FILE_QUIT, "&Exit")
        
        help_menu.Append(MENU_HELP_FAQ, "&FAQ")
        help_menu.Append(MENU_HELP_ABOUT, "&About")

        menu_bar = wx.MenuBar()

        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(help_menu, "&Help")

        self.Bind(wx.EVT_MENU,  self.OnAbout, id=MENU_HELP_ABOUT)
        self.Bind(wx.EVT_MENU,  self.OnQuit, id=MENU_FILE_QUIT)
        self.Bind(wx.EVT_MENU,  self.OnFaq, id=MENU_HELP_FAQ)

        return menu_bar

    def OnFaq(self, event):
      webbrowser.open_new("http://facebook.com/board.php?uid=2210484505")          
    
    def OnUpdate(self, event):
      #Messages
      self.options.messageCheck = self.checkboxMessages.GetValue()

      #Wall
      self.options.wallCheck = self.checkboxWall.GetValue()

      #Pokes
      self.options.pokeCheck = self.checkboxPokes.GetValue()
      
      #PhotoTag Check
      self.options.photoTagCheck = self.checkboxPhotoTag.GetValue()

      #Friend Request Check
      self.options.friendCheck = self.checkboxFriendCheck.GetValue()

      self.options.shareCheck = self.checkboxShareCheck.GetValue()
      self.options.groupCheck = self.checkboxGroupCheck.GetValue()
      self.options.eventCheck = self.checkboxEventCheck.GetValue()

      #Connect on Start UP
      self.options.startConnected = self.checkboxStartConnected.GetValue()

      #Update Interval
      intervalChoice = self.choiceInterval.GetStringSelection()
      if(intervalChoice!=''):
        self.options.interval = int(intervalChoice)
          
      #Pop Up Linger Time
      lingerChoice = self.choiceLinger.GetStringSelection()
      if(lingerChoice!=''):
        self.options.popUpLinger = int(lingerChoice)
      
      self.Close(True)
      
    def OnQuit(self, event):
      self.Destroy()

    def OnAbout(self, event):

      msg = "fbQuick : Your Facebook Notifier\n\n" + \
            "fbquick.com\n\n" + \
            "Please report any bug/requests or improvements\n" + \
            "comments@fbQuick.com"
            
      dlg = wx.MessageDialog(self, msg, "fbQuick : About",
                             wx.OK | wx.ICON_INFORMATION)
      dlg.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False, "Verdana"))
      dlg.ShowModal()
      dlg.Destroy()



if __name__ == "__main__":

    app = wx.PySimpleApp()

    # Run The Demo
    optionsPersister= OptionsPersistence()
    options = optionsPersister.load("settings.xml")

    frame = OptionsFrame(None, options, -1, "FBQuick Options", size=(400,400))
    frame.CenterOnScreen()
    frame.Show()

    app.MainLoop()

    optionsPersister.save(options, "settings.xml")

