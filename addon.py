#	PulseEqaulizerToggle is a Kodi plugin to toggle between different 
#	PulseAudio Eqaulizer profiles.
#	2021 wastis
#	
#	based on the code by Jason Newton <nevion@gmail.com
#	https://github.com/pulseaudio/pulseaudio
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Lesser General Public License as
#	published by the Free Software Foundation, either version 2.1 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Lesser General Public License for more details.
#
#	You should have received a copy of the GNU Lesser General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import xbmcaddon
import xbmcgui
import os, sys, dbus
 
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')


prop_iface='org.freedesktop.DBus.Properties'
eq_iface='org.PulseAudio.Ext.Equalizing1.Equalizer'
device_iface='org.PulseAudio.Core1.Device'

manager_path='/org/pulseaudio/equalizing1'
manager_iface='org.PulseAudio.Ext.Equalizing1.Manager'
core_iface='org.PulseAudio.Core1'
core_path='/org/pulseaudio/core1'
module_name='module-equalizer-sink'

def Error(msg):
	
	xbmcgui.Dialog().textviewer("PulseEqualizerToggle", msg + "\nPlease refer Kodi log.", False) 
	xbmc.log(msg , xbmc.LOGERROR) 
	sys.exit(-1)

def connect():
	try:
		if 'PULSE_DBUS_SERVER' in os.environ:
			address = os.environ['PULSE_DBUS_SERVER']
		else:
			bus = dbus.SessionBus()
			server_lookup = bus.get_object('org.PulseAudio1', '/org/pulseaudio/server_lookup1')
			address = server_lookup.Get('org.PulseAudio.ServerLookup1', 'Address', dbus_interface='org.freedesktop.DBus.Properties')
		return dbus.connection.Connection(address)
	except Exception as e:
		Error('Not able to connect to PulseEqualizer.\n' 
			  'has the module-dbus-protocol been loaded?\n'
			  'pactl load-module module-dbus-protocol')
		sys.exit(-1)
		
class Filter():
	def __init__(self,sink):
		self.sink_props=dbus.Interface(sink,dbus_interface=prop_iface)
		self.sink=dbus.Interface(sink,dbus_interface=eq_iface)
		self.channel=self.sink_props.Get(eq_iface,'NChannels')
	def set_filter(self,preamp,coefs):
		self.sink.SetFilter(self.channel,dbus.Array(coefs),self.preamp)
	def save_state(self):
		self.sink.SaveState()
	def load_profile(self,profile):
		self.sink.LoadProfile(self.channel,dbus.String(profile))

#------------------------------------
#	Setup Connection
#------------------------------------

#connect
connection=connect()

#load manager_obj
manager_obj=connection.get_object(object_path=manager_path)

#manager properties
manager_props=dbus.Interface(manager_obj,dbus_interface=prop_iface)

#try to get sinks
try:
	sinks=manager_props.Get(manager_iface,'EqualizedSinks')
except Exception:
	xbmc.log("here2" , xbmc.LOGERROR)
	# probably module not yet loaded, try to load it:
	try:
		core=connection.get_object(object_path=core_path)
		core.LoadModule(module_name,{},dbus_interface=core_iface)
		sinks=manager_props.Get(manager_iface,'EqualizedSinks')
	except Exception:
		Error('Loading %s module failed.\nExiting...\n' % module_name)
		sys.exit(-1)
		

profile_list = manager_props.Get(manager_iface,'Profiles')
sink_selection = 0

dialog = xbmcgui.Dialog()

if(len(sinks) > 1):
	#TODO multipe sinks, this part of the code is untested
	sink_selection = dialog.contextmenu(sinks)
	

selection = dialog.contextmenu(profile_list)
sink=connection.get_object(object_path=sinks[sink_selection])

sink_filter=Filter(sink)
sink_filter.load_profile(profile_list[selection])



