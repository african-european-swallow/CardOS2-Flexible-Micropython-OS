# core/kernal.py
# handles main os loop
"""
todo:
make the kernal less hardcoded, not direct LOADING txt etc. -later
system color list for unified color -later 
optional reboot in cfg -later
possibly compile into micropython itself -later
support for launching apps from sdcard and changhe kill app to file paths -launcher fixed

we hate heap fragmentation!
"""

#os imports
from core.setting import Settings
from core.output_manager import Output
from core.input_manager import Input
from core.gfx import Gfx
import core.intents as intent
from core.sdcard_manager import SDManager
import core.hardware as hardwarelib
from core.error import ErrorSystem
import core.tasks as task
from core.taskbar import TaskBar

import time
import sys
import gc
import os
import machine

class SystemContext:
    def __init__(self, settings):
        self.settings = settings
        self.input = None
        self.output = None
        self.gfx = None
        self.sd = None
        self.intent = None
        self.hw = None
        self.error = None
        self.task = None
        self.taskbar = None
        
        self.scr_w = None
        self.scr_h = None
        self.use_w = None
        self.use_h = None
        self.scale = None
        
        self.normal_font=None        
        
        self.task_results = {}
        self.active_task = None
        self.active_task_name = None
        
        self.running_app_name = None
        self.running_app = None

        self.app_intent_overide = None
        self.taskbar_enabled = True
        
        self.fps = 0
        self.dt = 0
        
        self.persist = {}
        
    def run_task(self, name, func, *args, **kwargs):
        self.active_task = func(self, *args, **kwargs)
        self.active_task_name = name

    def calculate_usable(self):
        status_bar_enabled = self.settings.get('dis.status_bar', False) and self.taskbar_enabled
        status_bar_height = int(self.settings.get('dis.status_bar_height', 0))
        self.use_h = self.scr_h - status_bar_height if status_bar_enabled else self.scr_h
        self.use_w = self.scr_w
    
    def set_taskbar(self,a):
        self.taskbar_enabled = a
        self.calculate_usable()
        
settings = Settings()
settings.load()

if isinstance(settings.get('cpu_freq', 240000000), int) and settings.get('cpu_freq', False) is False:
    machine.freq(settings.get('cpu_freq', 240000000))

cos = SystemContext(settings)

global hw

hw = hardwarelib.init(settings)
input_mgr = Input(settings)
input_mgr.ctx = cos
input_mgr.scan_drivers()
output_mgr = Output(settings)
output_mgr.scan_drivers()
gfx = Gfx(settings)
sd = SDManager(settings)
error = ErrorSystem(settings)

# wire into context
cos.input = input_mgr
cos.output = output_mgr
cos.gfx = gfx
cos.sd = sd
cos.intent = intent
cos.hw = hw
cos.error = error
cos.task = task
cos.taskbar = TaskBar(cos)

cos.scr_w = cos.settings.get('dis.x')
cos.scr_h = cos.settings.get('dis.y')
cos.scale = cos.settings.get('dis.scale',1)

cos.normal_font = cos.settings.get('dis.normal_text', 'normal')

cos.calculate_usable()
status_bar_enabled = cos.settings.get('dis.status_bar', False)

# inject ctx into manager
input_mgr.ctx = cos
output_mgr.error = error
gfx.error = error
error.cos = cos

def run(next_app):
    cos.input.clear_claims()
    current_module = next_app.__module__
    running_app = next_app(cos)
    running_app_instance = None
    cos.running_app = running_app
    cos.running_app_name = current_module

    # Take a snapshot of all modules loaded by the OS itself.
    # Any modules loaded later are assumed to belong to apps and
    # will be unloaded when switching apps.
    base_modules = set(sys.modules.keys())
    
    frame_start = time.ticks_ms()
    cos.dt = 0
    cos.fps = 0

    while True:
        cos.input.update()
        cos.output.update()
        cos.sd.update()
        
        now = time.ticks_us()
        dt_us = time.ticks_diff(now, frame_start)
        frame_start = now

        if dt_us <= 0:
            dt_us = 1

        cos.dt = dt_us / 1_000_000
        
        #if cos.dt > 0.05:
        #    cos.dt = 0.05
            
        cos.fps = 1.0 / cos.dt

        # =========================
        # RUN BACKGROUND TASK
        # =========================
        if cos.active_task:
            try:
                done, result = next(cos.active_task)
            except StopIteration as e:
                done = True
                result = e.value
            except Exception as e:
                done, result = True, str(e)

            if done:
                cos.task_results[cos.active_task_name] = result
                cos.active_task = None
                cos.active_task_name = None

            # While a task is running, always redraw.
            app_intent = cos.intent.INTENT_DRAW

        # =========================
        # RUN ACTIVE APPLICATION
        # =========================
        elif running_app:
            if not running_app_instance:
                cos.gfx.fill((0, 0, 0))
                running_app.setup()
                running_app_instance = running_app.run()
            
            try:
                app_intent = next(running_app_instance)
            except Exception as e:
                # print("{COS} APP CRASH:", e)
                error.report('Kernal', 'APP CRASH', exc=e, level="fatal")
                app_intent = cos.intent.INTENT_KILL_APP

        # =========================
        # NO APP RUNNING
        # =========================
        else:
            app_intent = cos.intent.INTENT_DRAW

        # APP INTENT OVERRIDE
        if cos.app_intent_overide:
            # if an override kills the app, also stop any active task.
            if cos.app_intent_overide == cos.intent.INTENT_KILL_APP:
                cos.active_task = None
                cos.active_task_name = None

            app_intent = cos.app_intent_overide
            cos.app_intent_overide = None
        
        # RUN TASK
        if app_intent and app_intent[0] == cos.intent.INTENT_TASK:
            _, task_name, func, args, kwargs = app_intent
            cos.run_task(task_name, func, *args, **kwargs)
            app_intent = cos.intent.INTENT_DRAW
        
        # KILL APP / LOAD NEW APP
        if cos.intent.is_intent(app_intent, cos.intent.INTENT_KILL_APP):
            cos.input.clear_claims()
            cos.gfx.set_mode(full_fb=False,auto_clear=True,segment=(cos.settings.get('dis.segx',2),cos.settings.get('dis.segy',2)),set_percent=100)
            cos.gfx.hard_queue_clear()
            cos.gfx.set_font(cos.normal_font)
            # Determine next app
            next_app_name = settings.get("bootapp", "core.launcher")
            if len(app_intent) == 2:
                next_app_name = app_intent[1]["file"]

            # Show loading screen
            cos.gfx.fill((0, 0, 0))
            cos.gfx.smart_text(f'Loading: {next_app_name}',0, 0,(0, 255, 0),font=cos.normal_font)
            cos.gfx.draw()

            # Let app clean itself up
            if running_app and hasattr(running_app, "cleanup"):
                try:
                    running_app.cleanup()
                except Exception as e:
                    error.report('Kernal', 'CLEANUP FAIL', exc=e)

            
            #cos.active_task = None
            #cos.active_task_name = None

           
            running_app = None
            running_app_instance = None

            print("{COS}: APP_KILLED")

            # Unload all modules not present at kernel startup 
            current_modules = list(sys.modules.keys())
            for mod_name in current_modules:
                if mod_name not in base_modules:
                    try:
                        print("{COS}: UNLOAD:", mod_name)
                        del sys.modules[mod_name]
                    except:
                        pass

            
            running_app = None
            running_app_instance = None

            gc.collect()
            time.sleep_ms(10)
            gc.collect()

            time.sleep_ms(100)
            
            mod = __import__(next_app_name, None, None, [None], 0)
            running_app = mod.App(cos)
            cos.running_app = running_app
            cos.running_app_name = next_app_name
            
            current_module = next_app_name

            # Remove temporary module reference
            mod = None

            
            gc.collect()

        # =========================
        # NO OP
        # =========================
        if cos.intent.is_intent(app_intent, cos.intent.INTENT_NO_OP):
            pass

        # =========================
        # DRAW
        # =========================
        if cos.intent.is_intent(app_intent, cos.intent.INTENT_DRAW):
            if status_bar_enabled and cos.taskbar_enabled:
                cos.taskbar.draw()

            cos.gfx.draw()
        
        
def get_applications(path,dir=True):
    def is_dir(path):
        try:
            mode = os.stat(path)[0]
            return mode & 0x4000 == 0x4000
        except:
            return False
    files = []
    for file in os.listdir(path):
        full_path = path.rstrip("/") + "/" + file
        if file.endswith(".py") or is_dir(full_path):
            if is_dir(full_path) and dir:
                files.append(file + '/')
            else:
                files.append(file)
    return files

def load_app(path): #later
    namespace = {}

    with open(path) as f:
        code = f.read()

    exec(compile(code, path, "exec"), namespace)

    return namespace["App"]