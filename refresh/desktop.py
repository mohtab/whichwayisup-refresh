"""Optional Hyprland resize adapter, restricted to this process's game window.

Only used by an explicit F2 resize. No configuration or global bindings are changed.
SDL handles other desktops. Lua/legacy dispatch follows installed Omarchy helpers.
"""
import json
import os
import re
import shutil
import subprocess

def resize_own_window(size):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') or not shutil.which('hyprctl'):return False
    def call(*args):
        return subprocess.run(['hyprctl',*args],capture_output=True,text=True,timeout=.5,check=True).stdout
    def dispatch(lua,*legacy):
        try:call('dispatch',lua)
        except subprocess.CalledProcessError:call('dispatch',*legacy)
    try:
        clients=json.loads(call('clients','-j'))
        matches=[c for c in clients if c.get('pid')==os.getpid() and
                 c.get('title','').startswith('Which Way Is Up?') and c.get('mapped')]
        if len(matches)!=1:return False
        client=matches[0];address=client.get('address','')
        if not re.fullmatch(r'0x[0-9a-fA-F]+',address):return False
        window='address:'+address
        if not client.get('floating'):
            dispatch(f'hl.dsp.window.float({{ window = "{window}", action = "toggle" }})','setfloating',window)
        scale=1.
        if type(client.get('monitor')) is int:
            monitors=json.loads(call('monitors','-j'))
            scale=next((m.get('scale',1.) for m in monitors if m.get('id')==client['monitor']),1.)
            if not isinstance(scale,(int,float)) or not .5<=scale<=4:scale=1.
        # SDL surfaces use physical pixels here; Hyprland dispatch uses logical pixels.
        w,h=(max(1,round(value/scale)) for value in size)
        dispatch(f'hl.dsp.window.resize({{ window = "{window}", x = {w}, y = {h} }})',
                 'resizewindowpixel',f'exact {w} {h},{window}')
        dispatch(f'hl.dsp.window.center({{ window = "{window}" }})','centerwindow',window)
        return True
    except (OSError,ValueError,TypeError,subprocess.SubprocessError):return False
