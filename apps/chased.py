import core.kernal as kernal
import random

class App:
    def __init__(self, cos):
        self.cos = cos

    def setup(self):
        self.reset()

    def reset(self):
        self.x = 64
        self.y = 64

        self.enemies = []  # [x, y, vx, vy]
        self.spawn_timer = 0

        self.score = 0
        self.dead = False

        # dash
        self.dash_timer = 0
        self.dash_cooldown = 0

    def spawn_enemy(self):
        edge = random.randint(0, 3)

        if edge == 0:   # top
            x, y = random.randint(0, 128), 0
        elif edge == 1: # bottom
            x, y = random.randint(0, 128), 128
        elif edge == 2: # left
            x, y = 0, random.randint(0, 128)
        else:           # right
            x, y = 128, random.randint(0, 128)

        self.enemies.append([x, y, 0, 0])

    def run(self):
        cos = self.cos

        while True:
            keys = cos.input.get_cap("dpad")
            # =====================
            # INPUT
            # =====================
            speed = 2

            if self.dash_timer > 0:
                speed = 8
                self.dash_timer -= 1

            if self.dash_cooldown > 0:
                self.dash_cooldown -= 1

            if not self.dead:
                if "LEFT" in keys: self.x -= speed
                if "RIGHT" in keys: self.x += speed
                if "UP" in keys: self.y -= speed
                if "DOWN" in keys: self.y += speed

                if (cos.input.was_pressed_cap("touchpad", "1")) and self.dash_cooldown == 0:
                    self.dash_timer = 10
                    self.dash_cooldown = 40

            # clamp
            if self.x < 0: self.x = 0
            if self.x > 118: self.x = 118
            if self.y < 0: self.y = 0
            if self.y > 118: self.y = 118

            # restart
            if self.dead and cos.input.was_pressed_cap("dpad", "CENTER"):
                self.reset()

            # =====================
            # GAME LOGIC
            # =====================
            if not self.dead:
                self.score += 1
                self.spawn_timer += 1

                # spawn enemies
                if self.spawn_timer > 50:
                    self.spawn_timer = 0
                    self.spawn_enemy()

                # move enemies toward player
                new_enemies = []
                for ex, ey, vx, vy in self.enemies:
                    dx = self.x - ex
                    dy = self.y - ey

                    # normalize-ish (cheap)
                    if dx > 0: vx = 1
                    elif dx < 0: vx = -1
                    else: vx = 0

                    if dy > 0: vy = 1
                    elif dy < 0: vy = -1
                    else: vy = 0

                    # speed scales with score
                    ex += vx * (1 + self.score // 300)
                    ey += vy * (1 + self.score // 300)

                    # collision (unless dashing)
                    if self.dash_timer == 0:
                        if (
                            ex < self.x + 10 and
                            ex + 10 > self.x and
                            ey < self.y + 10 and
                            ey + 10 > self.y
                        ):
                            self.dead = True

                    if 0 <= ex <= 128 and 0 <= ey <= 128:
                        new_enemies.append([ex, ey, vx, vy])

                self.enemies = new_enemies

            # =====================
            # DRAW
            # =====================
            cos.gfx.fill((0,0,0))

            # player
            color = (0,255,255) if self.dash_timer > 0 else (0,255,0)
            cos.gfx.rect(self.x, self.y, 10, 10, color, True)

            # enemies
            for ex, ey, _, _ in self.enemies:
                cos.gfx.rect(ex, ey, 10, 10, (255,0,0), True)

            # UI
            cos.gfx.text("S:" + str(self.score), 0, 0, (255,255,255))
            cos.gfx.text("D:" + str(self.dash_cooldown), 70, 0, (200,200,255))

            if self.dead:
                cos.gfx.text("GAME OVER", 20, 50, (255,0,0))
                cos.gfx.text("CENTER=retry", 10, 70, (255,255,255))

            yield cos.intent.INTENT_DRAW


if __name__ == "__main__":
    kernal.run(App)