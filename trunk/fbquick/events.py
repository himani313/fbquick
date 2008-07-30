import wx.lib.newevent

FBQApp_StateOnline_Event, EVT_FBQA_STATEONLINE = wx.lib.newevent.NewEvent()
FBQApp_StateOffline_Event, EVT_FBQA_STATEOFFLINE = wx.lib.newevent.NewEvent()
FBQApp_StateIconNew_Event, EVT_FBQA_STATEICONNEW = wx.lib.newevent.NewEvent()
FBQApp_StateIconDefault_Event, EVT_FBQA_STATEICONDEFAULT = wx.lib.newevent.NewEvent()
FBQApp_SetTimerInterval_Event, EVT_FBQA_SETTIMERINTERVAL = wx.lib.newevent.NewEvent()
FBQApp_TriggerPoll_Event, EVT_FBQA_TRIGGERPOLL = wx.lib.newevent.NewEvent()

FBQController_LoginFirst_Event, EVT_FBQC_LOGINFIRST = wx.lib.newevent.NewEvent()
FBQController_FailedServiceCall_Event, EVT_FBQC_FAILEDSERVICECALL = wx.lib.newevent.NewEvent()


