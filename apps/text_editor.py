import core.kernal as kernal
import time
import os


class App:
    def __init__(self, cos):
        self.cos = cos

        self.filename = None
        self.text = ""
        self.cursor_pos = 0

        self.scroll_offset = 0
        self.horiz_scroll_offset = 0

        self.last_text = ""
        self.last_cursor = -1

        self.overide = True
        self.pending_backslash = False

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
            with open(self.filename, "r") as f:
                self.text = f.read()
        except:
            self.text = ""

    def save_file(self):
        try:
            with open(self.filename, "w") as f:
                f.write(self.text)
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

        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos += len(char)

    def backspace(self):
        if self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
            self.cursor_pos -= 1

    def move_left(self):
        self.cursor_pos = max(0, self.cursor_pos - 1)

    def move_right(self):
        self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        
    def scroll_up(self):
        lines = self.text.split("\n")
        cursor_line = self.text.count("\n", 0, self.cursor_pos)

        if cursor_line <= 0:
            return

        # current column
        line_start = self.text.rfind("\n", 0, self.cursor_pos)
        if line_start == -1:
            cursor_column = self.cursor_pos
        else:
            cursor_column = self.cursor_pos - line_start - 1

        # previous line start
        prev_start = self.text.rfind("\n", 0, line_start)
        prev_start = prev_start + 1 if prev_start != -1 else 0

        prev_len = len(lines[cursor_line - 1])

        self.cursor_pos = prev_start + min(cursor_column, prev_len)

        #self.update_screen()
    
    def scroll_down(self):
        lines = self.text.split("\n")
        cursor_line = self.text.count("\n", 0, self.cursor_pos)

        if cursor_line >= len(lines) - 1:
            return

        # current column
        line_start = self.text.rfind("\n", 0, self.cursor_pos)
        if line_start == -1:
            cursor_column = self.cursor_pos
        else:
            cursor_column = self.cursor_pos - line_start - 1

        # next line start
        next_start = self.text.find("\n", self.cursor_pos)
        next_start = next_start + 1 if next_start != -1 else len(self.text)

        next_len = len(lines[cursor_line + 1])

        self.cursor_pos = next_start + min(cursor_column, next_len)

        #self.update_screen()

    # -------------------------
    # CURSOR HELPERS
    # -------------------------
    def get_cursor(self):
        pos = 0
        lines = self.text.split("\n")

        for i, line in enumerate(lines):
            if self.cursor_pos <= pos + len(line):
                return i, self.cursor_pos - pos
            pos += len(line) + 1

        return len(lines) - 1, len(lines[-1])
    
    def get_current_line_text(self):
        lines = self.text.split("\n")
        line_idx, _ = self.get_cursor()
        if 0 <= line_idx < len(lines):
            return lines[line_idx]
        return ""

    # -------------------------
    # SCREEN
    # -------------------------
    def update_screen(self):
        '''if (self.text == self.last_text and
            self.cursor_pos == self.last_cursor and
            not self.overide):
            return'''

        self.overide = False
        self.cos.gfx.fill((0, 0, 0))

        if not self.text:
            return

        w, h = self.cos.use_w, self.cos.use_h
        line_h = 8
        max_lines = h // line_h
        max_chars = w // 8

        lines = self.text.split("\n")

        cur_line, cur_col = self.get_cursor()

        # -------------------------
        # VERTICAL SCROLL
        # -------------------------
        if cur_line < self.scroll_offset:
            self.scroll_offset = cur_line
        elif cur_line >= self.scroll_offset + max_lines:
            self.scroll_offset = cur_line - max_lines + 1

        # -------------------------
        # HORIZONTAL SCROLL (IMPORTANT FIX)
        # -------------------------
        if cur_col < self.horiz_scroll_offset:
            self.horiz_scroll_offset = cur_col
        elif cur_col >= self.horiz_scroll_offset + max_chars:
            self.horiz_scroll_offset = cur_col - max_chars + 1

        # -------------------------
        # DRAW TEXT (NO smart_text)
        # -------------------------
        for i in range(min(max_lines, len(lines) - self.scroll_offset)):
            line = lines[self.scroll_offset + i]

            visible = line[self.horiz_scroll_offset:self.horiz_scroll_offset + max_chars]

            self.cos.gfx.text(
                visible,
                0,
                i * line_h,
                (255, 255, 255)
            )

        # -------------------------
        # CURSOR
        # -------------------------
        cx = (cur_col - self.horiz_scroll_offset) * 8
        cy = (cur_line - self.scroll_offset) * line_h

        self.cos.gfx.text("_", cx, cy, (255, 255, 0))

        self.last_text = self.text
        self.last_cursor = self.cursor_pos

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self):
        if self.filename is None:
            yield self.cos.intent.INTENT_REPLACE_APP({"file": "apps.file_explorer"})
            
        self.load_file()
        self.cursor_pos = len(self.text)
        self.overide = True
        self.update_screen()

        while True:

            # EXIT
            if self.cos.input.was_pressed_cap("action", "SELECT"):
                yield self.cos.intent.INTENT_REPLACE_APP({"file": "apps.file_explorer"})

            # ENTER
            if self.cos.input.was_pressed_cap("keyboard", "ENTER") or self.cos.input.was_pressed_cap("action", "X"):
                self.insert_char("\n")

            # BACKSPACE
            if self.cos.input.was_pressed_cap("keyboard", "BACKSPACE") or self.cos.input.was_pressed_cap("action", "B"):
                self.backspace()
                
            if self.cos.input.was_pressed_cap("keyboard", "TAB"):
                [self.insert_char(' ') for z in range(4)]

            # ARROWS
            if self.cos.input.is_down_cap("dpad", "LEFT"):
                self.move_left()

            if self.cos.input.is_down_cap("dpad", "RIGHT"):
                self.move_right()

            if self.cos.input.is_down_cap("dpad", "UP"):
                self.scroll_up()

            if self.cos.input.is_down_cap("dpad", "DOWN"):
                self.scroll_down()

            # SAVE
            if self.cos.input.was_pressed_cap("keyboard", "ESC") or self.cos.input.was_pressed_cap("action", "Y"):
                if self.filename.endswith(".py"):
                    ok, err = self.syntax_check(self.text, self.filename)
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
                line_text = self.get_current_line_text()

                self.cos.run_task("text",self.cos.task.get_text,current=line_text)

                yield self.cos.intent.INTENT_NO_OP

                if "text" in self.cos.task_results:
                    new_line = self.cos.task_results.pop("text")

                    # replace current line in file
                    lines = self.text.split("\n")
                    line_idx, _ = self.get_cursor()

                    if 0 <= line_idx < len(lines):
                        lines[line_idx] = new_line
                        self.text = "\n".join(lines)

                        self.cursor_pos = sum(len(l) + 1 for l in lines[:line_idx]) + len(new_line)

                    self.overide = True

            self.update_screen()

            yield self.cos.intent.INTENT_DRAW


if __name__ == "__main__":
    del App
    import gc
    gc.collect()
    import apps.file_explorer as l
    kernal.run(l.App)