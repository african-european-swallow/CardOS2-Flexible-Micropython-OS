# core/error.py

import time
'''
"info"
"warn"
"error"
"fatal"'''
class ErrorSystem:
    def __init__(self, settings=None):
        self.settings = settings
        self.cos = None

        self.errors = []
        self.max_errors = 12

        self.last = None  # for spam suppression

        self.fatal_handler = None  # callback for crashes

    # =========================
    # REPORT ERROR
    # =========================
    def report(self, source, msg, exc=None, level="error"):
        # minimal allocation entry
        entry = (source, msg, level)

        # prevent spam (same error repeated)
        if self.last == entry:
            return
        #self.last = entry

        # bounded storage
        if len(self.errors) >= self.max_errors:
            self.errors.pop(0)
        self.errors.append(entry)

        # debug output
        if self.settings and self.settings.get("debug.errors", True):
            print("[ERR]", level, source, msg, exc)

        # handle fatal errors
        if level == "fatal":
            self._handle_fatal(source, msg, exc)
            
        #give feedback
        if self.cos.output:
            time.sleep(0.5)
            self.cos.output.feedback('error')

    # =========================
    # SAFE CALL WRAPPER
    # =========================
    def guard(self, source, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.report(source, "exception", e, level="error")
            return None

    # =========================
    # FATAL HANDLER
    # =========================
    def set_fatal_handler(self, func):
        self.fatal_handler = func

    def _handle_fatal(self, source, msg, exc):
        if self.cos:
            self.cos.run_task('error_warn', ErrorSystem.error_warn, f'[FATAL] {source} {msg} {exc}')
        if self.settings and self.settings.get("debug.errors", True):
            print("[FATAL]", source, msg, exc)

        if self.fatal_handler:
            try:
                self.fatal_handler(source, msg, exc)
            except Exception as e:
                print("[FATAL HANDLER FAILED]", e)

    # =========================
    # GETTERS
    # =========================
    def get(self):
        return self.errors

    def clear(self):
        self.errors.clear()
        self.last = None

    # =========================
    # ON-SCREEN warning
    # =========================
    @staticmethod
    def error_warn(cos, error):
        cos.gfx.fill((0,0,0))
        cos.gfx.smart_text(f'{error}\\nPress anything to continue.', 0, 0, (255,0,0),font=cos.normal_font)
        while True:
            if cos.input.get_pressed():
                yield True, error  # done
            yield False, None  # running