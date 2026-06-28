# core/gfx.py

from machine import Pin, SPI
import framebuf2
from array import array
import gc
import math

# --------------------------
# Command constants
# --------------------------
CMD_FILL = 0
CMD_PIXEL = 1
CMD_HLINE = 2
CMD_VLINE = 3
CMD_LINE = 4
CMD_RECT = 5
CMD_ELLIPSE = 6
CMD_POLY = 7
CMD_TEXT = 8
CMD_SCROLL = 9
CMD_BLIT = 10

FONT_SMALL = 0
FONT_NORMAL = 1
FONT_LARGE = 2
FONT_TITLE = 3


class Gfx:
    def __init__(self, settings):
        self.settings = settings
        
        # --- mode ---
        self.auto_clear = settings.get("dis.auto_clear", True)
        self.full_fb = settings.get("dis.full_fb", False)

        self.OGsegx = int(settings.get("dis.segx", 2))
        self.OGsegy = int(settings.get("dis.segy", 2))

        self.screen_x = int(settings.get("dis.x", 128))
        self.screen_y = int(settings.get("dis.y", 128))

        # --- segmentation logic ---
        if self.full_fb:
            self.segx = 1
            self.segy = 1
        elif self.auto_clear:
            self.segx = self.OGsegx
            self.segy = self.OGsegy
        else:
            self.segx = 1
            self.segy = 1

        self.seg_width = math.ceil(self.screen_x / 2.) * 2 // self.segx
        self.seg_height = math.ceil(self.screen_y / 2.) * 2 // self.segy

        # --- SPI ---
        spi = SPI(
            int(settings.get("dis.spi_bus", 2)),
            baudrate=int(settings.get("dis.spi_baud", 20000000)),
            sck=Pin(int(settings.get("dis.sck", 36))),
            mosi=Pin(int(settings.get("dis.mosi", 35)))
        )
        Display = __import__(settings.get('dis.lib','lib.ssd1351_lite'), None, None, [None])
        Display = getattr(Display,str(settings.get('dis.class','Display')))
        
        self.display = Display(
            spi,
            dc=Pin(int(settings.get("dis.dc", 14))),
            cs=Pin(int(settings.get("dis.cs", 8))),
            rst=Pin(int(settings.get("dis.rst", 15)))
        )
        self.push_method = getattr(self.display,str(settings.get('dis.push_method','blit_buffer')))
        # --- framebuffer ---
        size = self.seg_width * self.seg_height * 2
        self.buf = bytearray(size)

        self.fb = framebuf2.FrameBuffer(
            self.buf,
            self.seg_width,
            self.seg_height,
            framebuf2.RGB565
        )

        # --- queues ---
        self.MAX_QUEUE = 1024
        self.queue = [None] * self.MAX_QUEUE
        self.q_len = 0
        self.dirty = [True] * (self.segx * self.segy)

        # --- misc ---
        self.use_h = self.screen_y - int(settings.get('dis.status_bar_height', 0)) if settings.get('dis.status_bar', False) else self.screen_y
        self.use_w = self.screen_x
        self.error = None
        
        rotate_func = settings.get("dis.rotate_function", None)

        if rotate_func:
            amount = int(settings.get("dis.rotate_amount", 0))
            getattr(self.display, rotate_func)(amount)
        
        self.fonts = {
            FONT_SMALL: {
                "scale": 1,
                "w": 8,
                "h": 8,
            },
            FONT_NORMAL: {
                "scale": 1,
                "w": 8,
                "h": 8,
            },
            FONT_LARGE: {
                "scale": 2,
                "w": 8 * 2,
                "h": 8 * 2,
            },
            FONT_TITLE: {
                "scale": 3,
                "w": 8 * 3,
                "h": 8 * 3,
            },
        }

        self.current_font = FONT_NORMAL

  
    def set_mode(self,full_fb=None,auto_clear=None,segment=None,set_dimensions=None,set_percent=None):
        """
        Dynamically switch rendering mode.

        full_fb:
            True = full framebuffer mode

        auto_clear:
            True = clear framebuffer before redraw

        segment:
            (segx, segy) manual segmentation

        set_dimensions:
            (x, y) virtual screen size

        set_percent:
            Scale virtual screen size as percentage
            of physical display (100 = full size)
            
        stupid heap fragmentation!
        """

        settings = self.settings
        gc.collect()

        allow_switching = settings.get("dis.allow_framebuf_switching", True)

        old_screen_x = self.screen_x
        old_screen_y = self.screen_y

        # =========================================================
        # HARD SAFETY GATE
        # =========================================================
        if not allow_switching:
            # ONLY safe metadata updates

            if auto_clear is not None:
                self.auto_clear = auto_clear

            if full_fb is not None:
                if full_fb and not settings.get("dis.full_fb", True):
                    return False
                self.full_fb = full_fb

            # ignore EVERYTHING that triggers framebuffer rebuild
            return True

        # =========================================================
        # NORMAL MODE 
        # =========================================================

        if set_dimensions is not None:
            if len(set_dimensions) == 2:
                self.screen_x = max(1, int(set_dimensions[0]))
                self.screen_y = max(1, int(set_dimensions[1]))

        elif set_percent is not None:
            base_x = int(settings.get("dis.x", 128))
            base_y = int(settings.get("dis.y", 128))

            pct = max(1, int(set_percent))

            self.screen_x = max(1, base_x * pct // 100)
            self.screen_y = max(1, base_y * pct // 100)

        if auto_clear is not None:
            self.auto_clear = auto_clear

        if full_fb is not None:
            if full_fb and not settings.get("dis.full_fb", True):
                return False
            self.full_fb = full_fb

        if self.full_fb:
            segx, segy = 1, 1
        elif segment is not None:
            segx = max(1, int(segment[0]))
            segy = max(1, int(segment[1]))
        else:
            segx = self.OGsegx
            segy = self.OGsegy

        segw = ((self.screen_x + 1) // 2 * 2) // segx
        segh = ((self.screen_y + 1) // 2 * 2) // segy

        new_size = segw * segh * 2

        try:
            buf = bytearray(new_size)

            fb = framebuf2.FrameBuffer(buf,segw,segh,framebuf2.RGB565)

        except MemoryError:
            gc.collect()

            self.screen_x = old_screen_x
            self.screen_y = old_screen_y
            self.full_fb = False

            segx = self.OGsegx
            segy = self.OGsegy

            segw = ((self.screen_x + 1) // 2 * 2) // segx
            segh = ((self.screen_y + 1) // 2 * 2) // segy

            try:
                buf = bytearray(segw * segh * 2)
                fb = framebuf2.FrameBuffer(buf, segw, segh, framebuf2.RGB565)
            except MemoryError:
                gc.collect()
                return False

        self.buf = buf
        self.fb = fb

        self.segx = segx
        self.segy = segy
        self.seg_width = segw
        self.seg_height = segh

        self.q_len = 0
        self.dirty = [True] * (segx * segy)

        gc.collect()
        return True
        
    # --------------------------
    # Color
    # --------------------------
    def color565(self, r, g, b):
        return (b & 0xf8) << 8 | (r & 0xfc) << 3 | g >> 3

    # --------------------------
    # Dirty helpers
    # --------------------------
    def mark_dirty(self, x, y):
        if 0 <= x < self.screen_x and 0 <= y < self.screen_y:
            sx = x // self.seg_width
            sy = y // self.seg_height
            self.dirty[sy * self.segx + sx] = True

    def mark_all_dirty(self):
        for i in range(len(self.dirty)):
            self.dirty[i] = True
    @micropython.native
    def mark_dirty_rect(self, x, y, w, h):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.screen_x - 1, x + w - 1)
        y1 = min(self.screen_y - 1, y + h - 1)

        sx0 = x0 // self.seg_width
        sy0 = y0 // self.seg_height
        sx1 = x1 // self.seg_width
        sy1 = y1 // self.seg_height

        for sy in range(sy0, sy1 + 1):
            base = sy * self.segx
            for sx in range(sx0, sx1 + 1):
                self.dirty[base + sx] = True
                
    @micropython.native
    def _intersects(self, sx, sy, x0, y0, x1, y1):
        sx0 = sx * self.seg_width
        sy0 = sy * self.seg_height
        sx1 = sx0 + self.seg_width
        sy1 = sy0 + self.seg_height

        return not (
            x1 < sx0 or x0 > sx1 or
            y1 < sy0 or y0 > sy1
        )
    
    def q_add(self, cmd):
        i = self.q_len
        if i >= self.MAX_QUEUE:
            return 

        self.queue[i] = cmd
        self.q_len = i + 1
        
    def hard_queue_clear(self):
        for i in range(self.q_len):
            self.queue[i] = None
        self.q_len = 0
        gc.collect()
    # --------------------------
    # Queue helper (precompute color)
    # --------------------------
    def _c(self, color):
        return self.color565(*color) if isinstance(color, tuple) else color

    # --------------------------
    # API
    # --------------------------
    def fill(self, color):
        self.q_add((CMD_FILL, self._c(color)))
        self.mark_all_dirty()

    def fill_usable(self, color):
        self.q_add((CMD_RECT,0, 0, self.use_w, self.use_h, self._c(color), True,0, 0, self.use_w, self.use_h))
        self.mark_dirty_rect(-1, -1, self.use_w+2, self.use_h+2)

    def pixel(self, x, y, color):
        self.q_add((CMD_PIXEL, x, y, self._c(color),x, y, x+1, y+1))
        self.mark_dirty(x, y)

    def hline(self, x, y, w, color):
        self.q_add((CMD_HLINE, x, y, w, self._c(color),x, y, x+w, y+1))
        self.mark_dirty_rect(x, y, w, 1)

    def vline(self, x, y, h, color):
        self.q_add((CMD_VLINE, x, y, h, self._c(color),x, y, x+1, y+h))
        self.mark_dirty_rect(x, y, 1, h)

    def line(self, x1, y1, x2, y2, color):
        self.q_add((CMD_LINE, x1, y1, x2, y2, self._c(color),min(x1, x2), min(y1, y2),max(x1, x2), max(y1, y2)))
        self.mark_dirty_rect(min(x1,x2), min(y1,y2),abs(x2-x1)+1, abs(y2-y1)+1)

    def rect(self, x, y, w, h, color, f=False):
        self.q_add((CMD_RECT, x, y, w, h, self._c(color), f,x, y, x+w, y+h))
        self.mark_dirty_rect(x-1, y-1, w+2, h+2)

    def ellipse(self, x, y, xr, yr, color, f=False, m=None):
        self.q_add((CMD_ELLIPSE, x, y, xr, yr, self._c(color), f,x-xr, y-yr, x+xr, y+yr))
        self.mark_dirty_rect(x-xr, y-yr, xr*2, yr*2)

    def poly(self, x, y, coords, color, f=False):
        arr = array('h', coords)

        minx = maxx = coords[0] + x
        miny = maxy = coords[1] + y

        for i in range(2, len(coords), 2):
            px = coords[i] + x
            py = coords[i + 1] + y

            if px < minx:
                minx = px
            elif px > maxx:
                maxx = px

            if py < miny:
                miny = py
            elif py > maxy:
                maxy = py

        self.q_add((CMD_POLY, x, y, arr, self._c(color), f,minx, miny, maxx, maxy))

        self.mark_dirty_rect(minx,miny,maxx - minx,maxy - miny)

    def text(self, stri, x, y, color, font=None):
        f = self.get_font(font)
        scale = f["scale"]
        w = len(stri) * f["w"]
        h = f["h"]

        self.q_add((CMD_TEXT, stri, x, y, scale,self._c(color),x, y, x + w, y + h))
        self.mark_dirty_rect(x, y, w, h)

    def smart_text(self, string, x, y, color, font=None, end=None, return_spacing=2):
        f = self.get_font(font)

        char_w = f["w"]
        char_h = f["h"]

        s = str(string)
        n = len(s)

        if end is None:
            end = self.screen_x

        if end - x < char_w:
            end = x + char_w

        max_width = end - x

        i = 0
        y_offset = 0

        while i < n:
            start = i
            width = 0

            while i < n:
                # handle "\n"
                if s[i] == '\\' and i + 1 < n and s[i + 1] == 'n':
                    i += 2
                    i = i  # keep index
                    width = max_width  # force line break
                    break

                if width + char_w > max_width:
                    break

                i += 1
                width += char_w

            # direct slice (fast, no build-up structures)
            self.text(s[start:i], x, y + y_offset, color, font)

            y_offset += char_h + return_spacing
            
    def set_font(self, font):
        fonts = {
            "small": FONT_SMALL,
            "normal": FONT_NORMAL,
            "large": FONT_LARGE,
            "title": FONT_TITLE,
        }

        if font in fonts:
            self.current_font = fonts[font]
        else:
            self.current_font = FONT_NORMAL  # safe fallback

    def get_font(self, font=None):
        if font is None:
            font = self.current_font

        if isinstance(font, str):
            font = {
                "small": FONT_SMALL,
                "normal": FONT_NORMAL,
                "large": FONT_LARGE,
                "title": FONT_TITLE,
            }.get(font, FONT_NORMAL)

        return self.fonts.get(font, self.fonts[FONT_NORMAL])

    def font_width(self, font=None):
        return self.get_font(font)["w"]

    def font_height(self, font=None):
        return self.get_font(font)["h"]
        
    def scroll(self, xstep, ystep):
        self.q_add((CMD_SCROLL, xstep, ystep))
        self.mark_all_dirty()

    def blit(self, fbuf, x, y, key=-1, palette=None):
        self.q_add((CMD_BLIT, fbuf, x, y, key, palette,x, y, x+fbuf.width, y+fbuf.height))
        self.mark_dirty_rect(x, y, fbuf.width, fbuf.height)

    # --------------------------
    # DRAW
    # --------------------------
    @micropython.native
    def draw(self):
        fb = self.fb
        queue = self.queue
        q_len = self.q_len
        dirty = self.dirty

        segx = self.segx
        segw = self.seg_width
        segh = self.seg_height

        pixel = fb.pixel
        hline = fb.hline
        vline = fb.vline
        line = fb.line
        rect = fb.rect
        ellipse = fb.ellipse
        text = fb.text
        blit = fb.blit
        scroll = fb.scroll
        fill = fb.fill
        poly = fb.poly
        large_text = fb.large_text

        push_method = self.push_method

        for seg_idx in range(len(dirty)):
            if not dirty[seg_idx]:
                continue

            sx = seg_idx % segx
            sy = seg_idx // segx

            x_off = sx * segw
            y_off = sy * segh

            if self.auto_clear:
                fill(0)

            try:
                for i in range(q_len):
                    q = queue[i]
                    cmd = q[0]

                    # -------------------------
                    # GLOBAL COMMANDS
                    # -------------------------
                    if cmd == CMD_FILL:
                        fill(q[1])
                        continue

                    if cmd == CMD_SCROLL:
                        scroll(q[1], q[2])
                        continue

                    # -------------------------
                    # BOX CULLING 
                    # -------------------------
                    x0 = q[-4]
                    y0 = q[-3]
                    x1 = q[-2]
                    y1 = q[-1]

                    if not self._intersects(sx, sy, x0, y0, x1, y1):
                        continue

                    # -------------------------
                    # DRAW COMMANDS
                    # -------------------------
                    if cmd == CMD_PIXEL:
                        pixel(q[1] - x_off, q[2] - y_off, q[3])


                    elif cmd == CMD_HLINE:
                        hline(q[1] - x_off, q[2] - y_off, q[3], q[4])

                    elif cmd == CMD_VLINE:
                        vline(q[1] - x_off, q[2] - y_off, q[3], q[4])

                    elif cmd == CMD_LINE:
                        line(
                            q[1] - x_off, q[2] - y_off,
                            q[3] - x_off, q[4] - y_off,
                            q[5]
                        )

                    elif cmd == CMD_RECT:
                        rect(q[1] - x_off, q[2] - y_off, q[3], q[4], q[5], q[6])

                    elif cmd == CMD_ELLIPSE:
                        ellipse(q[1] - x_off, q[2] - y_off, q[3], q[4], q[5], q[6])

                    elif cmd == CMD_POLY:
                        poly(q[1] - x_off, q[2] - y_off, q[3], q[4], q[5])

                    elif cmd == CMD_TEXT:
                        scale = q[4]
                        if scale <= 1:
                            text(q[1], q[2] - x_off, q[3] - y_off, q[5])
                        else:
                            large_text(q[1], q[2] - x_off, q[3] - y_off, scale, q[5])

                    elif cmd == CMD_BLIT:
                        blit(q[1], q[2] - x_off, q[3] - y_off, q[4], q[5])

            except Exception as e:
                if self.error:
                    self.error.report('GFX', 'DRAW ERROR', exc=e, level="error")

            push_method(self.buf, x_off, y_off, segw, segh)
            dirty[seg_idx] = False

        self.q_len = 0
