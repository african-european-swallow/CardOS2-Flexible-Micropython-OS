# core/taskbar.py

import gc


class TaskBar:
    def __init__(self, cos):
        self.cos = cos

        self.providers = {
            "mem": self.mem,
            "bat": self.bat,
            "app": self.app,
            "fps": self.get_fps,
        }
        self.bar_color = tuple(self.cos.settings.get("dis.taskbar_color", [150,150,150]))
        self.text_color = tuple(self.cos.settings.get("dis.taskbar_text_color", [255,255,255]))

    def mem(self):
        gc.collect()

        free = gc.mem_free()
        total = free + gc.mem_alloc()

        used = 100 - (free * 100 / total)
        return "mem:{:.2f}%".format(used)
    
    def get_fps(self):
        return "fps:{:.1f}".format(self.cos.fps)

    def bat(self):
        value = self.cos.input.get_sensor("battery")

        if value is None or 'battery' not in self.cos.input.get_active_capabilities():
            return "bat: --%"

        return f"bat:{value[0]:.1f}"

    def app(self):
        name = self.cos.running_app_name

        if not name:
            return "app: none"

        return 'app:' + name.split(".")[-1]

    def draw(self):
        gfx = self.cos.gfx

        height = int(
            self.cos.settings.get("dis.status_bar_height", 10)
        )

        y = gfx.screen_y - height

        gfx.rect(0,y,gfx.screen_x,height,self.bar_color,True)

        items = self.cos.settings.get("dis.info", [])

        values = []

        for item in items:
            provider = self.providers.get(item)

            if provider:
                try:
                    values.append(provider())
                except:
                    values.append(f"{provider}: ?")

        text = "|".join(values)

        txt_scale = 1
        text_height = txt_scale * 8

        text_y = (gfx.screen_y- ((height - text_height) // 2)- text_height)

        gfx.text(text,2,text_y,self.text_color,font=self.cos.normal_font)