import core.kernal as kernal
import random

class App:
    def __init__(self, cos):
        self.cos = cos

    def setup(self):
        self.reset()

    def reset(self):
        self.player_x = 60
        self.player_y = 110

        self.blocks = []  # [x, y, speed]
        self.spawn_timer = 0

        self.score = 0
        self.speed = 1

        self.dead = False

    def spawn_block(self):
        x = random.randint(0, 118)
        speed = random.randint(1, 3) + self.speed
        self.blocks.append([x, 0, speed])

    def run(self):
        cos = self.cos

        while True:
            keys = cos.input.get_cap("dpad")

            # =====================
            # INPUT
            # =====================
            if not self.dead:
                if "LEFT" in keys:
                    self.player_x -= 3
                if "RIGHT" in keys:
                    self.player_x += 3

            # Clamp player
            if self.player_x < 0: self.player_x = 0
            if self.player_x > 118: self.player_x = 118

            # Restart on death
            if self.dead and cos.input.was_pressed_cap("dpad", "CENTER"):
                self.reset()

            # =====================
            # GAME LOGIC
            # =====================
            if not self.dead:
                self.spawn_timer += 1
                self.score += 1

                # Increase difficulty
                if self.score % 200 == 0:
                    self.speed += 1

                # Spawn blocks
                if self.spawn_timer > 20:
                    self.spawn_timer = 0
                    self.spawn_block()

                # Move blocks
                new_blocks = []
                for bx, by, bs in self.blocks:
                    by += bs

                    # Collision
                    if (
                        bx < self.player_x + 10 and
                        bx + 10 > self.player_x and
                        by < self.player_y + 10 and
                        by + 10 > self.player_y
                    ):
                        self.dead = True

                    if by < 128:
                        new_blocks.append([bx, by, bs])

                self.blocks = new_blocks

            # =====================
            # DRAW
            # =====================
            cos.gfx.fill((0, 0, 0))

            # Player
            cos.gfx.rect(self.player_x, self.player_y, 10, 10, (0, 255, 0), True)

            # Blocks
            for bx, by, _ in self.blocks:
                cos.gfx.rect(bx, by, 10, 10, (255, 0, 0), True)

            # Score
            cos.gfx.text("Score: " + str(self.score), 0, 0, (255, 255, 255))

            # Death screen
            if self.dead:
                cos.gfx.text("GAME OVER", 20, 50, (255, 0, 0))
                cos.gfx.text("Press CENTER", 10, 70, (255, 255, 255))

            yield cos.intent.INTENT_DRAW


if __name__ == "__main__":
    kernal.run(App)