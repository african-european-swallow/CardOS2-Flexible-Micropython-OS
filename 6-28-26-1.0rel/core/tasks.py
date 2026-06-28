# core/tasks.py

def get_text(cos,prompt='',current=''):
    content = current
    pre_claim = cos.input.get_claims()
    available = cos.input.get_active_capabilities()
    # =========================
    # MODE DETECTION
    # =========================
    mode = None
    cos.input.clear_claims()
    if "keyboard" in available:
        cos.input.claim_caps(['keyboard'])
        mode = 1
    elif "touchpad" in available and "dpad" in available:
        cos.input.claim_caps(['touchpad','dpad'])
        mode = 2
    elif "dpad" in available:
        cos.input.claim_caps(['dpad','action'])
        mode = 3
    else:
        cos.gfx.fill((0, 0, 0))
        cos.gfx.text("NO INPUT", 0, 0, (255, 0, 0),font=cos.normal_font)
        cos.gfx.draw()
        cos.input.claim_caps(pre_claim)
        return False, None
    cos.input.update()
    cos.input.get_pressed_cap("touchpad")
    cos.input.update()

    w = int(cos.use_w)
    h = int(cos.use_h)

    kb_pages = [
        ['q','w','e','a','s','d','z','x','c',' ','DEL','ENT'],
        ['r','t','y','f','g','h','v','b','n',' ','DEL','ENT'],
        ['u','i','o','j','k','l','m',',','.',' ','DEL','ENT'],
        ['p','[',']','{','}',';',':',"'",'"',' ','DEL','ENT'],
        ['`','~','!','@','#','$','%','^','&',' ','DEL','ENT'],
        ['*','(',')','_','-','+','=','|','\\',' ','DEL','ENT'],
        ['/','?','<',',','>','.','\\','n','\t',' ','DEL','ENT'],
        ['7','8','9','4','5','6','1','2','3','0','.','DEL'],
    ]

    page = 0
    index = 0

    # =========================
    # MODIFIERS
    # =========================
    caps = False
    shift = False

    def touch_to_index(nk):
        i = int(nk)
        row = i // 3
        col = i % 3
        row = 3 - row
        return row * 3 + col

    # =========================
    # DISPLAY HELPERS
    # =========================
    def display_key(k):
        if k == "DEL":
            return "D"
        if k == "ENT":
            return "E"
        if k == "\t":
            return "T"
        return k

    def apply_case(k):
        nonlocal caps, shift

        if len(k) == 1 and k.isalpha():
            if caps or shift:
                k = k.upper()

        shift = False
        return k

    while True:

        # =========================
        # MODE 1 (keyboard)
        # =========================
        if mode == 1:
            keys = cos.input.get_pressed_cap("keyboard")

            if keys:
                if not isinstance(keys, (list, tuple)):
                    keys = [keys]

                for k in keys:
                    if k in ("ENTER", "RETURN"):
                        cos.input.claim_caps(pre_claim)
                        yield True, content

                    elif k in ("BACKSPACE", "BKSP"):
                        content = content[:-1]
                    elif k in ("SPACE"):
                        content += ' '

                    else:
                        content += str(k)

        # =========================
        # MODE 2 (touchpad + dpad)
        # =========================
        elif mode == 2:
            dpad = cos.input.get_pressed_cap("dpad")
            numpad = cos.input.get_pressed_cap("touchpad")

            if 'LEFT' in dpad:
                page = (page - 1) % len(kb_pages)

            if 'RIGHT' in dpad:
                page = (page + 1) % len(kb_pages)

            # =========================
            # MODIFIERS
            # =========================
            if 'UP' in dpad:
                caps = not caps

            if 'DOWN' in dpad:
                shift = True

            if 'CENTER' in dpad:
                cos.input.claim_caps(pre_claim)
                yield True, content

            if numpad:
                if not isinstance(numpad, (list, tuple)):
                    numpad = [numpad]

                for nk in numpad:
                    try:
                        idx = touch_to_index(nk)
                    except:
                        continue

                    key = kb_pages[page][idx]

                    if key == "DEL":
                        content = content[:-1]

                    elif key == "ENT":
                        cos.input.claim_caps(pre_claim)
                        yield True, content

                    elif key == "\t":
                        content += "    "

                    else:
                        key = apply_case(key)
                        content += key

        # =========================
        # MODE 3 (dpad + action)
        # =========================
        elif mode == 3:
            dpad = cos.input.get_pressed_cap("dpad")
            action = cos.input.get_pressed_cap('action')

            if 'LEFT' in dpad:
                if index % 3 != 0:
                    index -= 1
                else:
                    page = (page - 1) % len(kb_pages)
                    index += 2

            if 'RIGHT' in dpad:
                if index % 3 != 2:
                    index += 1
                else:
                    page = (page + 1) % len(kb_pages)
                    index -= 2

            if 'CENTER' in dpad or 'A' in action:
                key = kb_pages[page][index]

                if key == "DEL":
                    content = content[:-1]

                elif key == "ENT":
                    cos.input.claim_caps(pre_claim)
                    yield True, content

                elif key == "\t":
                    content += "    "

                else:
                    key = apply_case(key)
                    content += key

            # navigation
            if 'UP' in dpad:
                index = (index - 3) % 12
            if 'DOWN' in dpad:
                index = (index + 3) % 12
                
                
            if 'X' in action:
                caps = not caps
            if 'START' in action:
                cos.input.claim_caps(pre_claim)
                yield True, content
            if 'B' in action:
                content = content[:-1]
            if 'Y' in action:
                content += ' '

        # =========================
        # UI
        # =========================
        cos.gfx.fill((0, 0, 0))

        # text output
        cos.gfx.smart_text(prompt+content, 0, 0, (0, 255, 0),font=cos.normal_font)

        # =========================
        # MODIFIER DISPLAY
        # =========================
        mod_text = ""
        if caps:
            mod_text += "[CAPS] "
        if shift:
            mod_text += "[SHIFT] "

        cos.gfx.text(mod_text, 0, 10, (255, 255, 0),font=cos.normal_font)

        # =========================
        # KEYBOARD GRID
        # =========================
        keys = kb_pages[page]

        kb_y_start = h // 2
        kb_h = h - kb_y_start

        cell_w = w // 3
        cell_h = kb_h // 4

        for i, k in enumerate(keys):
            col = i % 3
            row = i // 3

            x = col * cell_w + 2
            y = kb_y_start + row * cell_h + 2

            color = (255, 255, 255)
            if mode == 3 and i == index:
                color = (255, 0, 0)

            cos.gfx.text(display_key(k), x, y, color,font=cos.normal_font)

        yield False, None