import core.kernal as kernal
import math


class App:
    def __init__(self, cos):
        self.cos = cos

        # =========================
        # REQUEST HARDWARE
        # =========================

        cos.input.claim_caps(["dpad","action"])

        # =========================
        # SCREEN SIZE
        # =========================

        self.screen_width = cos.use_w
        self.screen_height = cos.use_h

        # =========================
        # TILES
        # =========================

        self.tile_size = 10

        # =========================
        # LOAD MAP
        # =========================
        self.tilemap = None #moived to setup
        

        # =========================
        # TILE DEFINITIONS
        # =========================

        tile_definitions = {
            "W": {"color": (100, 0, 0), "solid": True,  "type": "floor"},
            "w": {"color": (100, 0, 0), "solid": True,  "type": "floor"},
            ".": {"color": (0, 40, 0), "solid": False, "type": "air"},
            "k": {"color": (255, 0, 0), "solid": False, "type": "kill"},
            "l": {"color": (0, 0, 255), "solid": False, "type": "water"},
        }

        self.TILE_LOOKUP = [{"color": (0, 0, 0), "solid": False, "type": "air"}] * 256

        for k, v in tile_definitions.items():
            self.TILE_LOOKUP[ord(k)] = v


    # =========================================================
    # SETUP
    # =========================================================

    def setup(self):
        self.cos.gfx.set_mode(full_fb=True)
        self.water = False

        self.player_x = 50
        self.player_y = 50
        
        self.cam_offset_x = 0.0
        self.cam_offset_y = 0.0

        self.spawn_x = 50
        self.spawn_y = 50

        self.vel_x = 0
        self.vel_y = 0

        self.grounded = False

        # =========================
        # TUNABLE PHYSICS SETTINGS
        # =========================

        self.GROUND_ACCEL = 350.0
        self.AIR_ACCEL = 100.0

        self.GRAVITY = 160.0

        self.JUMP_SPEED = 100.0

        self.MAX_X_SPEED = 220.0
        self.MAX_Y_SPEED = 500.0

        self.GROUND_FRICTION = 5.0
        self.AIR_FRICTION = 2.0
        self.WATER_DRAG = 4.25

        self.CAMERA_LAG = 0.07
        
        dir_map = "sd/map2.txt"

        with open(dir_map, "r") as f:
            self.tilemap = [bytearray(line, "utf-8") for line in f.read().splitlines()]
       
        self.map_width = len(self.tilemap[0]) * self.tile_size
        self.map_height = len(self.tilemap) * self.tile_size
        self.map_h = len(self.tilemap)
        self.map_w = len(self.tilemap[0])

    # =========================================================
    # RESPAWN
    # =========================================================

    def respawn(self):
        self.player_x = self.spawn_x
        self.player_y = self.spawn_y

        self.vel_x = 0
        self.vel_y = 0

        self.grounded = False

    # =========================================================
    # DRAW MAP
    # =========================================================

    def draw_map(self):
        cos = self.cos
        gfx = cos.gfx

        ts = self.tile_size
        tilemap = self.tilemap
        lookup = self.TILE_LOOKUP

        sw = self.screen_width
        sh = self.screen_height

        cam_x = ((self.player_x + ts // 2) - sw // 2) - self.X_offset
        cam_y = ((self.player_y + ts // 2) - sh // 2) - self.Y_offset

        start_tx = max(cam_x // ts, 0)
        end_tx = min((cam_x + sw) // ts + 1, self.map_w)

        start_ty = max(cam_y // ts, 0)
        end_ty = min((cam_y + sh) // ts + 1, self.map_h)

        active = []  # (x, y, w, h, color)

        for ty in range(start_ty, end_ty + 1):

            new_active = []

            if ty < end_ty:
                row = tilemap[int(ty)]

                tx = start_tx

                while tx < end_tx:
                    start = tx
                    val = row[int(tx)]
                    tile = lookup[val]
                    color = tile["color"]

                    # horizontal merge
                    while tx < end_tx and row[int(tx)] == val:
                        tx += 1

                    x = start * ts - cam_x
                    y = ty * ts - cam_y
                    w = (tx - start) * ts
                    h = ts

                    merged = False

                    # vertical merge with active rects
                    for i in range(len(active)):
                        ax, ay, aw, ah, acol = active[i]

                        if ax == x and aw == w and acol == color and ay + ah == y:
                            active[i] = (ax, ay, aw, ah + ts, acol)
                            merged = True
                            break

                    if not merged:
                        new_active.append((x, y, w, h, color))

            # flush previous row's finished vertical runs
            for r in active:
                gfx.rect(int(r[0]), int(r[1]), int(r[2]), int(r[3]), r[4], True)

            active = new_active

        # final flush
        for r in active:
            gfx.rect(int(r[0]), int(r[1]), int(r[2]), int(r[3]), r[4], True)

    # =========================================================
    # DRAW PLAYER
    # =========================================================

    def draw_player(self):
        cos = self.cos

        cos.gfx.rect(
            (self.screen_width // 2 - self.tile_size // 2) + self.X_offset -1,
            (self.screen_height // 2 - self.tile_size // 2) + self.Y_offset -1,
            self.tile_size,
            self.tile_size,
            (255, 255, 255),
            True
        )
        cos.gfx.pixel(
            (self.screen_width // 2 - self.tile_size // 2) + 2*self.tile_size//10 + self.X_offset - 1,
            (self.screen_height // 2 - self.tile_size // 2) + 4*self.tile_size//10 + self.Y_offset - 1,
            (0,0,0)
        )

        cos.gfx.pixel(
            (self.screen_width // 2 - self.tile_size // 2) + 8*self.tile_size//10 + self.X_offset - 1,
            (self.screen_height // 2 - self.tile_size // 2) + 4*self.tile_size//10 + self.Y_offset - 1,
            (0,0,0)
        )
    # =========================================================
    # COLLISION
    # =========================================================

    def is_solid(self, px, py):
        for cx, cy in (
            (px, py),
            (px + self.tile_size - 1, py),
            (px, py + self.tile_size - 1),
            (px + self.tile_size - 1, py + self.tile_size - 1),
        ):
            tx = cx // self.tile_size
            ty = cy // self.tile_size

            if (
                ty < 0
                or ty >= self.map_h
                or tx < 0
                or tx >= self.map_w
            ):
                return True

            if self.TILE_LOOKUP[self.tilemap[int(ty)][int(tx)]]["solid"]:
                return True

        return False

    # =========================================================
    # MOVE PLAYER
    # =========================================================

    def move_player(self, dx, dy):

        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1

        remaining_x = abs(dx)

        while remaining_x > 0:
            move = 1 if remaining_x >= 1 else remaining_x

            if not self.is_solid(
                self.player_x + step_x * move,
                self.player_y
            ):
                self.player_x += step_x * move
            else:
                self.vel_x = 0
                break

            remaining_x -= move

        remaining_y = abs(dy)

        while remaining_y > 0:
            move = 1 if remaining_y >= 1 else remaining_y

            if not self.is_solid(
                self.player_x,
                self.player_y + step_y * move
            ):
                self.player_y += step_y * move
            else:
                self.vel_y = 0
                break

            remaining_y -= move

    # =========================================================
    # UNSTICK
    # =========================================================

    def unstick_player(self):
        if not self.is_solid(self.player_x, self.player_y):
            return

        best_dx = 0
        best_dy = 0
        best_dist = 999999

        for cx, cy in (
            (self.player_x, self.player_y),
            (self.player_x + self.tile_size - 1, self.player_y),
            (self.player_x, self.player_y + self.tile_size - 1),
            (
                self.player_x + self.tile_size - 1,
                self.player_y + self.tile_size - 1
            ),
        ):
            tx = cx // self.tile_size
            ty = cy // self.tile_size

            if not (
                0 <= tx < self.map_w
                and 0 <= ty < self.map_h
            ):
                continue

            if self.TILE_LOOKUP[self.tilemap[ty][tx]]["solid"]:
                left = (tx + 1) * self.tile_size - cx
                right = cx - tx * self.tile_size

                top = (ty + 1) * self.tile_size - cy
                bottom = cy - ty * self.tile_size

                for dx, dy, d in (
                    (left, 0, left),
                    (-right, 0, right),
                    (0, top, top),
                    (0, -bottom, bottom),
                ):
                    if d < best_dist:
                        best_dist = d
                        best_dx = dx
                        best_dy = dy

        self.player_x += best_dx
        self.player_y += best_dy

    # =========================================================
    # TOUCH
    # =========================================================

    def touch(self):
        start_tx = (self.player_x - 1) // self.tile_size
        end_tx = (self.player_x + self.tile_size) // self.tile_size

        start_ty = (self.player_y - 1) // self.tile_size
        end_ty = (self.player_y + self.tile_size) // self.tile_size

        touched = set()

        for ty in range(start_ty, end_ty + 1):
            if 0 <= ty < self.map_h:
                row = self.tilemap[int(ty)]

                for tx in range(start_tx, end_tx + 1):
                    if 0 <= tx < len(row):
                        touched.add(
                            self.TILE_LOOKUP[row[int(tx)]]["type"]
                        )

        if "kill" in touched:
            self.respawn()

        self.water = "water" in touched

    # =========================================================
    # RUN
    # =========================================================

    def run(self):
        cos = self.cos

        while True:
            dpad = cos.input.get_cap("dpad")
            action = cos.input.get_cap("action")
            keys = cos.input.get_cap("keyboard")
            dt = cos.dt

            # =====================
            # CLEAR
            # =====================

            cos.gfx.fill((0, 0, 0))

            # =====================
            # PHYSICS
            # =====================

            self.grounded = self.is_solid(
                self.player_x,
                self.player_y + 1
            )

            self.touch()

            self.vel_y += self.GRAVITY * dt

            if self.grounded:
                self.vel_y = max(0, self.vel_y)

            # fall reset
            if self.player_y + self.tile_size > self.map_height + 50:
                self.respawn()

            # =====================
            # INPUT
            # =====================

            # respawn
            if (
                "START" in action
                or "k" in keys
            ):
                self.respawn()

            # exit
            if (
                "ESC" in keys
                or "`" in keys
            ):
                break

            # jump
            if (
                (
                    "UP" in dpad
                    or "A" in action
                )
                and (self.grounded or self.water)
            ):
                if self.water:
                    self.vel_y = -self.JUMP_SPEED * 0.25
                else:
                    self.vel_y = -self.JUMP_SPEED

            # left
            if (
                "LEFT" in dpad
                or "a" in keys
            ):
                if self.grounded:
                    self.vel_x -= self.GROUND_ACCEL * dt
                else:
                    self.vel_x -= self.AIR_ACCEL * dt

            # right
            if (
                "RIGHT" in dpad
                or "d" in keys
            ):
                if self.grounded:
                    self.vel_x += self.GROUND_ACCEL * dt
                else:
                    self.vel_x += self.AIR_ACCEL * dt

            # =====================
            # FRICTION
            # =====================
            if self.water:
                decay = math.exp(-self.WATER_DRAG * dt)
                self.vel_x *= decay
                self.vel_y *= decay

            else:
                if (
                    "LEFT" not in dpad
                    and "RIGHT" not in dpad
                    and "a" not in keys
                    and "d" not in keys
                ):
                    if self.grounded:
                        decay = math.exp(-self.GROUND_FRICTION * dt)
                    else:
                        decay = math.exp(-self.AIR_FRICTION * dt)

                    self.vel_x *= decay

            # =====================
            # LIMITS
            # =====================

            if self.vel_x > self.MAX_X_SPEED:
                self.vel_x = self.MAX_X_SPEED

            elif self.vel_x < -self.MAX_X_SPEED:
                self.vel_x = -self.MAX_X_SPEED

            if self.vel_y > self.MAX_Y_SPEED:
                self.vel_y = self.MAX_Y_SPEED

            elif self.vel_y < -self.MAX_Y_SPEED:
                self.vel_y = -self.MAX_Y_SPEED

            # =====================
            # MOVE
            # =====================

            self.move_player(
                self.vel_x * dt,
                self.vel_y * dt
            )

            self.unstick_player()

            # =====================
            # DRAW
            # =====================
            target_x = self.vel_x * self.CAMERA_LAG
            target_y = self.vel_y * self.CAMERA_LAG

            self.cam_offset_x += (
                target_x - self.cam_offset_x
            ) * 10 * dt

            self.cam_offset_y += (
                target_y - self.cam_offset_y
            ) * 10 * dt

            self.X_offset = int(self.cam_offset_x)
            self.Y_offset = int(self.cam_offset_y)
            
            self.draw_map()
            self.draw_player()

            yield cos.intent.INTENT_DRAW


if __name__ == "__main__":
    kernal.run(App)