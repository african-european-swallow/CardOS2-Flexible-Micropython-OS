# CardOS2 Drivers

Drivers allow CardOS2 to access hardware while providing a consistant interface to applications. Drivers are automatically discovered by the input system and provide one or more input capabilities. Drivers come in two types: input and output.

Drivers should be placed in `/drivers/in/` or `/drivers/out/` depending on their function. They also have to end in `_driver.py`.

Input drivers provide data (buttons, sensors, touchpads, batteries, etc.).

Output drivers perform actions (haptics, LEDs, buzzers, etc.).

---

## Basic Structure

Every driver must contain a Driver class.

```python
class Driver:
    CAPABILITIES = []
    I2C_SUPPORT = []

    def __init__(self):
        pass

    def connect(self, settings=None):
        pass

    def disconnect(self):
        pass
```

---

## CAPABILITIES

Capabilities describe what the driver provides.

```python
CAPABILITIES = ["touchpad", "action"]
CAPABILITIES = ["battery"]
CAPABILITIES = ["tick", "notify"]
```

Applications interact with capabilities rather than specific hardware.

---

## I2C_SUPPORT

Drivers that use I2C should declare supported buses.

```python
I2C_SUPPORT = ["internal"]
I2C_SUPPORT = ["internal", "external"]
```

Use shared buses through the hardware manager:

from core.hardware import hw

```python
i2c = hw.get_i2c("internal")
Connection
```

Hardware should be initialized inside connect().

```python
def connect(self, settings=None):
    ...
```

When hardware is successfully found, the driver should set:

```python
self.present = True
```

---

## Input Drivers

Input drivers return information to the OS.

Common examples:

- Buttons
- Touchpads
- Sensors
- Battery monitors

To update cached values, many input drivers use:

```python
def poll(self):
    ...
```

Non-sensor input drivers return values to the input manager via:
```python
def get(self, cap):
    ...
```
Sensor input drivers return data via:

```python
def read(self, cap):
    ...
```

---

### Example:

Sensor:

```python
def read(self, cap):
    if cap == "battery":
        return [95]
    return []
```

Non-sensor:

```python
def get(self, cap):
    if cap == "action":
        return ["A"]
    return []
```

---

## Polymorphic drivers

Polymorphic drivers expose multiple capabilities from a single physical device. 
For example, a touchpad can act as both a grid input (touchpad) and a button-style input (action). 
To keep these linked and avoid conflicts, CardOS2 uses SHARED_CAP_GROUPS, which tells the system that these capabilities come from the same hardware source and must be owned together:
```python
SHARED_CAP_GROUPS = [["action", "touchpad"]]
```
This ensures that only one of the capablilites of the driver is exposed at a time, preventing mixed or duplicated input behavior.

This behavour is only achieved when an application calls: 
```python
cos.input.claim_caps(["action"])
# Action-? polymorphic drivers will only return action values
# Go to "cos_object.md" for more details
```

---

## System Quit Driver

`/drivers/in/system_quit_driver.py` allows for a global way to return to the defalt application. 

The defalt quit command at the moment is `START + SELECT + A`, although this can easily be changed by modifying the file.

---

## Output Drivers

Output drivers perform actions.

Common examples:

- Haptics
- LEDs
- Buzzers

---

### Example:

```python
def play(self, cap):
    ...
```

In app:
```python
cos.output.feedback("tick")
```

---

## Disconnect

Drivers should clean up any hardware references when disconnected.

```python
def disconnect(self):
    self.present = False
    self.device = None
```

---

## Guidelines

Drivers should:

- Initialize hardware
- Read or control hardware
- Expose capabilities

Drivers should not:

- Draw graphics
- Launch apps
- Modify OS state

Drivers should fail gracefully if hardware is missing so the OS can continue running.





---

## Driver Examples

Below are the basic structures for the main driver types in CardOS2.

---

## 1. Sensor Input Driver

For hardware that continuously provides readings (battery, IMU, temperature, etc.).

```python
from core.hardware import hw
# Import sensor library here

class Driver:
    CAPABILITIES = ["battery"]
    I2C_SUPPORT = ["internal"]

    def __init__(self):
        self.present = False
        self.device = None

    def connect(self, settings=None):
        # Initialize sensor hardware
        # e.g. self.device = sensor(self.i2c)
        self.present = True

    def disconnect(self):
        self.present = False
        self.device = None

    def probe(self):
        return self.device is not None

    def read(self, cap):
        if not self.present:
            return []

        if cap == "battery":
            return [100]  # example value

        return []
```

---

## Polled Input Driver

For inputs that change every frame (buttons, touchpads, gamepads).

```python
from core.hardware import hw
# Import library here

class Driver:
    CAPABILITIES = ["action"]
    I2C_SUPPORT = ["internal"]

    def __init__(self):
        self.present = False
        self.device = None
        self.cached = []

    def connect(self, settings=None):
        # Initialize input hardware
        self.present = True

    def disconnect(self):
        self.present = False
        self.device = None

    def probe(self):
        return self.device is not None

    def poll(self):
        if not self.present:
            self.cached = []
            return

        # read hardware once per frame
        self.cached = ["A"]

    def get(self, cap):
        if cap == "action":
            return self.cached

        return []
```

---

## Output Driver

For hardware that performs actions (haptics, LEDs, buzzers).

```python
from core.hardware import hw

class Driver:
    CAPABILITIES = ["tick", "error"]
    I2C_SUPPORT = ["internal"]

    def __init__(self):
        self.present = False
        self.device = None

    def connect(self, settings=None):
        # Initialize output hardware
        self.present = True

    def disconnect(self):
        self.present = False
        self.device = None

    def probe(self):
        return self.device is not None

    def play(self, cap):
        if not self.present:
            return

        if cap == "tick":
            # trigger haptic tick
            pass

        elif cap == "error":
            # trigger error feedback
            pass
```
