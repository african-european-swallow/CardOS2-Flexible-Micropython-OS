
class Driver:
    CAPABILITIES = ["quit"]
    I2C_SUPPORT = ["internal", "external"]

    def __init__(self):
        self.present = False

    def set_ctx(self, ctx):
        self.ctx = ctx
        
    # =========================
    # CONNECT
    # =========================
    def connect(self, settings=None):
        self.present = True
        return

    def get(self, cap=None):
        if not self.present:
            return []

        if cap == "quit":
            if set(self.ctx.input.get_cap('touchpad')) == set(['0','6','7']) or set(self.ctx.input.get_cap('action')) == set(['A','START','SELECT']):
                self.ctx.app_intent_overide = self.ctx.intent.INTENT_KILL_APP
                self.ctx.active_task = None
                self.ctx.active_task_name = None
                return [True]

        return []