import core.kernal as kernal
        
class App:
    def __init__(self,cos):
        self.cos = cos
        cos.gfx.set_font('normal')

    def setup(self):
        self.cos.input.claim_caps(['touchpad','dpad'])
        
    def run(self):
        cos = self.cos
       
        while True:
          #Do stuff
          
          yield cos.intent.INTENT_DRAW

    def cleanup():
      #OPTIONAL
      #Delete parts of app, kernal does an okay job of deleting the app

#Launch app if it is the launched file, used for testing with an IDE.
if __name__ == "__main__":
    kernal.run(App)
