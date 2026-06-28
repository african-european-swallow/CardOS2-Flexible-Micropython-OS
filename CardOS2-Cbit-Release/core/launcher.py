import os
import core.kernal as kernal

class App:
    def __init__(self, cos):
        self.claims = ['action','dpad']
        self.cos = cos

        # navigation state
        self.cwd = "/"
        self.files = []
        self.sel = 0
        self.page = 0

        # layout (computed in setup)
        self.cols = 1
        self.rows = 1
        self.items_per_page = 1
        self.box_w = 0
        self.box_h = 0

        # redraw flags (IMPORTANT for performance)
        self.dirty = True

        # blacklist
        self.blacklist = {
            "core/",
            "__pycache__/",
            "boot.py",
            "main.py"
        }

    # =========================
    # SETUP
    # =========================
    def setup(self):
        cos = self.cos
        cos.input.claim_caps(self.claims)
        cos.gfx.set_mode(full_fb=False, auto_clear=True)
        cos.gfx.set_font(cos.normal_font)
        # ===== CONFIG =====
        MIN_BOX_W = 80*cos.scale   # minimum width per item
        MIN_BOX_H = 60*cos.scale   # minimum height per item (usually it is -PADDING)
        TOP_BAR = 12 
        PADDING = 4
        self.TEXT_PADDING = 2

        # usable space
        usable_w = cos.use_w
        usable_h = cos.use_h - TOP_BAR

        # ===== GRID CALC =====
        self.cols = max(1, usable_w // MIN_BOX_W)
        self.rows = max(1, usable_h // MIN_BOX_H)

        # recompute exact size so it fits perfectly
        self.box_w = usable_w // self.cols
        self.box_h = usable_h // self.rows

        # store layout config
        self.top_bar = TOP_BAR+PADDING
        self.pad = PADDING
        self.items_per_page = self.cols * self.rows

        # ===== INIT STATE =====
        self.scan_dir()
        self.sel = 0
        self.page = 0
        self.dirty = True
    # =========================
    # FILESYSTEM
    # =========================
    def is_dir(self, path):
        try:
            return (os.stat(path)[0] & 0x4000) == 0x4000
        except:
            return False

    def scan_dir(self):
        path = self.cwd.rstrip("/")
        if path == "":
            path = "/"

        items = []

        try:
            for f in os.listdir(path):
                full = path.rstrip("/") + "/" + f

                if f in self.blacklist:
                    continue

                if self.is_dir(full):
                    items.append(f + "/")
                elif f.endswith(".py"):
                    items.append(f)

        except Exception as e:
            self.cos.error.report("Launcher", "DIR_FAIL", exc=e)

        # sort: dirs first
        dirs = [f for f in items if f.endswith("/")]
        files = [f for f in items if not f.endswith("/")]

        self.files = ["../"] + sorted(dirs) + sorted(files)

        # clamp selection
        if self.sel >= len(self.files):
            self.sel = max(0, len(self.files) - 1)

    # =========================
    # HELPERS
    # =========================
    def get_page_items(self):
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        return self.files[start:end]

    def move_selection(self, dx, dy):
        items = self.get_page_items()
        max_items = len(items)

        row = self.sel // self.cols
        col = self.sel % self.cols

        new_row = row + dy
        new_col = col + dx

        # move inside page
        if 0 <= new_col < self.cols and 0 <= new_row < self.rows:
            new_index = new_row * self.cols + new_col
            if new_index < max_items:
                self.sel = new_index
                self.dirty = True
                return

        # page transitions
        if dy == 1 and new_row >= self.rows:
            if (self.page + 1) * self.items_per_page < len(self.files):
                self.page += 1
                self.sel = min(col, len(self.get_page_items()) - 1)
                self.dirty = True

        elif dy == -1 and new_row < 0:
            if self.page > 0:
                self.page -= 1
                items = self.get_page_items()
                last_row = (len(items) - 1) // self.cols
                self.sel = min(last_row * self.cols + col, len(items) - 1)
                self.dirty = True

    def get_selected(self):
        items = self.get_page_items()
        if not items:
            return None
        return items[self.sel]

    def build_module_path(self, full_path):
        path = full_path.strip("/")

        # remove .py
        if path.endswith(".py"):
            path = path[:-3]
            
        if path.startswith('sd/') and self.cos.sd.present:
            path = path[3:]

        # block unsafe system areas
        if path.startswith("core/") or path.startswith("__"):
            return None

        # convert filesystem path to module path
        return path.replace("/", ".")
    # =========================
    # DRAW
    # =========================
    def draw(self):
        cos = self.cos

        cos.gfx.fill((0, 0, 0))

        # ===== PATH BAR =====
        cos.gfx.rect(0, 0, cos.use_w, self.top_bar-self.pad, (40, 40, 40), f=True)
        cos.gfx.smart_text(self.cwd,2,1,(255, 255, 0),end=cos.use_w - 2)

        items = self.get_page_items()

        for i, name in enumerate(items):
            row = i // self.cols
            col = i % self.cols

            # base position
            x = col * self.box_w
            y = self.top_bar + row * self.box_h

            pad = self.pad

            # padded box size
            w = self.box_w - pad
            h = self.box_h - pad

            # ===== HARD CLAMP =====
            if x + w > cos.use_w:
                w = cos.use_w - x
            if y + h > cos.use_h:
                h = cos.use_h - y

            if w <= 0 or h <= 0:
                continue

            selected = (i == self.sel)

            # ===== COLORS =====
            if selected:
                fill = (100, 100, 255)
                border = (255, 255, 255)
            else:
                fill = (40, 40, 40)
                border = (120, 120, 120)

            # folders green tint
            if name.endswith("/"):
                if selected:
                    fill = (80, 160, 80)
                else:
                    fill = (40, 80, 40)

            # ===== DRAW (FILL FIRST, BORDER SECOND) =====
            cos.gfx.rect(x, y, w, h, fill, f=True)
            cos.gfx.rect(x, y, w, h, border, f=False)

            # ===== TEXT =====
            char_w = cos.gfx.font_width()
            char_h = cos.gfx.font_height() + 2

            inner_w = w - 2 * self.TEXT_PADDING
            inner_h = h - 2 * self.TEXT_PADDING

            max_cols = max(1, inner_w // char_w)
            max_rows = max(1, inner_h // char_h)

            max_chars = max_cols * max_rows

            display_name = name

            # hard cap text first
            if len(display_name) > max_chars:
                display_name = display_name[:max(0, max_chars - 2)] + ".."

            max_pixel_h = max_rows * char_h

            cos.gfx.smart_text(display_name,x + self.TEXT_PADDING,y + self.TEXT_PADDING,(0, 255, 0),end=x + inner_w,return_spacing=2)

        self.dirty = False
        
    # =========================
    # RUN LOOP
    # =========================
    def run(self):
        cos = self.cos

        while True:
            dpad = cos.input.get_pressed_cap("dpad")

            # movement
            if "UP" in dpad:
                self.move_selection(0, -1)
            if "DOWN" in dpad:
                self.move_selection(0, 1)
            if "LEFT" in dpad:
                self.move_selection(-1, 0)
            if "RIGHT" in dpad:
                self.move_selection(1, 0)

            # SELECT
            if (cos.input.was_pressed_cap("dpad", "CENTER") or cos.input.was_pressed_cap('action','A')):
                selected = self.get_selected()

                if selected:
                    # go back
                    if selected == "../":
                        if self.cwd != "/":
                            self.cwd = "/".join(self.cwd.rstrip("/").split("/")[:-1])
                            if self.cwd == "":
                                self.cwd = "/"

                    # enter directory
                    elif selected.endswith("/"):
                        if self.cwd.endswith("/"):
                            self.cwd += selected
                        else:
                            self.cwd += "/" + selected

                    # launch app
                    else:
                        full_path = self.cwd.rstrip("/") + "/" + selected
                        module = self.build_module_path(full_path)

                        # ===== NOT A VALID APP =====
                        if not module:
                            self.cos.error.report("Launcher", "INVALID_PATH", exc=full_path)
                            self.dirty = True
                            continue

                        # ===== SAFE IMPORT CHECK =====
                        '''try:
                            __import__(module)
                        except Exception as e:
                            self.cos.error.report("Launcher", "IMPORT_FAIL", exc=e)
                            self.dirty = True
                            break
                            continue'''
                        
                        yield cos.intent.INTENT_REPLACE_APP({
                            "file": module
                        })

                    self.page = 0
                    self.sel = 0
                    self.scan_dir()
                    self.dirty = True

            # BACK
            if cos.input.was_pressed_cap('action','B'):
                if self.cwd != "/":
                    self.cwd = "/".join(self.cwd.rstrip("/").split("/")[:-1])
                    if self.cwd == "":
                        self.cwd = "/"

                    self.page = 0
                    self.sel = 0
                    self.scan_dir()
                    self.dirty = True

            # draw only if needed
            if self.dirty:
                self.draw()
                yield cos.intent.INTENT_DRAW

            yield cos.intent.INTENT_NO_OP
            
if __name__ == '__main__':
    kernal.run(App)