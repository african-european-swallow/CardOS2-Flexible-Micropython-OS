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

## Capability Input

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

## Sensors

---

### get_sensor(cap, default=None)

Reads sensor value from a capability

```python
cos.input.get_sensor("temperature")
```

---

# Capabilities

---

### claim_caps(caps)

Claim input capabilities for this app

```python
cos.input.claim_caps(["keyboard", "dpad"])
```

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

Provides terminal and debug output.

API coming soon

---

# cos.gfx

Graphics system used for drawing and display control.

API coming soon

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
