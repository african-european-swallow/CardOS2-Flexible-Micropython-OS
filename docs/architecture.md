# Architecture Overview

CardOS2 is built around a modular architecture designed to separate hardware-specific code from applications. This allows the same applications to run on different devices with little or no modification.

At the center of the operating system is the kernel, which manages the main event loop and coordinates the system's core components.

## Kernel

The kernel is responsible for:

* Running the main system loop
* Launching and switching applications
* Updating the display
* Managing system tasks

Most applications interact with the system through the `cos` object provided by the kernel.

## Drivers

Drivers provide support for hardware such as displays, keyboards, touchpads, gamepads, and other peripherals.

Applications request capabilities from the input system or use the graphics API, rather than communicating with hardware directly. This allows hardware to be replaced without modifying application code.

## Graphics

The graphics system provides a unified drawing API regardless of the display hardware being used.

Depending on the hardware configuration, CardOS2 can use either a full framebuffer or a segmented framebuffer to reduce memory usage.
Different graphics files may be avaible to support screens that can't use a framebuffer.

## Input

The input manager combines input from multiple devices into a common interface.

Applications request the capabilities they require, such as:

* Keyboard
* Dpad
* Touchpad
* Action buttons

The input manager determines which driver provides each capability.


## Note: CardOS2 is designed to have a dpad and action buttons (A, B, X, Y, START, SELECT) at least.

## Settings

System behavior is configured through a global settings system.

Settings define hardware configuration, display options, enabled drivers, and other system-wide options.

## Applications

Applications are independent modules that interact with CardOS2 through the public API.

This separation allows applications to remain portable across different hardware configurations without needing to know the details of the underlying device.

# Tasks

When a call for a task is received, the kernel starts a background task and temporarily pauses normal app execution flow.

While a task is active:

- the task is advanced step-by-step by the kernel each frame
- the application does not progress its logic in parallel
- the app is effectively “held” in place until the task yields back control

