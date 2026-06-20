# The cos Object

Every CardOS2 application (and some drivers) receives a single cos object when it is created.

```python
class App:
    def __init__(self, cos):
        self.cos = cos
```

The cos object (CardOS System Context) is the main interface between applications and the operating system.

Applications should use it instead of importing kernel modules directly.

---

# System Services

These provide access to the main parts of CardOS2.

---

# cos.settings

Provides access to the settings system.

---

### load()

Reloads settings from /settings.cfg

```python 
cos.settings.load()
```
---

###  get(key, default=None)

Returns a setting value or default if it does not exist

```python 
cos.settings.get("ui.theme", "dark")
```

---

###  set(key, value)

Sets a setting in memory

```python 
cos.settings.set("ui.theme", "light")
```
---

###  save()

Saves settings to /settings.cfg

```python 
cos.settings.save()
```
---

###  get_section(prefix)

Returns all settings starting with prefix

```python 
cos.settings.get_section("ui")
```
Returns:

dict with prefix removed

---

###  has(key)
Checks if a setting exists
```python 
cos.settings.has("ui.theme")
```
Returns:

True or False

---

###  remove(key)

Removes a setting if it exists
```python 
cos.settings.remove("ui.theme")
```
---

# cos.input

Input system for CardOS2. Handles drivers, capabilities, and global key state.

---

### get()

Returns all currently pressed keys

```python
cos.input.get()
```

---

### get_pressed()

Keys pressed this frame

```python
cos.input.get_pressed()
```

---

### get_released()

Keys released this frame

```python
cos.input.get_released()
```

---

### is_down(key)

Checks if a key is currently held

```python
cos.input.is_down("A")
```

---

### was_pressed(key)

True if key was pressed this frame

```python
cos.input.was_pressed("A")
```

---

### was_released(key)

True if key was released this frame

```python
cos.input.was_released("A")
```

---

### get_cap(cap)

Returns keys for a capability

```python
cos.input.get_cap("dpad")
```

---

### is_down_cap(cap, key)

Checks if key is down in a capability

```python
cos.input.is_down_cap("dpad", "LEFT")
```

---

### get_pressed_cap(cap)

Keys pressed this frame for a capability

```python
cos.input.get_pressed_cap("dpad")
```

---

### get_released_cap(cap)

Keys released this frame for a capability

```python
cos.input.get_released_cap("dpad")
```

---

### was_pressed_cap(cap, key)

True if key was pressed this frame

```python
cos.input.was_pressed_cap("dpad", "LEFT")
```

---

### was_released_cap(cap, key)

True if key was released this frame

```python
cos.input.was_released_cap("dpad", "LEFT")
```

---

### get_sensor(cap, default=None)

Reads sensor value from a capability

```python
cos.input.get_sensor("temperature")
```

---

### claim_caps(caps)

Claims input capabilities for this app.

If multiple drivers provide the same capability, priority is resolved based on order.

Some drivers may expose multiple capabilities that map to the same physical input source (for example a card keyboard providing both "keyboard" and "action"). In these cases, claiming one can affect how the shared source is routed.

```python
cos.input.claim_caps(["keyboard", "dpad"])
```

**Note:** Capability priority is order-sensitive.

---

### clear_claims()

Clears all claimed capabilities

```python
cos.input.clear_claims()
```

---

### get_claims()

Returns currently claimed capabilities

```python
cos.input.get_claims()
```

---

### has_claim(cap)

Checks if a capability is claimed

```python
cos.input.has_claim("keyboard")
```

---

### get_active_capabilities()

Returns all active capabilities from drivers

```python
cos.input.get_active_capabilities()
```

---

# Notes

- Input updates once per frame
- Drivers are hot-swappable
- Capability system prevents input conflicts

---


# cos.output

Provides feedback output based on drivers. 

Example:

Haptic feedback motor.

---

### feedback(cap)

Plays feedback to any device that supports it.

Common feedback types:

- "tick"
-  "ok"
-  "error"
-  "buzz"
-  "alert_short"
-  "alert_long"
-  'notify'

```python
cos.output.feedback("tick")
```
---

# cos.gfx

Graphics system used for drawing and display control.

---

### set_mode(full_fb=None,auto_clear=None,segment=None,set_dimensions=None,set_percent=None)

(None = True/False)

**Deprecated**
Changes the settings of the screen, partually broken due to heap fragmentation. Can be disabled in settings.

- full_fb: True = screen takes up full framebuffer, False = screen fragmentation is defalt (settings)
- auto_clear: True = screen automatically clears before drawing, False = screen does not clear before drawing (Note: auto_clear should be True if the screen is segmented)
- segment: (segx, segy) manual segmentation
- set_dimensions:  (x, y) virtual screen size
- set_percent: Scale virtual screen size as percentage of physical display (100 = full size)

```python
cos.gfx.set_mode(full_fb=False, auto_clear=True)
```

---

### Drawing API

Color format: (r, g, b)

---

### fill(color)

Fill entire screen.

---

### fill_usable(color) (deprecated)

Fill usable screen area.

---

### pixel(x, y, color)

Draw a single pixel.

---

### hline(x, y, w, color)

Draw horizontal line.

---

### vline(x, y, h, color)

Draw vertical line.

---

### line(x1, y1, x2, y2, color)

Draw line between two points.

---

### rect(x, y, w, h, color, f=False)

Draw rectangle.

f = filled

---

### ellipse(x, y, xr, yr, color, f=False, m=None)

Draw ellipse.

f = filled

---

### poly(x, y, coords, color, f=False)

Draw polygon.

coords = list of points

---

### text(string, x, y, color, s=1)

Draw text.

s = scale

---

### large_text(...) (deprecated)

Use text() instead.

---

### smart_text(string, x, y, color, end=None, s=1, return_spacing=2)

Auto-wrapping text renderer.

- end: wrap X position
- return_spacing: line spacing in pixels

---

### scroll(xstep, ystep) (broken)

Scroll framebuffer (currently unstable).

---

### blit(fbuf, x, y, key=-1, palette=None) (broken)

Draw framebuffer to screen.
---

# cos.sd

SD card and file system access.

API coming soon

---

# cos.intent

Used to launch apps and pass data between them.

API coming soon

---

# cos.hw

Low level hardware access.

Most apps should avoid using this directly.

API coming soon

---

# cos.error

Error handling system.

API coming soon

---

# cos.task

Background task system.

API coming soon

---

# cos.taskbar

System taskbar control.

API coming soon

---

# Display Information

---

cos.scr_w

Screen width in pixels

---

cos.scr_h

Screen height in pixels

---

cos.use_w

Usable width for apps

---

cos.use_h

Usable height for apps

---

cos.textw

Text columns available

---

cos.texth

Text rows available

---

# Runtime Information

---

cos.running_app

Current running app instance

---

cos.running_app_name

Name of current app

---

cos.active_task

Current background task

---

cos.active_task_name

Name of active task

---

cos.task_results

Results of finished tasks

---

cos.fps

Current frame rate

---

cos.dt

Time between frames (seconds)

---

# System State

---

cos.app_intent_override

Intent used when launching apps

---

cos.taskbar_enabled

Whether taskbar is shown

---

cos.persist (dictionary)

Persistent runtime storage shared across apps
