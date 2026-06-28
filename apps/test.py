import core.kernal as kernal

def number_input_task(cos):
    value = ""
    pre_claim = cos.input.get_claims()
    cos.input.claim_caps(['touchpad','dpad'])
    while True:
        keys = cos.input.get_pressed_cap("touchpad")

        for k in keys:
            if k.isdigit():
                value += k
        if cos.input.was_pressed_cap('dpad','CENTER'):
            cos.input.claim_caps(pre_claim)
            yield True, value  # DONE

        cos.gfx.fill((0,0,0))
        cos.gfx.text("Enter:", 0, 0, (255,255,255))
        cos.gfx.smart_text(value, 0, 20, (255,255,255))

        yield False, None  # still running
        
class App:
    def __init__(self,cos):
        self.cos = cos

    def setup(self):
        #self.cos.hardware.init(self.cos.settings)
        #self.cos.gfx.set_auto_clear(True)
        self.cos.input.claim_caps(['touchpad','dpad'])
        pass
    def run(self):
        cos = self.cos
        y = 0
        x = 0
        val = None
        while True:
            #self.cos.gfx.text(str(cos.input.get_cap('battery')[0]),0, 10, (0,0,170))
            self.cos.gfx.smart_text(str(x), 0, 0, (200,0,0))
            if "num_input" in cos.task_results:
                val = cos.task_results.pop("num_input")
            if val: self.cos.gfx.smart_text(str(val), 0, 40, (0,255,0))
            reinput = cos.input.get_cap("dpad")
            reeinput = cos.input.get_cap("touchpad")

            if '0' in reeinput:
                self.cos.gfx.set_mode(full_fb=False, auto_clear=True)
            elif '1' in reeinput:
                self.cos.gfx.set_mode(full_fb=True, auto_clear=True)
            elif '2' in reeinput:
                self.cos.gfx.fill(55)
            elif '11' in reeinput:
                yield cos.intent.INTENT_KILL_APP#INTENT_REPLACE_APP({'file':'test_app'})
            if '5' in reeinput:
                cos.run_task("num_input", number_input_task)
            #print(cos.input.get_cap("dpad"))
            if "UP" in reinput:
                y -= 2
            if "DOWN" in reinput:
                y += 2
            if "LEFT" in reinput:
                x -= 2
            if "RIGHT" in reinput:
                x += 2
            
            cos.gfx.rect(x, y, 10, 10, (255,0,0), True)
            yield cos.intent.INTENT_DRAW
            
if __name__ == "__main__":
    kernal.run(App)