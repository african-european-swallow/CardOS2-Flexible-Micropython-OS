import core.kernal as kernal
import time
import os


class App:
    def __init__(self, cos):
        self.cos = cos
        self.cos.gfx.set_font('normal')
        
        self.filename = None
        self.text = ""

        self.scroll_offset = 0
        self.horiz_scroll_offset = 0

        self.lines = [""]
        self.cursor_line = 0
        self.cursor_col = 0

        self.overide = True
        self.pending_backslash = False
        
        self.repeat_timer = {
            "LEFT": 0,
            "RIGHT": 0,
            "UP": 0,
            "DOWN": 0
        }

        self.repeat_active = {
            "LEFT": False,
            "RIGHT": False,
            "UP": False,
            "DOWN": False
        }

        self.repeat_delay = 0.4

    # -------------------------
    # SETUP
    # -------------------------
    def setup(self):
        self.cos.input.claim_caps(['dpad', 'keyboard', 'action'])

        if 'edit_app' in self.cos.persist:
            self.filename = self.cos.persist['edit_app']

    # -------------------------
    # FILE
    # -------------------------
    def load_file(self):
        try:
            with open(self.filename) as f:
                self.lines = f.read().split("\n")
        except:
            self.lines = [""]

        if not self.lines:
            self.lines = [""]

        self.cursor_line = 0
        self.cursor_col = 0

    def save_file(self):
        try:
            with open(self.filename, "w") as f:
                for i, line in enumerate(self.lines):
                    if isinstance(line, list):
                        f.write("".join(line))
                    else:
                        f.write(line)

                    if i != len(self.lines) - 1:
                        f.write("\n")

        except Exception as e:
            self.cos.error.report("Editor", "SAVE_FAIL", exc=e)

    # -------------------------
    # SYNTAX CHECK
    # -------------------------
    def syntax_check(self, source, filename="<string>"):
        try:
            compile(source, filename, "exec")
            return True, None
        except Exception as e:
            return False, str(e)

    # -------------------------
    # EDITING
    # -------------------------
    def insert_char(self, char):
        if char == "\\":
            self.pending_backslash = True
            return

        if self.pending_backslash:
            if char == "n":
                char = "\n"
            self.pending_backslash = False

        line = self.lines[self.cursor_line]

        self.lines[self.cursor_line] = (line[:self.cursor_col]+char+line[self.cursor_col:])

        self.cursor_col += len(char)
        
    def new_line(self):

        line = self.lines[self.cursor_line]

        left = line[:self.cursor_col]
        right = line[self.cursor_col:]

        self.lines[self.cursor_line] = left
        self.lines.insert(self.cursor_line + 1, right)

        self.cursor_line += 1
        self.cursor_col = 0

    def backspace(self):
        # middle of line
        if self.cursor_col > 0:
            line = self.lines[self.cursor_line]

            self.lines[self.cursor_line] = (line[:self.cursor_col - 1] +line[self.cursor_col:])

            self.cursor_col -= 1
            return

        # start of line merge up
        if self.cursor_line > 0:
            prev = self.lines[self.cursor_line - 1]
            cur = self.lines[self.cursor_line]

            self.cursor_col = len(prev)
            self.lines[self.cursor_line - 1] = prev + cur
            del self.lines[self.cursor_line]

            self.cursor_line -= 1
            
    def move_left(self):
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_line > 0:
            self.cursor_line -= 1
            self.cursor_col = len(self.lines[self.cursor_line])

    def move_right(self):
        line = self.lines[self.cursor_line]

        if self.cursor_col < len(line):
            self.cursor_col += 1
        elif self.cursor_line < len(self.lines) - 1:
            self.cursor_line += 1
            self.cursor_col = 0
        
    def scroll_up(self):
        if self.cursor_line > 0:
            self.cursor_line -= 1
            self.cursor_col = min(self.cursor_col,len(self.lines[self.cursor_line]))

    def scroll_down(self):
        if self.cursor_line < len(self.lines) - 1:
            self.cursor_line += 1
            self.cursor_col = min(self.cursor_col,len(self.lines[self.cursor_line]))

    # -------------------------
    # CURSOR HELPERS
    # -------------------------
    def get_cursor(self):
        return self.cursor_line, self.cursor_col
    
    def get_current_line_text(self):
        lines = self.lines
        line_idx, _ = self.get_cursor()
        if 0 <= line_idx < len(lines):
            return lines[line_idx]
        return ""
    
    def handle_repeat(self, key, is_down, was_pressed, action, dt):
        if was_pressed:
            action()
            self.repeat_active[key] = False
            self.repeat_timer[key] = self.repeat_delay
            return

        if not is_down:
            self.repeat_active[key] = False
            self.repeat_timer[key] = 0
            return

        # still waiting before repeat starts
        if not self.repeat_active[key]:
            self.repeat_timer[key] -= dt
            if self.repeat_timer[key] <= 0:
                self.repeat_active[key] = True
            return

        # repeat phase
        action()
    
    # -------------------------
    # SCREEN
    # -------------------------
    def update_screen(self):
        self.overide = False
        self.cos.gfx.fill((0, 0, 0))

        if not self.lines:
            return

        w, h = self.cos.use_w, self.cos.use_h
        line_h = self.cos.gfx.font_height()
        max_lines = h // line_h
        max_chars = w // self.cos.gfx.font_width() + 2 - 2

        lines = self.lines

        cur_line, cur_col = self.get_cursor()

        # -------------------------
        # VERTICAL SCROLL
        # -------------------------
        if cur_line < self.scroll_offset:
            self.scroll_offset = cur_line
        elif cur_line >= self.scroll_offset + max_lines:
            self.scroll_offset = cur_line - max_lines + 1

        # -------------------------
        # HORIZONTAL SCROLL
        # -------------------------
        if cur_col < self.horiz_scroll_offset:
            self.horiz_scroll_offset = cur_col
        elif cur_col >= self.horiz_scroll_offset + max_chars:
            self.horiz_scroll_offset = cur_col - max_chars + 1

        # -------------------------
        # DRAW TEXT
        # -------------------------
        for i in range(min(max_lines, len(lines) - self.scroll_offset)):
            line = lines[self.scroll_offset + i]

            visible = line[self.horiz_scroll_offset:self.horiz_scroll_offset + max_chars]

            self.cos.gfx.text(visible,0,i * line_h,(255, 255, 255))

        # -------------------------
        # CURSOR
        # -------------------------
        cx = (cur_col - self.horiz_scroll_offset) * self.cos.gfx.font_width()
        cy = (cur_line - self.scroll_offset) * line_h

        self.cos.gfx.text("_", cx, cy, (255, 255, 0))

        self.last_cursor = (self.cursor_line, self.cursor_col)

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self):
        if self.filename is None:
            yield self.cos.intent.INTENT_REPLACE_APP({"file": "apps.file_explorer"})
            
        self.load_file()
        self.cursor_line = len(self.lines) - 1
        self.cursor_col = len(self.lines[self.cursor_line])
        self.overide = True
        self.update_screen()
        last_time = time.ticks_ms()

        while True:
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last_time) / 1000
            last_time = now

            # EXIT
            if self.cos.input.was_pressed_cap("action", "SELECT"):
                yield self.cos.intent.INTENT_REPLACE_APP({"file": "apps.file_explorer"})

            # ENTER
            if self.cos.input.was_pressed_cap("keyboard", "ENTER") or self.cos.input.was_pressed_cap("action", "X"):
                self.new_line()

            # BACKSPACE
            if self.cos.input.was_pressed_cap("keyboard", "BACKSPACE") or self.cos.input.was_pressed_cap("action", "B"):
                self.backspace()
                
            if self.cos.input.was_pressed_cap("keyboard", "TAB"):
                [self.insert_char(' ') for z in range(4)]

            # ARROWS
            inp = self.cos.input

            self.handle_repeat("LEFT",
                inp.is_down_cap("dpad","LEFT"),
                inp.was_pressed_cap("dpad","LEFT"),
                self.move_left,
                dt
            )

            self.handle_repeat("RIGHT",
                inp.is_down_cap("dpad","RIGHT"),
                inp.was_pressed_cap("dpad","RIGHT"),
                self.move_right,
                dt
            )

            self.handle_repeat("UP",
                inp.is_down_cap("dpad","UP"),
                inp.was_pressed_cap("dpad","UP"),
                self.scroll_up,
                dt
            )

            self.handle_repeat("DOWN",
                inp.is_down_cap("dpad","DOWN"),
                inp.was_pressed_cap("dpad","DOWN"),
                self.scroll_down,
                dt
            )

            # SAVE
            if self.cos.input.was_pressed_cap("keyboard", "ESC") or self.cos.input.was_pressed_cap("action", "Y"):
                if self.filename.endswith(".py"):
                    source = "\n".join(self.lines)

                    ok, err = self.syntax_check(source, self.filename)

                    if not ok:
                        self.cos.gfx.fill((0, 0, 0))
                        self.cos.gfx.smart_text("SYNTAX ERROR", 0, 0, (255, 0, 0))
                        self.cos.gfx.smart_text(err[:40], 0, 10, (255, 0, 0))
                        time.sleep(1)

                self.save_file()

            # TEXT INPUT
            keys = self.cos.input.get_cap("keyboard")
            for k in keys:
                if len(k) == 1:
                    self.insert_char(k)
                    
            if self.cos.input.was_pressed_cap("action", "A"):
                line_idx, col = self.get_cursor()

                lines = self.lines

                if 0 <= line_idx < len(lines):
                    line_text = lines[line_idx]

                    # only edit text before cursor
                    before_cursor = line_text[:col]

                    self.cos.run_task("text",self.cos.task.get_text,current=before_cursor)

                    yield self.cos.intent.INTENT_NO_OP

                    if "text" in self.cos.task_results:
                        new_before = self.cos.task_results.pop("text")

                        # preserve text after cursor
                        after_cursor = line_text[col:]

                        lines[line_idx] = new_before + after_cursor
                        lines[line_idx] = new_before + after_cursor
                        self.lines = lines

                        self.cursor_line = line_idx
                        self.cursor_col = len(new_before)

                        self.overide = True

            self.update_screen()

            yield self.cos.intent.INTENT_DRAW


if __name__ == "__main__":
    del App
    import gc
    gc.collect()
    import apps.file_explorer as l
    kernal.run(l.App)