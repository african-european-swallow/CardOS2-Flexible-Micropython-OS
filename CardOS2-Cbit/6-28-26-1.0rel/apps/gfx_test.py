import core.kernal as kernal
import time

class App:
    def __init__(self, cos):
        self.cos = cos
        self.test_id = 0
        self.tests = []

    def setup(self):
        cos = self.cos

        # Start in segmented mode
        cos.gfx.set_mode(full_fb=False, auto_clear=True)

        # --- define all tests---
        self.tests = [
            self.test_fill,
            self.test_fill_usable,
            self.test_pixel,
            self.test_lines,
            self.test_rect,
            self.test_ellipse,
            self.test_poly,
            self.test_text,
            self.test_smart_text,
            self.test_scroll,
        ]

    # --------------------------
    # TESTS
    # --------------------------
    def test_fill(self):
        self.cos.gfx.fill((0, 0, 100))

    def test_fill_usable(self):
        self.cos.gfx.fill_usable((0, 100, 0))

    def test_pixel(self):
        for i in range(0, 128, 4):
            self.cos.gfx.pixel(i, i, (255, 255, 0))

    def test_lines(self):
        g = self.cos.gfx
        g.hline(10, 20, 100, (255, 0, 0))
        g.vline(20, 10, 100, (0, 255, 0))
        g.line(0, 0, 127, 127, (0, 0, 255))

    def test_rect(self):
        g = self.cos.gfx
        g.rect(10, 10, 50, 30, (255, 0, 0), False)
        g.rect(70, 20, 40, 40, (0, 255, 0), True)

    def test_ellipse(self):
        g = self.cos.gfx
        g.ellipse(64, 64, 30, 20, (255, 255, 0), False)
        g.ellipse(64, 64, 10, 10, (0, 255, 255), True)

    def test_poly(self):
        g = self.cos.gfx
        coords = [0,0,  20,0,  10,20]
        g.poly(0, 0, coords, (255, 0, 255), True)

    def test_text(self):
        g = self.cos.gfx
        g.text("Text", 10, 10, (255, 255, 255))
        g.text("BIG", 10, 30,(255, 200, 0),font="large")

    def test_smart_text(self):
        g = self.cos.gfx
        g.smart_text(
            "This is a long string that should wrap nicely across the screen.",
            0, 0,
            (200, 200, 200),
            font='normal'
        )

    def test_scroll(self):
        g = self.cos.gfx
        g.fill((0, 0, 0))
        g.text("Scrolling...", 10, 50, (255, 255, 255))
        g.scroll(2, 0)

    # --------------------------
    # MAIN LOOP
    # --------------------------
    def run(self):
        cos = self.cos

        while True:
            #dpad = cos.input.get_cap("dpad")
            num = cos.input.get_cap("numpad")

            # --------------------------
            # Switch tests
            # --------------------------
            if cos.input.was_pressed_cap('dpad', 'RIGHT'):
                self.test_id = (self.test_id + 1) % len(self.tests)

            if cos.input.was_pressed_cap('dpad', 'LEFT'):
                self.test_id = (self.test_id - 1) % len(self.tests)

            # --------------------------
            # Switch modes
            # --------------------------
            if '1' in num:
                cos.gfx.set_mode(full_fb=False, auto_clear=True)

            elif '2' in num:
                cos.gfx.set_mode(full_fb=True)

            elif '3' in num:
                cos.gfx.set_mode(full_fb=False, auto_clear=False)

            # --------------------------
            # Clear screen
            # --------------------------
            cos.gfx.fill((0, 0, 0))

            # --------------------------
            # Run current test
            # --------------------------
            self.tests[self.test_id]()

            # Label
            cos.gfx.text(
                "Test: " + str(self.test_id),
                0, 120,
                (255, 255, 255)
            )
            yield cos.intent.INTENT_DRAW

if __name__=="__main__":
    kernal.run(App)