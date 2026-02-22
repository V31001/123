"""
2D Adventure Platformer Game
Built with Python and Pygame
Controls: Arrow Keys / A/D to move, Space to jump, ESC to quit
"""

import pygame
import sys
import random

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 600
FPS = 60
GRAVITY = 0.6
JUMP_FORCE = -14
PLAYER_SPEED = 4

# Colour palette
WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
SKY    = ( 30, 144, 255)
GROUND = ( 34, 139,  34)
PLAT   = ( 80,  80,  80)
RED    = (220,  50,  47)
YELLOW = (255, 215,   0)
ORANGE = (255, 140,   0)
PURPLE = (128,   0, 128)
DARK   = ( 20,  20,  20)
GREY   = (160, 160, 160)
GREEN  = (  0, 200,   0)
HEALTH_RED   = (200,  30,  30)
HEALTH_GREEN = ( 30, 200,  30)


# ─────────────────────────────────────────────
#  PLATFORM  (static terrain)
# ─────────────────────────────────────────────
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color=PLAT):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        # Add a subtle highlight on top
        pygame.draw.line(self.image, WHITE, (0, 0), (w, 0), 2)
        self.rect = self.image.get_rect(topleft=(x, y))


# ─────────────────────────────────────────────
#  COIN
# ─────────────────────────────────────────────
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (10, 10), 9)
        pygame.draw.circle(self.image, ORANGE, (10, 10), 6)
        self.rect = self.image.get_rect(center=(x, y))
        self._bob_timer = random.randint(0, 60)  # stagger bobbing

    def update(self):
        """Gentle up-down bobbing animation."""
        self._bob_timer += 1
        offset = int(3 * pygame.math.Vector2(0, 1).rotate(self._bob_timer * 6).y)
        self.rect.centery += offset // 6  # small, smooth motion


# ─────────────────────────────────────────────
#  ENEMY
# ─────────────────────────────────────────────
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_min, patrol_max):
        super().__init__()
        self.width, self.height = 36, 42
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw_enemy()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = 2                  # walking speed
        self.patrol_min = patrol_min    # left patrol boundary (x)
        self.patrol_max = patrol_max    # right patrol boundary (x)

    def _draw_enemy(self):
        """Draw a simple goblin-like shape using rectangles/circles."""
        img = self.image
        img.fill((0, 0, 0, 0))
        # Body
        pygame.draw.rect(img, RED, (6, 16, 24, 20), border_radius=4)
        # Head
        pygame.draw.ellipse(img, RED, (4, 2, 28, 22))
        # Eyes
        pygame.draw.circle(img, WHITE, (12, 10), 5)
        pygame.draw.circle(img, WHITE, (24, 10), 5)
        pygame.draw.circle(img, BLACK, (13, 10), 3)
        pygame.draw.circle(img, BLACK, (25, 10), 3)
        # Horns
        pygame.draw.polygon(img, DARK, [(8, 4), (4, -4), (12, 2)])
        pygame.draw.polygon(img, DARK, [(28, 4), (32, -4), (24, 2)])
        # Legs
        pygame.draw.rect(img, DARK, (8,  36, 8, 6), border_radius=2)
        pygame.draw.rect(img, DARK, (20, 36, 8, 6), border_radius=2)

    def update(self, platforms):
        """Move horizontally and reverse at patrol boundaries or platform edges."""
        self.rect.x += self.vel_x

        # Reverse at patrol boundaries
        if self.rect.left <= self.patrol_min or self.rect.right >= self.patrol_max:
            self.vel_x *= -1
            self.rect.x += self.vel_x * 2  # nudge back to avoid sticking

        # Keep on top of platforms (simple ground-snap)
        self.rect.y += 1
        hit = pygame.sprite.spritecollideany(self, platforms)
        if hit:
            self.rect.bottom = hit.rect.top
        else:
            self.rect.y -= 1  # restore if no ground below (avoid falling off)


# ─────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width, self.height = 32, 48
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._base_image = self.image.copy()
        self._draw_player()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

        self.max_health = 100
        self.health = self.max_health
        self.score = 0

        self.invincible_timer = 0   # frames of invincibility after being hit
        self.facing_right = True
        self.walk_frame = 0

    def _draw_player(self):
        """Draw a simple hero character."""
        img = self.image
        img.fill((0, 0, 0, 0))
        # Cape / body
        pygame.draw.rect(img, PURPLE, (4, 20, 24, 22), border_radius=4)
        # Head
        pygame.draw.ellipse(img, (255, 200, 150), (6, 2, 20, 20))
        # Hair
        pygame.draw.ellipse(img, DARK, (6, 2, 20, 10))
        # Eyes
        pygame.draw.circle(img, WHITE, (12, 12), 3)
        pygame.draw.circle(img, WHITE, (20, 12), 3)
        pygame.draw.circle(img, DARK,  (13, 12), 2)
        pygame.draw.circle(img, DARK,  (21, 12), 2)
        # Legs
        pygame.draw.rect(img, DARK, (6,  42, 8, 6), border_radius=2)
        pygame.draw.rect(img, DARK, (18, 42, 8, 6), border_radius=2)
        # Sword (right side)
        pygame.draw.rect(img, GREY, (27, 18, 4, 18), border_radius=1)
        pygame.draw.rect(img, YELLOW, (24, 22, 10, 3))

    def handle_input(self, keys):
        """Read keyboard state and apply horizontal movement / jump."""
        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
            moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
            moving = True
        else:
            # Friction / deceleration
            self.vel_x *= 0.75
            if abs(self.vel_x) < 0.5:
                self.vel_x = 0

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

        # Animate walk cycle by wiggling rect slightly (cosmetic)
        if moving and self.on_ground:
            self.walk_frame += 1

    def apply_gravity(self):
        """Increase vertical velocity each frame."""
        self.vel_y += GRAVITY
        # Terminal velocity cap
        if self.vel_y > 20:
            self.vel_y = 20

    def move_and_collide(self, platforms):
        """Move by velocity, then resolve collisions with platforms."""
        # ── Horizontal ──
        self.rect.x += int(self.vel_x)
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_x > 0:
                    self.rect.right = plat.rect.left
                elif self.vel_x < 0:
                    self.rect.left = plat.rect.right
                self.vel_x = 0

        # ── Vertical ──
        self.on_ground = False
        self.rect.y += int(self.vel_y)
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_y > 0:          # falling → land on top
                    self.rect.bottom = plat.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:        # rising → hit ceiling
                    self.rect.top = plat.rect.bottom
                    self.vel_y = 0

    def take_damage(self, amount=20):
        """Reduce health, with a short invincibility window."""
        if self.invincible_timer > 0:
            return
        self.health -= amount
        self.invincible_timer = 90  # ~1.5 s at 60 FPS
        if self.health < 0:
            self.health = 0

    def update(self, keys, platforms):
        self.handle_input(keys)
        self.apply_gravity()
        self.move_and_collide(platforms)

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # Keep player within horizontal screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_W:
            self.rect.right = SCREEN_W

    def is_dead(self):
        return self.health <= 0

    def draw(self, surface):
        """Draw player; flash when invincible."""
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return  # blink effect
        img = self.image
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, self.rect)


# ─────────────────────────────────────────────
#  HUD – health bar, score
# ─────────────────────────────────────────────
def draw_hud(surface, player):
    # Health bar background
    pygame.draw.rect(surface, DARK,       (10, 10, 204, 22), border_radius=5)
    # Health fill
    bar_w = int(200 * (player.health / player.max_health))
    color = HEALTH_GREEN if player.health > 40 else HEALTH_RED
    if bar_w > 0:
        pygame.draw.rect(surface, color, (12, 12, bar_w, 18), border_radius=4)
    # Border
    pygame.draw.rect(surface, WHITE, (10, 10, 204, 22), 2, border_radius=5)

    font = pygame.font.SysFont(None, 28)
    # Health text
    hp_text = font.render(f"HP  {player.health}/{player.max_health}", True, WHITE)
    surface.blit(hp_text, (220, 12))
    # Score
    score_text = font.render(f"Score: {player.score}", True, YELLOW)
    surface.blit(score_text, (SCREEN_W - score_text.get_width() - 12, 12))


# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
def draw_start_screen(surface):
    surface.fill(DARK)
    title_font = pygame.font.SysFont(None, 72)
    sub_font   = pygame.font.SysFont(None, 36)

    title = title_font.render("PIXEL QUEST", True, YELLOW)
    sub   = sub_font.render("Press ENTER to Start   |   ESC to Quit", True, WHITE)
    tips  = [
        "Arrow Keys / A D  →  Move",
        "SPACE / UP        →  Jump",
        "Collect coins, avoid enemies!",
    ]

    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))
    surface.blit(sub,   (SCREEN_W // 2 - sub.get_width()   // 2, 280))

    tip_font = pygame.font.SysFont(None, 28)
    for i, tip in enumerate(tips):
        t = tip_font.render(tip, True, GREY)
        surface.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 340 + i * 32))


def draw_game_over(surface, score):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    big   = pygame.font.SysFont(None, 90)
    med   = pygame.font.SysFont(None, 42)
    small = pygame.font.SysFont(None, 32)

    go   = big.render("GAME OVER", True, RED)
    sc   = med.render(f"Final Score: {score}", True, YELLOW)
    rest = small.render("Press ENTER to Restart   |   ESC to Quit", True, WHITE)

    surface.blit(go,   (SCREEN_W // 2 - go.get_width()   // 2, 200))
    surface.blit(sc,   (SCREEN_W // 2 - sc.get_width()   // 2, 310))
    surface.blit(rest, (SCREEN_W // 2 - rest.get_width() // 2, 390))


def draw_win_screen(surface, score):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    big   = pygame.font.SysFont(None, 80)
    med   = pygame.font.SysFont(None, 42)
    small = pygame.font.SysFont(None, 32)

    win  = big.render("YOU WIN!", True, GREEN)
    sc   = med.render(f"Score: {score}", True, YELLOW)
    rest = small.render("Press ENTER to Play Again   |   ESC to Quit", True, WHITE)

    surface.blit(win,  (SCREEN_W // 2 - win.get_width()  // 2, 200))
    surface.blit(sc,   (SCREEN_W // 2 - sc.get_width()   // 2, 310))
    surface.blit(rest, (SCREEN_W // 2 - rest.get_width() // 2, 390))


# ─────────────────────────────────────────────
#  LEVEL BUILDER
# ─────────────────────────────────────────────
def build_level():
    """Create and return all sprite groups for a fresh level."""
    platforms = pygame.sprite.Group()
    coins     = pygame.sprite.Group()
    enemies   = pygame.sprite.Group()

    # ── Ground ──
    ground = Platform(0, 560, 800, 40, GROUND)
    platforms.add(ground)

    # ── Floating platforms ──
    plat_data = [
        (100, 460, 140, 18),
        (280, 380, 120, 18),
        (430, 460, 110, 18),
        (570, 350, 130, 18),
        (680, 430, 100, 18),
        (200, 280, 100, 18),
        (350, 210, 120, 18),
        (520, 260, 90,  18),
        (620, 170, 110, 18),
        (  0, 300, 80,  18),
    ]
    for x, y, w, h in plat_data:
        platforms.add(Platform(x, y, w, h))

    # ── Coins ── (placed above platforms)
    coin_positions = [
        (170, 435), (310, 355), (490, 435), (620, 320),
        (740, 405), (250, 255), (410, 185), (570, 235),
        (670, 145), (40,  275), (400, 535), (600, 535),
        (200, 535),
    ]
    for cx, cy in coin_positions:
        coins.add(Coin(cx, cy))

    # ── Enemies ── (x, y, patrol_left, patrol_right)
    enemy_data = [
        (110,  518, 50,  260),   # ground patrol left section
        (400,  518, 300, 700),   # ground patrol right section
        (283,  338, 280, 400),   # platform 2
        (571,  308, 570, 700),   # platform 6
        (203,  238, 200, 300),   # platform 8
    ]
    for ex, ey, pmin, pmax in enemy_data:
        enemies.add(Enemy(ex, ey, pmin, pmax))

    player = Player(60, 490)
    return player, platforms, coins, enemies


# ─────────────────────────────────────────────
#  BACKGROUND DRAWING
# ─────────────────────────────────────────────
def draw_background(surface):
    """Gradient sky + simple clouds."""
    # Simple two-tone sky
    surface.fill(SKY)
    # Darker strip at top
    pygame.draw.rect(surface, (20, 90, 180), (0, 0, SCREEN_W, 150))

    # Static decorative clouds (just white rounded rects)
    clouds = [(80, 60, 120, 40), (280, 40, 90, 30),
              (500, 80, 110, 35), (680, 50, 100, 32)]
    for cx, cy, cw, ch in clouds:
        pygame.draw.ellipse(surface, (220, 235, 255), (cx, cy, cw, ch))
        pygame.draw.ellipse(surface, WHITE, (cx + 10, cy - 10, cw - 20, ch + 5))


# ─────────────────────────────────────────────
#  MAIN GAME LOOP
# ─────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Pixel Quest — A 2D Adventure")
    clock = pygame.time.Clock()

    # States: "start", "playing", "game_over", "win"
    state = "start"

    player, platforms, coins, enemies = build_level()
    total_coins = len(coins)

    while True:
        dt = clock.tick(FPS)  # milliseconds; not used numerically (frame-based physics)
        keys = pygame.key.get_pressed()

        # ── Event handling ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_RETURN:
                    if state in ("start", "game_over", "win"):
                        # Reset / start game
                        player, platforms, coins, enemies = build_level()
                        total_coins = len(coins)
                        state = "playing"

        # ── Update ──
        if state == "playing":
            player.update(keys, platforms)
            enemies.update(platforms)
            coins.update()

            # Coin collection
            collected = pygame.sprite.spritecollide(player, coins, True)
            player.score += len(collected) * 10

            # Win condition: all coins collected
            if len(coins) == 0:
                state = "win"

            # Enemy collision → player takes damage
            if pygame.sprite.spritecollideany(player, enemies):
                player.take_damage(20)

            # Fell off screen (below ground level)
            if player.rect.top > SCREEN_H + 50:
                player.health = 0

            if player.is_dead():
                state = "game_over"

        # ── Draw ──
        draw_background(screen)

        if state == "start":
            draw_start_screen(screen)
        else:
            # Draw world
            platforms.draw(screen)
            coins.draw(screen)
            enemies.draw(screen)
            player.draw(screen)
            draw_hud(screen, player)

            # Coin counter
            font = pygame.font.SysFont(None, 26)
            coin_info = font.render(
                f"Coins: {total_coins - len(coins)}/{total_coins}", True, YELLOW)
            screen.blit(coin_info, (10, 40))

            if state == "game_over":
                draw_game_over(screen, player.score)
            elif state == "win":
                draw_win_screen(screen, player.score)

        pygame.display.flip()


if __name__ == "__main__":
    main()
