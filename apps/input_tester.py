import core.kernal as kernal

class App:
    def __init__(self,cos):
        self.cos = cos

    def setup(self):
        #self.cos.input.clear_claims()
        #self.cos.input.claim_caps(['action','dpad'])
        pass

    
    def run(self):
        cos = self.cos
        
        while True:
            cos.gfx.smart_text(f'dpad{cos.input.get_cap('dpad')}', 0, 0, (255,255,255))
            cos.gfx.smart_text(f'action{cos.input.get_cap('action')}', 0, 10, (255,255,255))
            cos.gfx.smart_text(f'touchpad{cos.input.get_cap('touchpad')}', 0, 20, (255,255,255))
            yield cos.intent.INTENT_DRAW
            
if __name__ == "__main__":
    kernal.run(App)