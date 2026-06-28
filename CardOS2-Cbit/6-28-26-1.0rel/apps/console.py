import io
import sys
import core.kernal as kernal


class App:
    def __init__(self, cos):
        self.cos = cos
        self.cos.gfx.set_font('normal')
        
        # execution scope
        self.locals = {"cos": cos}

        # single output system 
        self.output = PrintOutput(cos)
        
        self.buffer_text = ""
        self.block_mode = False

        self.input_history = []
        self.max_history = 30
        self.input_pos = -1
        

    def setup(self):
        self.cos.input.claim_caps(['action', 'dpad', 'keyboard'])
        self.output.push("Welcome to the console! If no kb, press Y to open os kb and B to enter typed commands.")

    # -------------------------
    # EXECUTION CORE
    # -------------------------
    def exec_code(self, code_str):
        original_print = print

        def dual_print(*args, **kwargs):
            sep = kwargs.get("sep", " ")
            end = kwargs.get("end", "\n")
            text = sep.join(str(a) for a in args) + end

            self.output.push(text)

            self.cos.gfx.fill((0, 0, 0))
            self.output.draw(0, 0)
            self.cos.gfx.draw()

        try:
            globals()["print"] = dual_print
            self.locals["print"] = dual_print

            try:
                compiled = compile(code_str, "<repl>", "eval")
                result = eval(compiled, self.locals, self.locals)
                if result is not None:
                    self.output.push(repr(result))
            except SyntaxError:
                exec(code_str, self.locals, self.locals)

        except Exception as e:
            self.output.push("Error: " + str(e))

        finally:
            globals()["print"] = original_print
            self.locals["print"] = original_print
    
    def run_code(self, code_str):
        self.exec_code(code_str)
        
    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self):
        cos = self.cos

        while True:
            cos.gfx.fill((0, 0, 0))

            # -------------------------
            # INPUT 
            # -------------------------
            keys = cos.input.get_pressed_cap("keyboard")
            dpad = cos.input.get_pressed_cap("dpad")

            if 'UP' in dpad and self.input_pos < len(self.input_history)-1:
                self.input_pos += 1
                self.output.live_input = self.input_history[self.input_pos]
                
            if 'DOWN' in dpad and self.input_pos > -1:
                self.input_pos -= 1
                if self.input_pos == -1:
                     self.output.live_input = ''
                else:
                    self.output.live_input = self.input_history[self.input_pos]
                
            for k in keys:
                if k == "\n":
                    continue

                elif k == 'BACKSPACE':
                    self.output.live_input = self.output.live_input[:-1]
                    continue

                elif k == 'TAB':
                    self.output.live_input += '    '
                    continue

                elif k == 'SPACE':
                    self.output.live_input += ' '
                    continue

                elif k in ("LEFT", "RIGHT", "UP", "DOWN", "ENTER", "ESC"):
                    continue

                self.output.live_input += str(k)
            
            if cos.input.was_pressed_cap("action", "Y"):
                prefix = "." if self.block_mode else ">"
                curr = self.output.live_input
                cos.run_task("text", cos.task.get_text,prompt=prefix,current=curr)
                yield cos.intent.INTENT_NO_OP
                if "text" in cos.task_results:
                    self.output.live_input = cos.task_results.pop("text")
            # -------------------------
            # exit app
            # -------------------------
            if cos.input.was_pressed_cap('keyboard', 'ESC'):
                yield cos.intent.INTENT_KILL_APP

            # -------------------------
            # commit line
            # -------------------------
            if cos.input.was_pressed_cap("keyboard", "ENTER") or cos.input.was_pressed_cap("action", "B"):

                line = self.output.live_input
                self.output.live_input = ""

                self.input_history.insert(0, line)
                self.input_history = self.input_history[:self.max_history]
                self.input_pos = -1
                
                if line is None:
                    line = ""
                
                prefix = "." if self.block_mode else ">"
                self.output.push(prefix + line)

                consumed = False
                # =====================================================
                # BUILT-IN COMMANDS
                # =====================================================
                if line.strip() == ":clear":
                    self.output.clear()
                    consumed = True
    
                # =====================================================
                # START BLOCK
                # =====================================================
                if not self.block_mode and line.rstrip().endswith(":"):
                    self.block_mode = True
                    self.buffer_text = line + "\n"
                    consumed = True

                # =====================================================
                # BLOCK MODE
                # =====================================================
                if self.block_mode and not consumed:

                    # EXIT BLOCK ON EMPTY ENTER
                    if line == "":

                        try:
                            self.exec_code(self.buffer_text)
                        except Exception as e:
                            self.output.push("Error: " + str(e))

                        self.buffer_text = ""
                        self.block_mode = False
                        consumed = True

                    else:
                        self.buffer_text += line + "\n"
                        consumed = True

                # =====================================================
                # SINGLE LINE EXECUTION
                # =====================================================
                if not consumed and not self.block_mode:
                    self.run_code(line)

            # -------------------------
            # RENDER
            # -------------------------
            self.output.block_mode = self.block_mode
            self.output.draw(0, 0)

            yield cos.intent.INTENT_DRAW
        
class PrintOutput:
    def __init__(self, cos):
        self.cos = cos
        self.block_mode = False

        # committed terminal history
        self.buffer = []

        # live input line
        self.live_input = ""

        self.char_w = cos.gfx.font_width()
        self.char_h = cos.gfx.font_height()
        self.spacing = 2

        self.screen_w = cos.use_w
        self.screen_h = cos.use_h

        self.chars_per_line = max(1, self.screen_w // self.char_w)
        self.useable_lines = max(1, self.screen_h // (self.char_h + self.spacing))

        self.scroll = 0
        self.follow = True

    # -------------------------
    # SAFE LINE WRAP
    # -------------------------
    def _wrap(self, text):
        if not text:
            return []

        lines = []
        i = 0
        n = len(text)

        while i < n:
            lines.append(text[i:i + self.chars_per_line])
            i += self.chars_per_line

        return lines

    # -------------------------
    # PUSH OUTPUT TEXT
    # -------------------------
    def push(self, text):
        text = str(text)

        if self.follow:
            self.scroll = 0

        for raw in text.split("\n"):
            i = 0
            while i < len(raw):
                self.buffer.append(raw[i:i + self.chars_per_line])
                i += self.chars_per_line

        # trim memory safely
        max_lines = self.useable_lines * 5
        if len(self.buffer) > max_lines:
            self.buffer = self.buffer[-max_lines:]

    # -------------------------
    # LIVE LINE HEIGHT
    # -------------------------
    def _live_lines(self):
        prompt = "." if self.block_mode else ">"
        text = prompt + (self.live_input or "")

        if not text:
            return 1

        lines = 1
        i = 0

        while i < len(text):
            i += self.chars_per_line
            if i < len(text):
                lines += 1

        return max(1, lines)

    # -------------------------
    # VIEW WINDOW
    # -------------------------
    def _view(self, live_lines):
        total = len(self.buffer)
        visible = self.useable_lines - live_lines

        if visible < 1:
            visible = 1

        if total <= visible:
            return 0, total

        start = max(0, total - visible - self.scroll)
        end = start + visible
        return start, end

    # -------------------------
    # DRAW TERMINAL
    # -------------------------
    def draw(self, x=0, y=0, color=(255, 255, 255)):
        live_lines = self._live_lines()
        start, end = self._view(live_lines)

        y_offset = 0

        # draw history
        for line in self.buffer[start:end]:
            self.cos.gfx.text(line, x, y + y_offset, color)
            y_offset += self.char_h + self.spacing

        # draw live input safely wrapped
        prompt = "." if self.block_mode else ">"
        text = prompt + (self.live_input or "")

        i = 0
        row = 0

        while i < len(text):
            chunk = text[i:i + self.chars_per_line]
            self.cos.gfx.text(chunk,x,y + y_offset + row * (self.char_h + self.spacing),(0, 255, 0))
            i += self.chars_per_line
            row += 1

    # -------------------------
    # CLEAR
    # -------------------------
    def clear(self):
        self.buffer = []
        self.live_input = ""
        self.scroll = 0
        self.follow = True

if __name__ == "__main__":
    kernal.run(App)