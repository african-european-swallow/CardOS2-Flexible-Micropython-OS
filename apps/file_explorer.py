import os
import core.kernal as kernal


class App:
    def __init__(self, cos):
        self.cos = cos
        self.claims = ["action", "dpad"]
        cos.gfx.set_font('normal')
        
        self.cwd = "/"

        self.files = []

        self.sel = 0
        self.scroll = 0

        self.mode = "browse"

        self.menu_items = []
        self.menu_sel = 0
        
        self.info_lines = []
        self.info_scroll = 0

        self.line_h = 12
        self.visible_rows = 1
        
        self.y_items = []
        self.y_sel = 0
        
        self.delete_confirm = False
        
        self.clipboard = None
        self.clipboard_mode = None  # "copy" or "cut"

        self.dirty = True

        self.blacklist = {}

    # ==================================================
    # SETUP
    # ==================================================

    def setup(self):
        cos = self.cos

        cos.input.claim_caps(self.claims)
        cos.gfx.set_mode(full_fb=False,auto_clear=True)

        self.visible_rows = max(1,(cos.use_h - 24) // self.line_h)

        self.scan_dir()

    # ==================================================
    # FILESYSTEM
    # ==================================================

    def is_dir(self, path):
        try:
            return (os.stat(path)[0] & 0x4000) == 0x4000
        except:
            return False

    def build_path(self, name):
        if self.cwd == "/":
            return "/" + name

        return self.cwd.rstrip("/") + "/" + name

    def scan_dir(self):
        entries = []

        try:

            path = self.cwd.rstrip("/")
            if path == "":
                path = "/"

            for name in os.listdir(path):

                if name in self.blacklist:
                    continue

                full = self.build_path(name)

                entries.append({"name": name,"dir": self.is_dir(full)})

        except Exception as e:
            self.cos.error.report("Explorer","SCAN_FAIL",exc=e)

        dirs = sorted([e for e in entries if e["dir"]],key=lambda x: x["name"].lower())

        files = sorted([e for e in entries if not e["dir"]],key=lambda x: x["name"].lower())

        self.files = []

        if self.cwd != "/":
            self.files.append({"name": "..","dir": True})

        self.files.extend(dirs)
        self.files.extend(files)

        if not self.files:
            self.sel = 0
            self.scroll = 0
        else:
            self.sel = min(self.sel,len(self.files) - 1)

        self.dirty = True
        
    def create_file(self):
        cos = self.cos

        cos.run_task("text",cos.task.get_text,prompt="File:")

        yield cos.intent.INTENT_NO_OP

        if "text" not in cos.task_results:
            return

        name = cos.task_results.pop("text").strip()

        if not name:
            return

        path = self.build_path(name)

        try:
            with open(path, "w") as f:
                f.write("")
        except Exception as e:
            self.cos.error.report("Explorer","CREATE_FILE_FAIL",exc=e)
        self.scan_dir()
        
    def paste(self):
        if not self.clipboard:
            return

        name = self.clipboard.split("/")[-1]
        dest = self.build_path(name)

        # check if exists
        try:
            open(dest, "rb").close()
            exists = True
        except:
            exists = False

        if exists:
            dest = self.build_path("copy_" + name)

        try:
            if self.clipboard_mode == "copy":
                with open(self.clipboard, "rb") as fsrc:
                    with open(dest, "wb") as fdst:
                        fdst.write(fsrc.read())

            elif self.clipboard_mode == "cut":
                os.rename(self.clipboard, dest)
                self.clipboard = None

        except:
            pass

        self.scan_dir()


    def create_folder(self):
        cos = self.cos

        cos.run_task("text",cos.task.get_text,prompt="Dir:")

        yield cos.intent.INTENT_NO_OP

        if "text" not in cos.task_results:
            return

        name = cos.task_results.pop("text").strip()

        if not name:
            return

        path = self.build_path(name)

        try:
            os.mkdir(path)
        except Exception as e:
            self.cos.error.report("Explorer","CREATE_FOLDER_FAIL",exc=e)

        self.scan_dir()


    def refresh(self):
        self.scan_dir()
        
    def rename(self):
        item = self.selected()

        if not item or item["name"] == "..":
            return

        old_path = self.build_path(item["name"])

        # ask user for new name 
        cos = self.cos
        cos.run_task("text",cos.task.get_text,prompt="Rename:",current=item["name"])

        yield cos.intent.INTENT_NO_OP

        if "text" not in cos.task_results:
            return

        new_name = cos.task_results.pop("text").strip()

        if not new_name or new_name == item["name"]:
            return

        new_path = self.build_path(new_name)

        try:
            os.rename(old_path, new_path)
        except Exception as e:
            self.cos.error.report("Explorer", "RENAME_FAIL", exc=e)

        self.scan_dir()
        
    def delete_selected(self):
        item = self.selected()

        if not item or item["name"] == "..":
            return

        path = self.build_path(item["name"])

        try:

            if item["dir"]:
                self.delete_tree(path)
            else:
                os.remove(path)

        except Exception as e:
            self.cos.error.report("Explorer","DELETE_FAIL",exc=e)

        self.scan_dir()
        
    def delete_tree(self, path):
        for name in os.listdir(path):

            full = path.rstrip("/") + "/" + name

            if self.is_dir(full):
                self.delete_tree(full)
            else:
                os.remove(full)

        os.rmdir(path)

    # ==================================================
    # SELECTION
    # ==================================================

    def move_selection(self, delta):
        if not self.files:
            return

        self.sel += delta

        if self.sel < 0:
            self.sel = 0

        if self.sel >= len(self.files):
            self.sel = len(self.files) - 1

        if self.sel < self.scroll:
            self.scroll = self.sel

        if self.sel >= self.scroll + self.visible_rows:
            self.scroll = (self.sel- self.visible_rows+ 1)

        self.dirty = True

    def selected(self):
        if not self.files:
            return None

        return self.files[self.sel]
    
    def get_info_visible_lines(self):
        h = self.cos.use_h - 20
        return max(1, (h - self.cos.gfx.font_width()) // 12)


    def get_info_max_scroll(self):
        visible = self.get_info_visible_lines()

        return max(0,len(self.info_lines) - visible)

    # ==================================================
    # DIRECTORY NAVIGATION
    # ==================================================

    def go_up(self):
        if self.cwd == "/":
            return

        self.cwd = "/".join(self.cwd.rstrip("/").split("/")[:-1])

        if self.cwd == "":
            self.cwd = "/"

        self.sel = 0
        self.scroll = 0

        self.scan_dir()

    def enter_directory(self, dirname):
        if self.cwd == "/":
            self.cwd += dirname
        else:
            self.cwd += "/" + dirname

        self.sel = 0
        self.scroll = 0

        self.scan_dir()

    # ==================================================
    # MENU
    # ==================================================

    def open_menu(self):
        self.delete_confirm = False
        item = self.selected()

        if item is None:
            return

        if item["dir"]:
            self.menu_items = [
                "Open",
                "Info",
                "Delete",
                "Cancel"
            ]
        else:
            self.menu_items = [
                "Open",
                "Info",
                "Rename",
                "Copy",
                "Move",
                "Delete",
                "Cancel"
            ]

        self.menu_sel = 0
        self.mode = "menu"
        self.dirty = True

    def close_menu(self):
        self.delete_confirm = False
        self.mode = "browse"
        self.dirty = True
        
    def open_y_menu(self):
        self.y_items = ["New File", "New Folder"]

        if self.clipboard:
            self.y_items.insert(2, "Paste")
        
        self.y_items.append("Refresh")

        self.y_items.append("Cancel")

        self.y_sel = 0
        self.mode = "y_menu"
        self.dirty = True


    def close_y_menu(self):
        self.mode = "browse"
        self.dirty = True

    def format_size(self, size):
        if size < 1024:
            return "%d B" % size

        if size < 1024 * 1024:
            return "%.1f KB" % (size / 1024)

        return "%.1f MB" % (size / (1024 * 1024))
    
    def open_info(self):
        self.info_scroll = 0

        item = self.selected()

        if item is None:
            return

        path = self.build_path(item["name"])

        lines = []

        # name
        lines.append(item["name"])

        try:
            stat = os.stat(path)

            # --------------------
            # FOLDER INFO
            # --------------------

            if item["dir"]:
                lines.append("Folder")

                try:
                    dirs = 0
                    files = 0

                    for name in os.listdir(path):
                        full = path.rstrip("/") + "/" + name

                        if self.is_dir(full):
                            dirs += 1
                        else:
                            files += 1

                    lines.append("Dirs: %d" % dirs)

                    lines.append("Files: %d" % files)

                    lines.append("Items: %d" % (dirs + files))

                except:
                    lines.append("List Error")

            # --------------------
            # FILE INFO
            # --------------------

            else:
                lines.append("File")

                lines.append("Size: " + self.format_size(stat[6]))

                # extension
                if "." in item["name"]:
                    ext = item["name"].rsplit(".",1)[1]

                    lines.append("Ext: " + ext)

                # cardos specific

                if item["name"].endswith(".py"):
                    lines.append("Python")

                # preview
                try:
                    lines.append("")
                    lines.append("Preview:")

                    with open(path, "r") as f:
                        for _ in range(3):
                            line = f.readline()

                            if not line:
                                break

                            line = line.strip()

                            if line:
                                lines.append(line)
                            else:
                                lines.append("")

                except:
                    lines.append("No Preview")

        except:
            lines.append("Stat Error")

        lines.append("")
        lines.append(path)

        self.info_lines = lines

        self.mode = "info"
        self.dirty = True

    # ==================================================
    # FILE ACTIONS
    # ==================================================

    def open_selected(self):
        item = self.selected()

        if item is None:
            return

        if item["dir"]:

            if item["name"] == "..":
                self.go_up()
            else:
                self.enter_directory(item["name"])

            return

        full_path = self.build_path(item["name"])

        # launch editor app
        self.cos.persist['edit_app'] = full_path
        yield self.cos.intent.INTENT_REPLACE_APP({"file": "apps.text_editor"})

    # ==================================================
    # DRAW
    # ==================================================

    def draw_browser(self):
        cos = self.cos

        cos.gfx.fill((0, 0, 0))

        # top bar

        cos.gfx.rect(0,0,cos.use_w,12,(40, 40, 40),f=True)

        path_text = self.trim_path(self.cwd,cos.use_w - 4)

        cos.gfx.smart_text(path_text,2,1,(255, 255, 0))

        visible = self.files[self.scroll:self.scroll + self.visible_rows]

        for i, item in enumerate(visible):
            actual_index = self.scroll + i

            y = 14 + i * self.line_h

            if actual_index == self.sel:

                cos.gfx.rect(0,y,cos.use_w,self.line_h,(80, 80, 180),f=True)

            if item["dir"]:
                prefix = "[D] "
                color = (100, 255, 100)
            else:
                prefix = "[F] "
                color = (255, 255, 255)

            text = prefix + item["name"]

            text = self.trim_text(text,cos.use_w - 4)

            cos.gfx.smart_text(text,2,y + 1,color)

        # bottom help bar
        bottom = cos.use_h - 10

        cos.gfx.rect(0,bottom,cos.use_w,10,(40, 40, 40),f=True)

        cos.gfx.smart_text("A:Menu,B:Up,Y:GMenu",2,bottom + 1,(255, 255, 255))

    def draw_menu(self):
        self.draw_browser()

        cos = self.cos

        mw = 90
        mh = len(self.menu_items) * 12 + 4

        mx = (cos.use_w - mw) // 2
        my = (cos.use_h - mh) // 2

        cos.gfx.rect(mx,my,mw,mh,(20, 20, 20),f=True)

        cos.gfx.rect(mx,my,mw,mh,(255, 255, 255),f=False)

        for i, option in enumerate(self.menu_items):
            y = my + 2 + i * 12

            if i == self.menu_sel:

                if self.delete_confirm and option == "Delete":
                    color = (255, 0, 0)   # red confirm state
                else:
                    color = (80, 80, 180)   # normal highlight

                cos.gfx.rect(mx + 1,y,mw - 2,12,color,f=True)

            display_text = option

            if self.delete_confirm and option == "Delete":
                display_text = "CONFIRM"

            cos.gfx.smart_text(display_text,mx + 4,y + 1,(255, 255, 255))

    def draw(self):
        if self.mode == "browse":
            self.draw_browser()

        elif self.mode == "menu":
            self.draw_menu()

        elif self.mode == "info":
            self.draw_info()

        elif self.mode == "y_menu":
            self.draw_y_menu()

        self.dirty = False
        
    def draw_info(self):
        self.draw_browser()

        cos = self.cos

        w = cos.use_w - 20
        h = min(cos.use_h - 20,len(self.info_lines) * 12 + self.cos.gfx.font_width())

        x = (cos.use_w - w) // 2
        y = (cos.use_h - h) // 2

        cos.gfx.rect(x,y,w,h,(20,20,20),f=True)

        cos.gfx.rect(x,y,w,h,(255,255,255),f=False)

        visible_lines = self.get_info_visible_lines()

        visible = self.info_lines[self.info_scroll:self.info_scroll + visible_lines]

        for i, line in enumerate(visible):
            line = self.trim_text(line,w - self.cos.gfx.font_width())

            cos.gfx.smart_text(line,x + 4,y + 4 + i * 12,(255,255,255))
            
        if self.get_info_max_scroll() > 0:
            cos.gfx.smart_text("%d/%d" % (self.info_scroll + 1,self.get_info_max_scroll() + 1),x + w - 30,y + h - 10,(150, 150, 150))
    
    def draw_y_menu(self):
        self.draw_browser()

        cos = self.cos

        mw = 100
        mh = len(self.y_items) * 14 + 6

        mx = (cos.use_w - mw) // 2
        my = (cos.use_h - mh) // 2

        cos.gfx.rect(mx, my, mw, mh, (20,20,20), f=True)
        cos.gfx.rect(mx, my, mw, mh, (255,255,255), f=False)

        for i, item in enumerate(self.y_items):

            y = my + 3 + i * 14

            if i == self.y_sel:
                cos.gfx.rect(mx+1, y, mw-2, 14, (120,120,200), f=True)

            cos.gfx.smart_text(item,mx + 6,y + 2,(255,255,255))
    
    def trim_path(self, text, max_width_px):
        chars = max_width_px // self.cos.gfx.font_width()

        if len(text) <= chars:
            return text

        if chars <= 3:
            return "." * chars

        return ".." + text[-(chars - 2):]
    
    def trim_text(self, text, max_width_px):
        # 8px font assumption
        chars = max_width_px // self.cos.gfx.font_width()

        if chars <= 0:
            return ""

        if len(text) <= chars:
            return text

        if chars <= 3:
            return "." * chars

        return text[:chars - 2] + ".."

    # ==================================================
    # RUN
    # ==================================================

    def run(self):
        cos = self.cos

        while True:

            if self.mode == "browse":

                if "UP" in cos.input.get_pressed_cap("dpad"):
                    self.move_selection(-1)

                if "DOWN" in cos.input.get_pressed_cap("dpad"):
                    self.move_selection(1)

                if cos.input.was_pressed_cap("action", "A"):
                    self.open_menu()

                if cos.input.was_pressed_cap("action", "B"):
                    self.go_up()
                    
                if cos.input.was_pressed_cap("action", "Y"):
                    self.open_y_menu()

            elif self.mode == "menu":
                
                if "UP" in cos.input.get_pressed_cap("dpad"):
                    self.menu_sel = max(0, self.menu_sel - 1)
                    self.delete_confirm = False
                    self.dirty = True

                if "DOWN" in cos.input.get_pressed_cap("dpad"):
                    self.menu_sel = min(len(self.menu_items) - 1, self.menu_sel + 1)
                    self.delete_confirm = False
                    self.dirty = True
                
                if self.delete_confirm:
                    # ONLY allow confirming delete OR cancelling
                    if cos.input.was_pressed_cap("action", "A"):
                        self.delete_selected()
                        self.delete_confirm = False
                        self.close_menu()

                    elif cos.input.was_pressed_cap("action", "B"):
                        self.delete_confirm = False
                        self.dirty = True

                    yield cos.intent.INTENT_NO_OP
                    continue

                if cos.input.was_pressed_cap("action", "B"):
                    self.close_menu()

                if cos.input.was_pressed_cap("action", "A"):

                    action = self.menu_items[self.menu_sel]

                    if action == "Open":
                        self.close_menu()
                        result = self.open_selected()
                        if result:
                            yield from result

                    elif action == "Info":
                        self.open_info()

                    elif action == "Rename":
                        result = self.rename()
                        if result:
                            yield from result

                    elif action == "Copy":
                        item = self.selected()
                        if not item or item["name"] == "..":
                            pass
                        if item:
                            self.clipboard = self.build_path(item["name"])
                            self.clipboard_mode = "copy"

                    elif action == "Move":
                        item = self.selected()
                        if not item or item["name"] == "..":
                            pass
                        if item:
                            self.clipboard = self.build_path(item["name"])
                            self.clipboard_mode = "cut"
                            
                    elif action == "Delete":
                        self.delete_confirm = True
                        self.dirty = True
                        
                    if action not in ("Delete", "Info"):
                        self.close_menu()
                        
            elif self.mode == "info":

                if "UP" in cos.input.get_pressed_cap("dpad"):

                    self.info_scroll = max(0,self.info_scroll - 1)
                    self.dirty = True

                if "DOWN" in cos.input.get_pressed_cap("dpad"):

                    self.info_scroll = min(self.get_info_max_scroll(),self.info_scroll + 1)
                    self.dirty = True

                if (cos.input.was_pressed_cap("action", "A") or cos.input.was_pressed_cap("action", "B")):
                    self.mode = "browse"
                    self.dirty = True
                    
                    
            elif self.mode == "y_menu":

                if "UP" in cos.input.get_pressed_cap("dpad"):
                    self.y_sel = max(0, self.y_sel - 1)
                    self.dirty = True

                if "DOWN" in cos.input.get_pressed_cap("dpad"):
                    self.y_sel = min(len(self.y_items) - 1, self.y_sel + 1)
                    self.dirty = True

                if cos.input.was_pressed_cap("action", "B"):
                    self.close_y_menu()

                if cos.input.was_pressed_cap("action", "A"):

                    choice = self.y_items[self.y_sel]
                    
                    if choice == "New File":
                        result = self.create_file()
                        if result:
                            yield from result
                    elif choice == "New Folder":
                        result = self.create_folder()
                        if result:
                            yield from result
                    elif choice == "Paste":
                        self.paste()
                    elif choice == "Refresh":
                        self.refresh()

                    self.close_y_menu()
                    
            if self.dirty:
                self.draw()
                yield cos.intent.INTENT_DRAW

            yield cos.intent.INTENT_NO_OP


if __name__ == "__main__":
    kernal.run(App)