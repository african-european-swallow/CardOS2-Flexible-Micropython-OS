from machine import Pin, SPI
#from ssd1351_lite import Display
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
        self.queue = []
        self.dirty = [True] * (self.segx * self.segy)

        # --- misc ---
        self.use_h = self.screen_y - int(settings.get('dis.status_bar_height', 0)) if settings.get('dis.status_bar', False) else self.screen_y
        self.use_w = self.screen_x
        self.error = None
        
        rotate_func = settings.get("dis.rotate_function", None)

        if rotate_func:
            amount = int(settings.get("dis.rotate_amount", 0))
            getattr(self.display, rotate_func)(amount)


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
        """

        settings = self.settings
        gc.collect()

        old_screen_x = self.screen_x
        old_screen_y = self.screen_y

        # -------------------------
        # Update virtual dimensions
        # -------------------------

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

        # -------------------------
        # Update settings
        # -------------------------

        if auto_clear is not None:
            self.auto_clear = auto_clear

        if full_fb is not None:
            if full_fb and not settings.get("dis.full_fb", True):
                return False

            self.full_fb = full_fb

        # -------------------------
        # Determine segmentation
        # -------------------------

        if self.full_fb:
            segx, segy = 1, 1

        elif segment is not None:
            segx = max(1, int(segment[0]))
            segy = max(1, int(segment[1]))

        else:
            segx = self.OGsegx
            segy = self.OGsegy

        # Round framebuffer dimensions to even numbers
        segw = ((self.screen_x + 1) // 2 * 2) // segx
        segh = ((self.screen_y + 1) // 2 * 2) // segy

        new_size = segw * segh * 2

        # -------------------------
        # Allocate framebuffer
        # -------------------------

        try:
            buf = bytearray(new_size)

            fb = framebuf2.FrameBuffer(
                buf,
                segw,
                segh,
                framebuf2.RGB565
            )

        except MemoryError:

            gc.collect()

            # Restore previous dimensions
            self.screen_x = old_screen_x
            self.screen_y = old_screen_y

            self.full_fb = False

            segx = self.OGsegx
            segy = self.OGsegy

            segw = ((self.screen_x + 1) // 2 * 2) // segx
            segh = ((self.screen_y + 1) // 2 * 2) // segy

            new_size = segw * segh * 2

            try:
                buf = bytearray(new_size)

                fb = framebuf2.FrameBuffer(
                    buf,
                    segw,
                    segh,
                    framebuf2.RGB565
                )

            except MemoryError:
                gc.collect()
                return False

        # -------------------------
        # Commit changes
        # -------------------------

        self.buf = buf
        self.fb = fb

        self.segx = segx
        self.segy = segy

        self.seg_width = segw
        self.seg_height = segh

        self.queue.clear()
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

    # --------------------------
    # Queue helper (precompute color)
    # --------------------------
    def _c(self, color):
        return self.color565(*color) if isinstance(color, tuple) else color

    # --------------------------
    # API
    # --------------------------
    def fill(self, color):
        self.queue.append([CMD_FILL, self._c(color)])
        self.mark_all_dirty()

    def fill_usable(self, color):
        self.queue.append((CMD_RECT, 0, 0, self.use_w, self.use_h, self._c(color), True))
        self.mark_dirty_rect(-1, -1, self.use_w+2, self.use_h+2)

    def pixel(self, x, y, color):
        self.queue.append((CMD_PIXEL, x, y, self._c(color)))
        self.mark_dirty(x, y)

    def hline(self, x, y, w, color):
        self.queue.append((CMD_HLINE, x, y, w, self._c(color)))
        self.mark_dirty_rect(x, y, w, 1)

    def vline(self, x, y, h, color):
        self.queue.append((CMD_VLINE, x, y, h, self._c(color)))
        self.mark_dirty_rect(x, y, 1, h)

    def line(self, x1, y1, x2, y2, color):
        self.queue.append((CMD_LINE, x1, y1, x2, y2, self._c(color)))
        self.mark_dirty_rect(min(x1,x2), min(y1,y2), abs(x2-x1)+1, abs(y2-y1)+1)

    def rect(self, x, y, w, h, color, f=False):
        self.queue.append((CMD_RECT, x, y, w, h, self._c(color), f))
        self.mark_dirty_rect(x-1, y-1, w+2, h+2)

    def ellipse(self, x, y, xr, yr, color, f=False, m=None):
        self.queue.append((CMD_ELLIPSE, x, y, xr, yr, self._c(color), f))
        self.mark_dirty_rect(x-xr, y-yr, xr*2, yr*2)

    def poly(self, x, y, coords, color, f=False):
        arr = array('h', coords)
        self.queue.append((CMD_POLY, x, y, arr, self._c(color), f))

        xs = [coords[i] + x for i in range(0, len(coords), 2)]
        ys = [coords[i] + y for i in range(1, len(coords), 2)]
        self.mark_dirty_rect(min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys))

    def text(self, stri, x, y, color, s=1):
        self.queue.append((CMD_TEXT, stri, x, y, s, self._c(color)))
        self.mark_dirty_rect(x, y, len(stri)*8*s, 8*s)

    def large_text(self, stri, x, y, s, color):
        self.text(stri, x, y, color, s)

    def smart_text(self, string, x, y, color, end=None, s=1, return_spacing=2):
        if end is None:
            end = self.screen_x  # absolute screen edge
    
        chars = list(str(string))
        char_w = 8 * s
        char_h = 8 * s
    
        # Ensure at least one character fits
        if end - x < char_w:
            end = x + char_w
    
        y_offset = 0
    
        while chars:
            line = []
            width = 0
    
            while chars and x + width + char_w <= end:
                if len(chars) >= 2 and chars[0] == '\\' and chars[1] == 'n':
                    chars.pop(0); chars.pop(0)
                    break
                line.append(chars.pop(0))
                width += char_w
    
            line = ''.join(line)
            self.text(line, x, y + y_offset, color, s)
            y_offset += char_h + return_spacing
        
    def scroll(self, xstep, ystep):
        self.queue.append((CMD_SCROLL, xstep, ystep))
        self.mark_all_dirty()

    def blit(self, fbuf, x, y, key=-1, palette=None):
        self.queue.append((CMD_BLIT, fbuf, x, y, key, palette))
        self.mark_dirty_rect(x, y, fbuf.width, fbuf.height)

    # --------------------------
    # DRAW
    # --------------------------
    @micropython.native
    def draw(self):
        fb = self.fb
        queue = self.queue
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

        for seg_idx in range(len(self.dirty)):
            if not self.dirty[seg_idx]:
                continue

            sx = seg_idx % self.segx
            sy = seg_idx // self.segx

            x_off = sx * self.seg_width
            y_off = sy * self.seg_height

            if self.auto_clear: #or self.full_fb
                fill(0)
                
            try:
                for q in queue:
                    cmd = q[0]

                    if cmd == CMD_FILL:
                        fill(q[1])

                    elif cmd == CMD_PIXEL:
                        pixel(q[1]-x_off, q[2]-y_off, q[3])

                    elif cmd == CMD_HLINE:
                        hline(q[1]-x_off, q[2]-y_off, q[3], q[4])

                    elif cmd == CMD_VLINE:
                        vline(q[1]-x_off, q[2]-y_off, q[3], q[4])

                    elif cmd == CMD_LINE:
                        line(q[1]-x_off, q[2]-y_off, q[3]-x_off, q[4]-y_off, q[5])

                    elif cmd == CMD_RECT:
                        rect(q[1]-x_off, q[2]-y_off, q[3], q[4], q[5], q[6])

                    elif cmd == CMD_ELLIPSE:
                        ellipse(q[1]-x_off, q[2]-y_off, q[3], q[4], q[5], q[6])

                    elif cmd == CMD_POLY:
                        poly(q[1]-x_off, q[2]-y_off, q[3], q[4], q[5])

                    elif cmd == CMD_TEXT:
                        if q[4] == 1:
                            text(q[1], q[2]-x_off, q[3]-y_off, q[5])
                        else:
                            large_text(q[1], q[2]-x_off, q[3]-y_off, q[4], q[5])

                    elif cmd == CMD_SCROLL:
                        scroll(q[1], q[2])

                    elif cmd == CMD_BLIT:
                        blit(q[1], q[2]-x_off, q[3]-y_off, q[4], q[5])

            except Exception as e:
                if self.error:
                    self.error.report('GFX', 'DRAW ERROR', exc=e, level="error")

            #disp.blit_buffer(self.buf, x_off, y_off, self.seg_width, self.seg_height)
            push_method(self.buf, x_off, y_off, self.seg_width, self.seg_height)
            self.dirty[seg_idx] = False

        self.queue.cle



