import math
import time
import core.kernal as kernal
import random
import micropython

class App:
    def __init__(self, cos):
        self.cos = cos

        self.G = 1.0
        self.show_map = False
        self.zoom_mode = False
        self.zoom_scale = 0.2
        self.last_toggle = False
        self.thrusting = False  # reset each frame
        self.landed = False

    def setup(self):
        self.cos.input.claim_caps(["dpad","action"])
        self.scr_w = self.cos.use_w
        self.scr_h = self.cos.use_h

        self.planets = self.generate_solar_system()
        indexx = random.randint(1,len(self.planets)-1)
        self.player = {
            'pos': [self.planets[indexx]['pos'][0], self.planets[indexx]['pos'][1]-self.planets[indexx]['r']+1],
            'vel': [self.planets[indexx]['vel'][0], self.planets[indexx]['vel'][1]],
            'angle': 0.0,
            'mass': 5.0
            }
        del indexx

    def generate_solar_system(self):
        sun = {
            'pos': [0.0, 3000.0],
            'vel': [0.0, 0.0],
            'mass': 30000000.0,
            'r': 500,
            'color': (255, 255, 0)
        }
        
    
        new_planets = [sun]
        orbits = []
        min_orbit = 500
        max_orbit = 20000
        orbit_spacing = 2500
    
        num_planets = 4 + random.randint(0, 2)
    
        for i in range(num_planets):
            if i == 0:
                orbit_radius = random.uniform(min_orbit, int(max_orbit / 4))
            else:
                last = orbits[-1]
                orbit_radius = last + orbit_spacing + random.uniform(0, 500)
                if orbit_radius > max_orbit:
                    break
            orbits.append(orbit_radius)
    
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle)
            dy = math.sin(angle)
            x = sun['pos'][0] + dx * orbit_radius
            y = sun['pos'][1] + dy * orbit_radius
    
            mass = random.uniform(500, 70000)
            radius = int((mass / 110) + random.uniform(0, 5))
    
            speed = math.sqrt(self.G * (sun['mass'] + mass) / orbit_radius)
            perp_x = -dy
            perp_y = dx
            vx = sun['vel'][0] + speed * perp_x
            vy = sun['vel'][1] + speed * perp_y
    
            color = (random.randint(80, 255), random.randint(80, 255), random.randint(80, 255))
    
            planet = {
                'pos': [x, y],
                'vel': [vx, vy],
                'mass': mass,
                'r': radius,
                'color': color
            }
    
            new_planets.append(planet)
    
            #  Add moon if massive enough
            if mass > 25000 and random.random() < 0.50:
                moon_mass = random.uniform(10, 100)
                moon_radius = max(7, int(moon_mass / 10) + random.randint(0, 5))
                moon_distance = random.uniform(radius + 200 + moon_radius, radius + 300 + moon_radius)
                moon_angle = random.uniform(0, 2 * math.pi)
                mx = x + moon_distance * math.cos(moon_angle)
                my = y + moon_distance * math.sin(moon_angle)
    
                moon_speed = math.sqrt(self.G * (mass + moon_mass) / moon_distance)
                perp_mx = -math.sin(moon_angle)
                perp_my = math.cos(moon_angle)
                mvx = vx + moon_speed * perp_mx
                mvy = vy + moon_speed * perp_my
    
                moon = {
                    'pos': [mx, my],
                    'vel': [mvx, mvy],
                    'mass': moon_mass,
                    'r': moon_radius,
                    'color': (200, 200, 255)
                }
    
                new_planets.append(moon)
        if random.random() < 0.1:
            blackhole = {
                    'pos': [random.uniform(-5000, 5000), random.uniform(8000, 12000)],
                    'vel': [0, 0],
                    'mass': 50000000.0,
                    'r': 80,
                    'color': (10, 10, 10)
                }
            new_planets.append(blackhole)
    
        return new_planets
    
    @micropython.native
    def apply_gravity(self,a, b):
        dx = b['pos'][0] - a['pos'][0]
        dy = b['pos'][1] - a['pos'][1]
        dist_sq = dx*dx + dy*dy
        if dist_sq == 0 or dist_sq < b['r'] * b['r']:
            return
        dist = math.sqrt(dist_sq)
        force = self.G * a['mass'] * b['mass'] / dist_sq
        inv_mass = 1 / a['mass']
        fx = force * dx / dist
        fy = force * dy / dist
        a['vel'][0] += fx * inv_mass
        a['vel'][1] += fy * inv_mass
    
    #@micropython.native
    def keep_out_of_planets(self):
        self.landed = False
        for p in self.planets:
            dx = self.player['pos'][0] - p['pos'][0]
            dy = self.player['pos'][1] - p['pos'][1]
            dist_sq = dx * dx + dy * dy
            if dist_sq < p['r'] * p['r']:
                dist = math.sqrt(dist_sq) if dist_sq > 0 else 1.0
                nx = dx / dist
                ny = dy / dist
                self.player['pos'][0] = p['pos'][0] + nx * p['r']
                self.player['pos'][1] = p['pos'][1] + ny * p['r']
                self.player['vel'][0] = p['vel'][0]
                self.player['vel'][1] = p['vel'][1]
                self.landed = True

    def resolve_collision(self, a, b):
        m1, m2 = a['mass'], b['mass']
        u1x, u1y = a['vel']
        u2x, u2y = b['vel']
    
        a['vel'][0] = (u1x * (m1 - m2) + 2 * m2 * u2x) / (m1 + m2)
        a['vel'][1] = (u1y * (m1 - m2) + 2 * m2 * u2y) / (m1 + m2)
        b['vel'][0] = (u2x * (m2 - m1) + 2 * m1 * u1x) / (m1 + m2)
        b['vel'][1] = (u2y * (m2 - m1) + 2 * m1 * u1y) / (m1 + m2)
    
    #@micropython.native
    def separate_planets(self):
        for i, a in enumerate(self.planets):
            for j in range(i + 1, len(self.planets)):
                b = self.planets[j]
                dx = b['pos'][0] - a['pos'][0]
                dy = b['pos'][1] - a['pos'][1]
                dist_sq = dx * dx + dy * dy
                min_dist = a['r'] + b['r']
                if dist_sq < min_dist * min_dist and dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    overlap = min_dist - dist
                    nx = dx / dist
                    ny = dy / dist
                    a['pos'][0] -= nx * overlap / 2
                    a['pos'][1] -= ny * overlap / 2
                    b['pos'][0] += nx * overlap / 2
                    b['pos'][1] += ny * overlap / 2
                    self.resolve_collision(a, b)
    
    @micropython.native
    def planet_gravity(self):
        for i, a in enumerate(self.planets):
            for j in range(i + 1, len(self.planets)):
                b = self.planets[j]
                dx = b['pos'][0] - a['pos'][0]
                dy = b['pos'][1] - a['pos'][1]
                dist_sq = dx * dx + dy * dy
                if dist_sq == 0 or dist_sq < (a['r'] + b['r']) ** 2:
                    continue
                inv_dist = 1 / math.sqrt(dist_sq)
                f = self.G * a['mass'] * b['mass'] * inv_dist * inv_dist
                fx = f * dx * inv_dist
                fy = f * dy * inv_dist
                a['vel'][0] += fx / a['mass']
                a['vel'][1] += fy / a['mass']
                b['vel'][0] -= fx / b['mass']
                b['vel'][1] -= fy / b['mass']
    
    #@micropython.native
    def update_player(self):
        for p in self.planets:
            self.apply_gravity(self.player, p)
        self.player['pos'][0] += self.player['vel'][0]
        self.player['pos'][1] += self.player['vel'][1]
        self.keep_out_of_planets()
    
    @micropython.native
    def update_planets(self):
        self.planet_gravity()
        planets = self.planets
        for p in planets:
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
        self.separate_planets()

    def get_SOI_body_index(self):
        """Return index of the planet whose gravity dominates (Sphere of Influence)."""
        closest_index = None
        closest_force = 0.0
        px, py = self.player['pos']
        for i, p in enumerate(self.planets):
            if p['mass'] > 1_000_000:
                continue
            dx = px - p['pos'][0]
            dy = py - p['pos'][1]
            dist_sq = dx * dx + dy * dy
            if dist_sq == 0:
                continue
            force = self.G * p['mass'] / dist_sq
            if force > closest_force:
                closest_index = i
                closest_force = force
        if closest_force < 0.019:
            return 0
        return closest_index

    def simulate_trajectory(self, index, steps=125, dt=10.0):
        sim_pos = self.player['pos'][:]
        sim_vel = self.player['vel'][:]
        sim_mass = self.player['mass']
    
        sim_planets = []
        for p in self.planets:
            sim_planets.append({
                'pos': p['pos'][:],
                'vel': p['vel'][:],
                'mass': p['mass']
            })
        ref_planet = sim_planets[index]
    
        points = [(sim_pos[0] - ref_planet['pos'][0], sim_pos[1] - ref_planet['pos'][1])]
        planet_forces = [[0.0, 0.0] for _ in sim_planets]
    
        for _ in range(steps):
            fx = fy = 0.0
            for forces in planet_forces:
                forces[0] = 0.0
                forces[1] = 0.0
    
            # Gravity on player from all planets
            for p in sim_planets:
                dx = p['pos'][0] - sim_pos[0]
                dy = p['pos'][1] - sim_pos[1]
                dist_sq = dx*dx + dy*dy
                if dist_sq < 1e-10:
                    continue
                inv_dist = 1.0 / (dist_sq ** 0.5)  # one sqrt per planet-player pair per step
                inv_dist_cubed = inv_dist / dist_sq  # (1/d)^3 = (1/d) / d^2
                f = self.G * sim_mass * p['mass'] * inv_dist_cubed
                fx += f * dx
                fy += f * dy
    
            sim_vel[0] += (fx / sim_mass) * dt
            sim_vel[1] += (fy / sim_mass) * dt
            sim_pos[0] += sim_vel[0] * dt
            sim_pos[1] += sim_vel[1] * dt
    
            # Planet-planet gravity
            num_planets = len(sim_planets)
            for i in range(num_planets):
                for j in range(i + 1, num_planets):
                    a = sim_planets[i]
                    b = sim_planets[j]
                    dx = b['pos'][0] - a['pos'][0]
                    dy = b['pos'][1] - a['pos'][1]
                    dist_sq = dx*dx + dy*dy
                    if dist_sq < 1e-10:
                        continue
                    inv_dist = 1.0 / (dist_sq ** 0.5)
                    inv_dist_cubed = inv_dist / dist_sq
                    f = self.G * a['mass'] * b['mass'] * inv_dist_cubed
                    force_x = f * dx
                    force_y = f * dy
                    planet_forces[i][0] += force_x
                    planet_forces[i][1] += force_y
                    planet_forces[j][0] -= force_x
                    planet_forces[j][1] -= force_y
    
            # Update planet velocities and positions
            for i, planet in enumerate(sim_planets):
                planet['vel'][0] += (planet_forces[i][0] / planet['mass']) * dt
                planet['vel'][1] += (planet_forces[i][1] / planet['mass']) * dt
                planet['pos'][0] += planet['vel'][0] * dt
                planet['pos'][1] += planet['vel'][1] * dt
    
            # Relative position to ref planet
            target = sim_planets[index]
            rel_x = sim_pos[0] - target['pos'][0]
            rel_y = sim_pos[1] - target['pos'][1]
            points.append((rel_x, rel_y))
    
        return points
    
    #@micropython.native
    def world_to_screen(self, x, y):
        cx, cy = self.player['pos']
        return int(x - cx + (self.scr_w//2)), int(y - cy + (self.scr_h//2))

    def draw(self):
        gfx = self.cos.gfx
        gfx.fill((0, 0, 0))

        # -------------------------
        # Draw planets
        # -------------------------
        for p in self.planets:
            try:
                px, py = self.world_to_screen(*p["pos"])

                r = int(p["r"])

                # completely offscreen?
                if (
                    px + r < 0 or
                    px - r >= self.scr_w or
                    py + r < 0 or
                    py - r >= self.scr_h
                ):
                    continue

                gfx.ellipse(px, py, r, r, p["color"])

            except Exception:
                pass

        # -------------------------
        # Draw player
        # -------------------------
        try:
            sx, sy = self.world_to_screen(*self.player["pos"])

            if math.isfinite(sx) and math.isfinite(sy):
                sx = int(sx)
                sy = int(sy)

                gfx.ellipse(sx, sy, 2, 2, (255, 255, 255))

                dx = int(math.cos(self.player["angle"]) * 5)
                dy = int(math.sin(self.player["angle"]) * 5)
                gfx.line(sx, sy, sx + dx, sy + dy, (0, 255, 255))

                if self.thrusting:
                    fx = sx - int(math.cos(self.player["angle"]) * 4)
                    fy = sy - int(math.sin(self.player["angle"]) * 4)
                    gfx.rect(fx, fy, 2, 2, (255, 100, 0), f=True)
        except Exception:
            sx = sy = 0

        # -------------------------
        # Find nearest body
        # -------------------------
        nearest_dist = None
        rel_speed = 0.0
        rvx = rvy = 0.0

        for p in self.planets:
            try:
                dx = p["pos"][0] - self.player["pos"][0]
                dy = p["pos"][1] - self.player["pos"][1]

                dist = math.sqrt(dx * dx + dy * dy) - p["r"]

                if nearest_dist is None or dist < nearest_dist:
                    nearest_dist = dist

                    rvx = self.player["vel"][0] - p["vel"][0]
                    rvy = self.player["vel"][1] - p["vel"][1]
                    rel_speed = math.sqrt(rvx * rvx + rvy * rvy)
            except Exception:
                pass

        # -------------------------
        # Prograde marker
        # -------------------------
        diff_angle = 0

        if rel_speed > 0.1:
            try:
                rel_angle = math.atan2(rvy, rvx)

                diff_angle = (rel_angle - self.player["angle"]) % (2 * math.pi)
                if diff_angle > math.pi:
                    diff_angle -= 2 * math.pi

                vx_dir = rvx / rel_speed
                vy_dir = rvy / rel_speed

                dot_x = sx + int(vx_dir * min(rel_speed, 20))
                dot_y = sy + int(vy_dir * min(rel_speed, 20))

                gfx.ellipse(dot_x, dot_y, 1, 1, (255, 0, 0))
            except Exception:
                pass

        # -------------------------
        # HUD
        # -------------------------
        gfx.text(f"VEL:{self.player['vel'][0]:.1f},{self.player['vel'][1]:.1f}",0, 0, (0, 255, 0))

        gfx.text(f"POS:{self.player['pos'][0]:.1f},{self.player['pos'][1]:.1f}",0, gfx.font_height(), (0, 255, 0))

        if self.landed:
            gfx.text("LANDED",0,self.scr_h - gfx.font_height() * 3,(255, 0, 0),)

        alt = int(nearest_dist) if nearest_dist is not None and math.isfinite(nearest_dist) else 0

        gfx.text(f"ALT:{alt}m   REL:{int(rel_speed)}m/s",0,self.scr_h - gfx.font_height(),(200, 200, 200),)

        if abs(diff_angle) < 0.5:
            gfx.text("PRO",0,self.scr_h - gfx.font_height() * 2,(0, 255, 0),)
        elif abs(abs(diff_angle) - math.pi) < 0.5:
            gfx.text("RETRO",0,self.scr_h - gfx.font_height() * 2,(255, 0, 0),)

    def draw_map(self):
        gfx = self.cos.gfx
        gfx.fill((0, 0, 0))
    
        if self.zoom_mode:
            cx, cy = self.player['pos']
            scale = self.zoom_scale
        else:
            min_x = max_x = self.player['pos'][0]
            min_y = max_y = self.player['pos'][1]
            for p in self.planets:
                x = p['pos'][0]
                y = p['pos'][1]

                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
            margin = 20
            scale_x = (self.scr_w - 2 * margin) / (max_x - min_x + 1)
            scale_y = (self.scr_h - 2 * margin) / (max_y - min_y + 1)
            scale = min(scale_x, scale_y)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
    
        def w2m(px, py):
            return int((self.scr_w//2) + (px - cx) * scale), int((self.scr_h//2) + (py - cy) * scale)
    
        for p in self.planets:
            mx, my = w2m(*p['pos'])
            r = max(1, int(p['r'] * scale))

            if (
                mx + r < 0 or
                mx - r >= self.scr_w or
                my + r < 0 or
                my - r >= self.scr_h
            ):
                continue

            gfx.ellipse(mx, my, r, r, p['color'])
            
        soi_index = self.get_SOI_body_index()
        ref_planet = self.planets[soi_index]
        path = self.simulate_trajectory(soi_index, steps=10, dt=22.0)
        ref_x, ref_y = ref_planet['pos']
    
        for i in range(len(path) - 1):
            x1 = path[i][0] + ref_x
            y1 = path[i][1] + ref_y
            x2 = path[i + 1][0] + ref_x
            y2 = path[i + 1][1] + ref_y
            mx1, my1 = w2m(x1, y1)
            mx2, my2 = w2m(x2, y2)
            if (
                (mx1 < 0 and mx2 < 0) or
                (mx1 >= self.scr_w and mx2 >= self.scr_w) or
                (my1 < 0 and my2 < 0) or
                (my1 >= self.scr_h and my2 >= self.scr_h)
            ):
                continue

            gfx.line(mx1, my1, mx2, my2, (255,255,0))
    
        # Player
        px, py = w2m(*self.player['pos'])
        gfx.ellipse(px, py, 2, 2, (255, 255, 255))
        dx = math.cos(self.player['angle']) * 8
        dy = math.sin(self.player['angle']) * 8
        gfx.line(px, py, int(px + dx), int(py + dy), (0, 255, 255))
    
        # SOI line
        sx, sy = w2m(*ref_planet['pos'])
        gfx.line(px, py, sx, sy, (0, 100, 255))
    
        gfx.text(f"MAP {'(Zoom)' if self.zoom_mode else ''}", 0, 0, (0, 255, 0))
        if self.landed:
            gfx.text("LANDED", 0, gfx.font_height(), (255, 0, 0))
    
    #@micropython.native
    def handle_input(self):
        player = self.player
        inputt = self.cos.input
        self.thrusting = False
        # Toggle map
        toggle = inputt.was_pressed_cap('action','START')
        if toggle and not self.last_toggle:
            self.show_map = not self.show_map
        self.last_toggle = toggle
    
        # Zoom toggle
        if self.show_map and inputt.was_pressed_cap('action','SELECT'):
            self.zoom_mode = not self.zoom_mode
        if self.zoom_mode:
            if inputt.is_down_cap('action','X'):
                self.zoom_scale *= 1.2
            if inputt.is_down_cap('action','Y'):
                self.zoom_scale /= 1.2
    
        # Rotation
        if inputt.is_down_cap('dpad','LEFT'):
            player['angle'] -= 0.4
        if inputt.is_down_cap('dpad','RIGHT'):
            player['angle'] += 0.4
    
        # Thrust
        if inputt.is_down_cap('action','A'):
            thrust = 1.4
            player['vel'][0] += thrust * math.cos(player['angle'])
            player['vel'][1] += thrust * math.sin(player['angle'])
            self.thrusting = True
        if inputt.is_down_cap('dpad','CENTER'):
            thrust = 6
            player['vel'][0] += thrust * math.cos(player['angle'])
            player['vel'][1] += thrust * math.sin(player['angle'])
            self.thrusting = True
    
        # Match orbit
        if inputt.was_pressed_cap('action','B'):
            nearest = None
            nearest_dist = float('inf')
            for p in self.planets:
                dx = player['pos'][0] - p['pos'][0]
                dy = player['pos'][1] - p['pos'][1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < nearest_dist:
                    nearest = p
                    nearest_dist = dist
            if nearest and nearest_dist > 1:
                dx = nearest['pos'][0] - player['pos'][0]
                dy = nearest['pos'][1] - player['pos'][1]
                dist = math.sqrt(dx * dx + dy * dy)
                speed = math.sqrt(self.G * nearest['mass'] / dist)
                tx = -dy / dist
                ty = dx / dist
                player['vel'][0] = nearest['vel'][0] + tx * speed
                player['vel'][1] = nearest['vel'][1] + ty * speed
    
        if inputt.is_down_cap('action','B') and inputt.is_down_cap('action','SELECT'):
            self.reset_game()
        #if 0 in btns or 'q' in keys:
        #    return False
        return True

    def reset_game(self):
        self.planets = self.generate_solar_system()
        indexx = random.randint(1,len(self.planets)-1)
        self.player['pos'] = [self.planets[indexx]['pos'][0], self.planets[indexx]['pos'][1]-self.planets[indexx]['r']+1]
        self.player['vel'] = [self.planets[indexx]['vel'][0], self.planets[indexx]['vel'][1]]
        self.player['angle'] = 0.0
        del indexx

    def run(self):
        cos = self.cos
        while True:
            if not self.handle_input():
                yield cos.intent.INTENT_KILL_APP
            self.update_planets()
            self.update_player()
            if self.show_map:
                self.draw_map()
            else:
                self.draw()
            yield cos.intent.INTENT_DRAW
            #time.sleep(0.01)

if __name__ == "__main__":
    kernal.run(App)