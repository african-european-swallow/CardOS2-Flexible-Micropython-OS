#intents are used by apps to talk to the os
#inspired by slime_os

INTENT_KILL_APP=[-1]

def INTENT_REPLACE_APP(next_app):
    return [INTENT_KILL_APP[0], next_app]

INTENT_NO_OP=[0]
INTENT_DRAW=[1]
INTENT_TASK=[2]

def INTENT_RUN_TASK(task_name, func, *args, **kwargs):
    return [INTENT_TASK[0], task_name, func, tuple(args), dict(kwargs)]

def is_intent(a, b):
    if len(a) == 0 or len(b) == 0:
        return False
    
    return a[0] == b[0]