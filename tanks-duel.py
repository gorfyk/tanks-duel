import pygame
import sys
import math
import random

pygame.init()

# === ФИКСИРОВАННЫЙ РАЗМЕР ИГРЫ ===
GAME_WIDTH = 1000
GAME_HEIGHT = 900
FPS = 60
TANK_SIZE = 55
BULLET_RADIUS = 8
BULLET_SPEED = 9
MAX_AMMO = 5
RELOAD_TIME = 90

# === ЦВЕТА ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)
PLAYER_COLOR = (148, 0, 211)
BOT_COLOR = (255, 215, 0)
BULLET_COLOR = (0, 191, 255)
COLOR_BRICK = (200, 100, 50)
COLOR_METAL = (169, 169, 169)
COLOR_GRASS = (144, 238, 144)
COLOR_HEALTH = (255, 50, 50)
COLOR_SHIELD = (0, 150, 255)
COLOR_FIRE = (255, 140, 0)
COLOR_ELECTRO = (0, 200, 255)
COLOR_DOUBLE = (255, 50, 50)

GRID_SIZE = 16
CELL_SIZE = GAME_WIDTH // GRID_SIZE

info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("ТАНЧИКИ: ДУЭЛЬ")
clock = pygame.time.Clock()

game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

font_title = pygame.font.Font(None, 72)
font_large = pygame.font.Font(None, 48)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 28)

def draw_game_surface():
    screen_width, screen_height = screen.get_size()
    scale_x = screen_width / GAME_WIDTH
    scale_y = screen_height / GAME_HEIGHT
    scale = min(scale_x, scale_y)
    new_width = int(GAME_WIDTH * scale)
    new_height = int(GAME_HEIGHT * scale)
    scaled_surface = pygame.transform.scale(game_surface, (new_width, new_height))
    x = (screen_width - new_width) // 2
    y = (screen_height - new_height) // 2
    screen.fill((0, 0, 0))
    screen.blit(scaled_surface, (x, y))

game_state = "menu"
difficulty = "normal"
player = None
bot = None
bullets = []
particles = []
game_map = []
bonuses = []
bonus_timer = 0
SHIELD_ACTIVE = False
FIRE_ACTIVE = False
ELECTRO_ACTIVE = False
DOUBLE_ACTIVE = False
FIRE_TIMER = 0
ELECTRO_TIMER = 0
DOUBLE_TIMER = 0
BOT_SLOW_TIMER = 0
BOT_CURRENT_SPEED = 1.5

def generate_map():
    game_map = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    for y in range(5, 10):
        for x in range(0, 4):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                game_map[y][x] = 0
    for y in range(5, 10):
        for x in range(12, 16):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                game_map[y][x] = 0
                
    for y in range(5, 11):
        for x in range(5, 11):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                game_map[y][x] = 0
    
    for y in range(2, 5):
        for x in range(2, 5):
            game_map[y][x] = 1
    for y in range(10, 13):
        for x in range(2, 5):
            game_map[y][x] = 1
    for y in range(2, 5):
        for x in range(11, 14):
            game_map[y][x] = 1
    for y in range(10, 13):
        for x in range(11, 14):
            game_map[y][x] = 1
    
    for y in range(3, 5):
        for x in range(3, 5):
            game_map[y][x] = 2
    for y in range(10, 12):
        for x in range(3, 5):
            game_map[y][x] = 2
    for y in range(3, 5):
        for x in range(11, 13):
            game_map[y][x] = 2
    for y in range(10, 12):
        for x in range(11, 13):
            game_map[y][x] = 2
    
    game_map[5][5] = 1
    game_map[5][6] = 1
    game_map[5][9] = 1
    game_map[5][10] = 1
    game_map[6][5] = 1
    game_map[6][10] = 1
    game_map[9][5] = 1
    game_map[9][10] = 1
    game_map[10][5] = 1
    game_map[10][6] = 1
    game_map[10][9] = 1
    game_map[10][10] = 1
    
    return game_map

def spawn_bonus():
    global bonuses
    free_cells = []
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if game_map[y][x] == 0:
                cell_center_x = x * CELL_SIZE + CELL_SIZE//2
                cell_center_y = y * CELL_SIZE + CELL_SIZE//2
                if player:
                    dist_to_player = math.sqrt((cell_center_x - player.x)**2 + (cell_center_y - player.y)**2)
                    if dist_to_player < CELL_SIZE * 2:
                        continue
                if bot:
                    dist_to_bot = math.sqrt((cell_center_x - bot.x)**2 + (cell_center_y - bot.y)**2)
                    if dist_to_bot < CELL_SIZE * 2:
                        continue
                free_cells.append((x, y))
    
    if free_cells:
        x, y = random.choice(free_cells)
        
        # РЕШАЕМ: ЧТО БУДЕТ ВЫПАДАТЬ?
        r = random.random()
        if r < 0.35:
            # Аптечка (35%)
            bonus_type = "health"
        elif r < 0.70:
            # Щит (35%)
            bonus_type = "shield"
        else:
            # ОРУЖИЕ (30%) — равные шансы на 3 вида!
            weapon_r = random.random()
            if weapon_r < 0.33:
                bonus_type = "fire"
            elif weapon_r < 0.66:
                bonus_type = "electro"
            else:
                bonus_type = "double"
        
        bonuses.append({
            'x': x * CELL_SIZE + CELL_SIZE//2,
            'y': y * CELL_SIZE + CELL_SIZE//2,
            'type': bonus_type,
            'timer': 900,
            'pulse': 0
        })

def create_explosion(x, y, color, count=25):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 6)
        particles.append({
            'x': x, 'y': y,
            'dx': math.cos(angle) * speed,
            'dy': math.sin(angle) * speed,
            'life': random.randint(15, 35),
            'color': color,
            'size': random.randint(3, 8)
        })

class Tank:
    def __init__(self, x, y, color, name):
        self.x = x
        self.y = y
        self.angle = 0
        self.color = color
        self.name = name
        self.hp = 3
        self.cooldown = 0
        self.shoot_count = 0
        self.hit_effect = 0
        self.ammo = MAX_AMMO
        self.reload_timer = 0
        self.is_reloading = False
        self.state = "idle"
        
    def draw(self, surface):
        shadow_rect = pygame.Rect(self.x - TANK_SIZE//2 + 4, self.y - TANK_SIZE//2 + 4, TANK_SIZE, TANK_SIZE)
        pygame.draw.rect(surface, (0, 0, 0, 50), shadow_rect)
        
        rect = pygame.Rect(self.x - TANK_SIZE//2, self.y - TANK_SIZE//2, TANK_SIZE, TANK_SIZE)
        pygame.draw.rect(surface, self.color, rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, rect, width=2, border_radius=5)
        
        for i in range(4):
            track_rect = pygame.Rect(self.x - TANK_SIZE//2 - 2, self.y - TANK_SIZE//2 + 5 + i*13, 10, 10)
            pygame.draw.rect(surface, (60, 60, 60), track_rect, border_radius=3)
            pygame.draw.rect(surface, (100, 100, 100), track_rect, width=1)
        for i in range(4):
            track_rect = pygame.Rect(self.x + TANK_SIZE//2 - 8, self.y - TANK_SIZE//2 + 5 + i*13, 10, 10)
            pygame.draw.rect(surface, (60, 60, 60), track_rect, border_radius=3)
            pygame.draw.rect(surface, (100, 100, 100), track_rect, width=1)
        
        pygame.draw.circle(surface, (220, 220, 220), (int(self.x), int(self.y)), TANK_SIZE//2.5)
        pygame.draw.circle(surface, (200, 200, 200), (int(self.x), int(self.y)), TANK_SIZE//3.5)
        pygame.draw.circle(surface, (150, 150, 150), (int(self.x), int(self.y)), TANK_SIZE//2.5, width=2)
        
        end_x = self.x + math.cos(self.angle) * TANK_SIZE//1.1
        end_y = self.y + math.sin(self.angle) * TANK_SIZE//1.1
        pygame.draw.line(surface, (80, 80, 80), (self.x, self.y), (end_x, end_y), 8)
        pygame.draw.line(surface, (150, 150, 150), 
                        (self.x + math.cos(self.angle) * 5, self.y + math.sin(self.angle) * 5),
                        (end_x - math.cos(self.angle) * 5, end_y - math.sin(self.angle) * 5), 4)
        tip_x = self.x + math.cos(self.angle) * TANK_SIZE//1.2
        tip_y = self.y + math.sin(self.angle) * TANK_SIZE//1.2
        pygame.draw.circle(surface, (50, 50, 50), (int(tip_x), int(tip_y)), 6)
        
        pygame.draw.circle(surface, (120, 120, 120), (int(self.x - 5), int(self.y - 8)), 5)
        pygame.draw.circle(surface, (100, 100, 100), (int(self.x + 5), int(self.y + 5)), 4)
        
        if self.hit_effect > 0:
            pygame.draw.circle(surface, (255, 0, 0), (int(self.x), int(self.y)), TANK_SIZE//2, 5)
            self.hit_effect -= 1
        
        if self == player:
            if FIRE_ACTIVE:
                pygame.draw.circle(surface, (255, 140, 0, 100), (int(self.x), int(self.y)), TANK_SIZE//1.5, 4)
                for i in range(6):
                    angle = pygame.time.get_ticks() / 200 + i * 1.0
                    dx = math.cos(angle) * TANK_SIZE//1.2
                    dy = math.sin(angle) * TANK_SIZE//1.2
                    pygame.draw.circle(surface, (255, 100, 0, 50), (int(self.x + dx), int(self.y + dy)), 6)
            
            if ELECTRO_ACTIVE:
                pygame.draw.circle(surface, (0, 200, 255, 100), (int(self.x), int(self.y)), TANK_SIZE//1.5, 4)
                for i in range(8):
                    angle = pygame.time.get_ticks() / 150 + i * 0.8
                    dx = math.cos(angle) * TANK_SIZE//1.3
                    dy = math.sin(angle) * TANK_SIZE//1.3
                    pygame.draw.circle(surface, (0, 150, 255, 50), (int(self.x + dx), int(self.y + dy)), 4)
            
            if DOUBLE_ACTIVE:
                pygame.draw.circle(surface, (255, 50, 50, 100), (int(self.x), int(self.y)), TANK_SIZE//1.5, 4)
                for i in range(4):
                    angle = pygame.time.get_ticks() / 100 + i * 1.5
                    dx = math.cos(angle) * TANK_SIZE//1.4
                    dy = math.sin(angle) * TANK_SIZE//1.4
                    pygame.draw.circle(surface, (255, 0, 0, 50), (int(self.x + dx), int(self.y + dy)), 5)

        if self == player and SHIELD_ACTIVE:
            pulse = pygame.time.get_ticks() / 200
            alpha = int((math.sin(pulse) * 0.3 + 0.7) * 150)
            shield_surface = pygame.Surface((TANK_SIZE + 30, TANK_SIZE + 30), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (0, 150, 255, alpha), 
                              (TANK_SIZE//2 + 15, TANK_SIZE//2 + 15), TANK_SIZE//2 + 15, 4)
            surface.blit(shield_surface, (self.x - TANK_SIZE//2 - 15, self.y - TANK_SIZE//2 - 15))

    def get_rect(self):
        return pygame.Rect(self.x - TANK_SIZE//2, self.y - TANK_SIZE//2, TANK_SIZE, TANK_SIZE)
    
    def shoot(self):
        if self.ammo > 0 and not self.is_reloading:
            self.ammo -= 1
            if self.ammo == 0:
                self.is_reloading = True
                self.reload_timer = RELOAD_TIME
            return True
        return False
    
    def update_reload(self):
        if self.is_reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.ammo = MAX_AMMO
                self.is_reloading = False

def is_colliding_with_map(rect):
    corners = [
        (rect.left, rect.top),
        (rect.right, rect.top),
        (rect.left, rect.bottom),
        (rect.right, rect.bottom)
    ]
    for cx, cy in corners:
        gx = int(cx // CELL_SIZE)
        gy = int(cy // CELL_SIZE)
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            if game_map[gy][gx] in [1, 2]:
                return True
    return False

def can_move_to(new_x, new_y, tank):
    test_rect = pygame.Rect(new_x - TANK_SIZE//2, new_y - TANK_SIZE//2, TANK_SIZE, TANK_SIZE)
    if test_rect.left < 0 or test_rect.right > GAME_WIDTH or test_rect.top < 0 or test_rect.bottom > GAME_HEIGHT:
        return False
    if is_colliding_with_map(test_rect):
        return False
    other = bot if tank == player else player
    if other and test_rect.colliderect(other.get_rect()):
        return False
    return True

def find_path_towards(start_x, start_y, target_x, target_y):
    best_angle = math.atan2(target_y - start_y, target_x - start_x)
    for angle_offset in [0, 0.2, -0.2, 0.4, -0.4, 0.6, -0.6, 0.8, -0.8]:
        angle = best_angle + angle_offset
        for dist in [1, 2, 3, 4]:
            dx = math.cos(angle) * dist * 3
            dy = math.sin(angle) * dist * 3
            test_rect = pygame.Rect(start_x + dx - TANK_SIZE//2, start_y + dy - TANK_SIZE//2, TANK_SIZE, TANK_SIZE)
            if not is_colliding_with_map(test_rect):
                if test_rect.left > 0 and test_rect.right < GAME_WIDTH and test_rect.top > 0 and test_rect.bottom < GAME_HEIGHT:
                    next_rect = pygame.Rect(start_x + dx*2 - TANK_SIZE//2, start_y + dy*2 - TANK_SIZE//2, TANK_SIZE, TANK_SIZE)
                    if not is_colliding_with_map(next_rect):
                        return dx, dy
                    if abs(angle_offset) < 0.4:
                        return dx, dy
    return None, None

def draw_map():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = game_map[y][x]
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if cell == 1:
                pygame.draw.rect(game_surface, COLOR_BRICK, rect)
                pygame.draw.rect(game_surface, (150, 70, 30), rect, 3)
                pygame.draw.line(game_surface, (150, 70, 30), (rect.x, rect.y + CELL_SIZE//2), 
                                (rect.x + CELL_SIZE, rect.y + CELL_SIZE//2), 3)
                pygame.draw.line(game_surface, (150, 70, 30), (rect.x + CELL_SIZE//2, rect.y), 
                                (rect.x + CELL_SIZE//2, rect.y + CELL_SIZE), 3)
            elif cell == 2:
                pygame.draw.rect(game_surface, COLOR_METAL, rect)
                pygame.draw.rect(game_surface, (120, 120, 120), rect, 3)
                for mx in [rect.x + 12, rect.x + CELL_SIZE - 12]:
                    for my in [rect.y + 12, rect.y + CELL_SIZE - 12]:
                        pygame.draw.circle(game_surface, (130, 130, 130), (mx, my), 5)

def draw_bonuses():
    for bonus in bonuses[:]:
        bonus['pulse'] += 0.05
        pulse_size = math.sin(bonus['pulse']) * 3
        
        if bonus['type'] == "health":
            x, y = bonus['x'], bonus['y']
            rect = pygame.Rect(x - 12, y - 12, 24, 24)
            pygame.draw.rect(game_surface, WHITE, rect, border_radius=4)
            pygame.draw.rect(game_surface, (200, 200, 200), rect, width=2, border_radius=4)
            pygame.draw.rect(game_surface, (255, 50, 50), (x - 8, y - 2, 16, 4))
            pygame.draw.rect(game_surface, (255, 50, 50), (x - 2, y - 8, 4, 16))
            glow_rect = pygame.Rect(x - 18 + pulse_size, y - 18 + pulse_size, 36 - pulse_size*2, 36 - pulse_size*2)
            pygame.draw.rect(game_surface, (255, 100, 100, 50), glow_rect, width=2, border_radius=10)
        
        elif bonus['type'] == "shield":
            x, y = bonus['x'], bonus['y']
            glow_size = 22 + pulse_size
            for i in range(3, 0, -1):
                alpha = i / 3
                size = glow_size * alpha
                pygame.draw.circle(game_surface, (0, 150, 255, int(alpha * 100)), (int(x), int(y)), int(size), 2)
            pygame.draw.circle(game_surface, (100, 200, 255), (int(x), int(y)), 16)
            pygame.draw.circle(game_surface, (0, 150, 255), (int(x), int(y)), 16, 3)
            pygame.draw.polygon(game_surface, (255, 255, 255), [
                (x, y - 10),
                (x - 10, y + 5),
                (x - 4, y + 5),
                (x - 4, y + 12),
                (x + 4, y + 12),
                (x + 4, y + 5),
                (x + 10, y + 5)
            ])
        
        elif bonus['type'] == "fire":
            x, y = bonus['x'], bonus['y']
            for i in range(3, 0, -1):
                alpha = i / 3
                size = 20 * alpha + pulse_size
                pygame.draw.circle(game_surface, (255, 140, 0, int(alpha * 100)), (int(x), int(y)), int(size), 3)
            pygame.draw.circle(game_surface, (255, 200, 50), (int(x), int(y)), 14)
            pygame.draw.circle(game_surface, (255, 100, 0), (int(x), int(y)), 14, 2)
            for i in range(5):
                angle = bonus['pulse'] + i * 1.2
                dx = math.cos(angle) * 8
                dy = math.sin(angle) * 8
                pygame.draw.circle(game_surface, (255, 200, 50), (int(x + dx), int(y + dy)), 4)
        
        elif bonus['type'] == "electro":
            x, y = bonus['x'], bonus['y']
            for i in range(3, 0, -1):
                alpha = i / 3
                size = 20 * alpha + pulse_size
                pygame.draw.circle(game_surface, (0, 200, 255, int(alpha * 100)), (int(x), int(y)), int(size), 3)
            pygame.draw.circle(game_surface, (0, 150, 255), (int(x), int(y)), 14)
            pygame.draw.circle(game_surface, (0, 100, 255), (int(x), int(y)), 14, 2)
            for i in range(4):
                angle = bonus['pulse'] + i * 1.5
                dx = math.cos(angle) * 12
                dy = math.sin(angle) * 12
                pygame.draw.line(game_surface, (0, 200, 255), (x, y), (x + dx, y + dy), 3)
        
        elif bonus['type'] == "double":
            x, y = bonus['x'], bonus['y']
            for i in range(3, 0, -1):
                alpha = i / 3
                size = 20 * alpha + pulse_size
                pygame.draw.circle(game_surface, (255, 50, 50, int(alpha * 100)), (int(x), int(y)), int(size), 3)
            pygame.draw.circle(game_surface, (255, 100, 100), (int(x), int(y)), 14)
            pygame.draw.circle(game_surface, (255, 0, 0), (int(x), int(y)), 14, 2)
            pygame.draw.circle(game_surface, (255, 200, 200), (int(x - 6), int(y - 4)), 5)
            pygame.draw.circle(game_surface, (255, 200, 200), (int(x + 6), int(y + 4)), 5)
            pygame.draw.line(game_surface, (255, 200, 200), (x - 6, y - 4), (x - 12, y - 10), 2)
            pygame.draw.line(game_surface, (255, 200, 200), (x + 6, y + 4), (x + 12, y + 10), 2)
        
        bonus['timer'] -= 1
        if bonus['timer'] <= 0:
            bonuses.remove(bonus)

def start_game(diff):
    global player, bot, bullets, particles, game_map, difficulty, bonuses, SHIELD_ACTIVE
    global FIRE_ACTIVE, ELECTRO_ACTIVE, DOUBLE_ACTIVE, FIRE_TIMER, ELECTRO_TIMER, DOUBLE_TIMER
    global BOT_SLOW_TIMER, BOT_CURRENT_SPEED
    difficulty = diff
    game_map = generate_map()
    player = Tank(CELL_SIZE * 1 + CELL_SIZE//2, CELL_SIZE * 7 + CELL_SIZE//2, PLAYER_COLOR, "Игрок")
    bot = Tank(CELL_SIZE * 14 + CELL_SIZE//2, CELL_SIZE * 7 + CELL_SIZE//2, BOT_COLOR, "Бот")
    bullets.clear()
    particles.clear()
    bonuses.clear()
    SHIELD_ACTIVE = False
    FIRE_ACTIVE = False
    ELECTRO_ACTIVE = False
    DOUBLE_ACTIVE = False
    FIRE_TIMER = 0
    ELECTRO_TIMER = 0
    DOUBLE_TIMER = 0
    BOT_SLOW_TIMER = 0
    BOT_CURRENT_SPEED = 1.5
    return "game"

def draw_menu():
    game_surface.fill(LIGHT_BLUE)
    
    shadow = font_title.render("ТАНЧИКИ: ДУЭЛЬ", True, (100, 100, 150))
    title = font_title.render("ТАНЧИКИ: ДУЭЛЬ", True, (50, 50, 100))
    game_surface.blit(shadow, (GAME_WIDTH//2 - shadow.get_width()//2 + 4, 104))
    game_surface.blit(title, (GAME_WIDTH//2 - title.get_width()//2, 100))
    
    subtitle = font_medium.render("Выберите действие:", True, DARK_GRAY)
    game_surface.blit(subtitle, (GAME_WIDTH//2 - subtitle.get_width()//2, 200))
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    screen_width, screen_height = screen.get_size()
    scale_x = screen_width / GAME_WIDTH
    scale_y = screen_height / GAME_HEIGHT
    scale = min(scale_x, scale_y)
    offset_x = (screen_width - GAME_WIDTH * scale) // 2
    offset_y = (screen_height - GAME_HEIGHT * scale) // 2
    game_mouse_x = (mouse_x - offset_x) / scale
    game_mouse_y = (mouse_y - offset_y) / scale
    
    play_rect = pygame.Rect(GAME_WIDTH//2 - 150, 280, 300, 70)
    color = (100, 200, 100) if play_rect.collidepoint(game_mouse_x, game_mouse_y) else (80, 180, 80)
    pygame.draw.rect(game_surface, color, play_rect, border_radius=15)
    pygame.draw.rect(game_surface, WHITE, play_rect, width=3, border_radius=15)
    play_text = font_large.render("ИГРАТЬ", True, WHITE)
    game_surface.blit(play_text, (GAME_WIDTH//2 - play_text.get_width()//2, 295))
    
    how_rect = pygame.Rect(GAME_WIDTH//2 - 150, 380, 300, 70)
    color = (100, 150, 255) if how_rect.collidepoint(game_mouse_x, game_mouse_y) else (80, 130, 235)
    pygame.draw.rect(game_surface, color, how_rect, border_radius=15)
    pygame.draw.rect(game_surface, WHITE, how_rect, width=3, border_radius=15)
    how_text = font_large.render("КАК ИГРАТЬ", True, WHITE)
    game_surface.blit(how_text, (GAME_WIDTH//2 - how_text.get_width()//2, 395))
    
    return play_rect, how_rect

def draw_difficulty():
    game_surface.fill(LIGHT_BLUE)
    
    title = font_title.render("ВЫБЕРИТЕ СЛОЖНОСТЬ", True, (50, 50, 100))
    game_surface.blit(title, (GAME_WIDTH//2 - title.get_width()//2, 80))
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    screen_width, screen_height = screen.get_size()
    scale_x = screen_width / GAME_WIDTH
    scale_y = screen_height / GAME_HEIGHT
    scale = min(scale_x, scale_y)
    offset_x = (screen_width - GAME_WIDTH * scale) // 2
    offset_y = (screen_height - GAME_HEIGHT * scale) // 2
    game_mouse_x = (mouse_x - offset_x) / scale
    game_mouse_y = (mouse_y - offset_y) / scale
    
    buttons = []
    
    easy_rect = pygame.Rect(GAME_WIDTH//2 - 200, 220, 400, 80)
    color = (100, 255, 100) if easy_rect.collidepoint(game_mouse_x, game_mouse_y) else (80, 220, 80)
    pygame.draw.rect(game_surface, color, easy_rect, border_radius=15)
    pygame.draw.rect(game_surface, WHITE, easy_rect, width=3, border_radius=15)
    easy_text = font_large.render("ЛЁГКАЯ", True, WHITE)
    game_surface.blit(easy_text, (GAME_WIDTH//2 - easy_text.get_width()//2, 242))
    desc = font_small.render("Медленный бот, плохо целится", True, (50, 50, 50))
    game_surface.blit(desc, (GAME_WIDTH//2 - desc.get_width()//2, 310))
    buttons.append(("easy", easy_rect))
    
    normal_rect = pygame.Rect(GAME_WIDTH//2 - 200, 360, 400, 80)
    color = (255, 255, 100) if normal_rect.collidepoint(game_mouse_x, game_mouse_y) else (220, 220, 80)
    pygame.draw.rect(game_surface, color, normal_rect, border_radius=15)
    pygame.draw.rect(game_surface, WHITE, normal_rect, width=3, border_radius=15)
    normal_text = font_large.render("НОРМАЛЬНАЯ", True, WHITE)
    game_surface.blit(normal_text, (GAME_WIDTH//2 - normal_text.get_width()//2, 382))
    desc = font_small.render("Сбалансированный бот", True, (50, 50, 50))
    game_surface.blit(desc, (GAME_WIDTH//2 - desc.get_width()//2, 450))
    buttons.append(("normal", normal_rect))
    
    hard_rect = pygame.Rect(GAME_WIDTH//2 - 200, 500, 400, 80)
    color = (255, 100, 100) if hard_rect.collidepoint(game_mouse_x, game_mouse_y) else (220, 80, 80)
    pygame.draw.rect(game_surface, color, hard_rect, border_radius=15)
    pygame.draw.rect(game_surface, WHITE, hard_rect, width=3, border_radius=15)
    hard_text = font_large.render("СЛОЖНАЯ", True, WHITE)
    game_surface.blit(hard_text, (GAME_WIDTH//2 - hard_text.get_width()//2, 522))
    desc = font_small.render("Агрессивный бот-снайпер", True, (50, 50, 50))
    game_surface.blit(desc, (GAME_WIDTH//2 - desc.get_width()//2, 590))
    buttons.append(("hard", hard_rect))
    
    back_rect = pygame.Rect(30, 30, 120, 50)
    pygame.draw.rect(game_surface, (200, 200, 200), back_rect, border_radius=10)
    pygame.draw.rect(game_surface, WHITE, back_rect, width=2, border_radius=10)
    back_text = font_medium.render("НАЗАД", True, BLACK)
    game_surface.blit(back_text, (45, 38))
    buttons.append(("back", back_rect))
    
    return buttons

def draw_how_to():
    game_surface.fill(LIGHT_BLUE)
    
    title = font_title.render("КАК ИГРАТЬ", True, (50, 50, 100))
    game_surface.blit(title, (GAME_WIDTH//2 - title.get_width()//2, 40))
    
    instructions = [
        ("УПРАВЛЕНИЕ:", ""),
        ("", ""),
        ("W A S D", "Движение танка"),
        ("Мышь", "Наведение башни"),
        ("ЛКМ", "Выстрел"),
        ("ПРОБЕЛ", "Перезапуск после победы"),
        ("", ""),
        ("ОРУЖИЕ:", ""),
        ("", ""),
        ("🔥 Огненное", "Прожигает металл (8 сек)"),
        ("⚡ Электрическое", "Замедляет бота (8 сек)"),
        ("✨ Двойной", "2 ракеты (3 секунды)"),
        ("", ""),
        ("БОНУСЫ:", ""),
        ("", ""),
        ("❤️ Аптечка", "Восстанавливает 1 HP"),
        ("🛡️ Щит", "Блокирует 1 попадание"),
        ("", ""),
        ("ЦЕЛЬ:", "Уничтожьте вражеский танк!")
    ]
    
    y_pos = 140
    for line1, line2 in instructions:
        if line1 and not line2:
            text = font_medium.render(line1, True, (50, 50, 150))
            game_surface.blit(text, (100, y_pos))
            y_pos += 40
        elif line1 and line2:
            text1 = font_medium.render(line1, True, (80, 80, 80))
            text2 = font_small.render(line2, True, (100, 100, 100))
            game_surface.blit(text1, (150, y_pos))
            game_surface.blit(text2, (450, y_pos + 3))
            y_pos += 35
        else:
            y_pos += 10
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    screen_width, screen_height = screen.get_size()
    scale_x = screen_width / GAME_WIDTH
    scale_y = screen_height / GAME_HEIGHT
    scale = min(scale_x, scale_y)
    offset_x = (screen_width - GAME_WIDTH * scale) // 2
    offset_y = (screen_height - GAME_HEIGHT * scale) // 2
    game_mouse_x = (mouse_x - offset_x) / scale
    game_mouse_y = (mouse_y - offset_y) / scale
    
    back_rect = pygame.Rect(30, 30, 120, 50)
    color = (200, 200, 200) if back_rect.collidepoint(game_mouse_x, game_mouse_y) else (180, 180, 180)
    pygame.draw.rect(game_surface, color, back_rect, border_radius=10)
    pygame.draw.rect(game_surface, WHITE, back_rect, width=2, border_radius=10)
    back_text = font_medium.render("НАЗАД", True, BLACK)
    game_surface.blit(back_text, (45, 38))
    
    return back_rect

def game_loop():
    global game_state, player, bot, bullets, particles, game_map, bonuses, bonus_timer, SHIELD_ACTIVE
    global FIRE_ACTIVE, ELECTRO_ACTIVE, DOUBLE_ACTIVE, FIRE_TIMER, ELECTRO_TIMER, DOUBLE_TIMER
    global BOT_SLOW_TIMER, BOT_CURRENT_SPEED
    
    running = True
    bot_timer = 0
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        screen_width, screen_height = screen.get_size()
        scale_x = screen_width / GAME_WIDTH
        scale_y = screen_height / GAME_HEIGHT
        scale = min(scale_x, scale_y)
        offset_x = (screen_width - GAME_WIDTH * scale) // 2
        offset_y = (screen_height - GAME_HEIGHT * scale) // 2
        game_mouse_x = (mouse_x - offset_x) / scale
        game_mouse_y = (mouse_y - offset_y) / scale
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == "game":
                        game_state = "menu"
                        continue
                    elif game_state == "how_to":
                        game_state = "menu"
                        continue
                    elif game_state == "difficulty":
                        game_state = "menu"
                        continue
                if event.key == pygame.K_r and game_state == "game" and player:
                    if player.is_reloading:
                        player.reload_timer = RELOAD_TIME
                    else:
                        player.is_reloading = True
                        player.reload_timer = RELOAD_TIME
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "menu":
                    play_rect, how_rect = draw_menu()
                    if play_rect.collidepoint(game_mouse_x, game_mouse_y):
                        game_state = "difficulty"
                    elif how_rect.collidepoint(game_mouse_x, game_mouse_y):
                        game_state = "how_to"
                
                elif game_state == "difficulty":
                    buttons = draw_difficulty()
                    for diff, rect in buttons:
                        if rect.collidepoint(game_mouse_x, game_mouse_y):
                            if diff == "back":
                                game_state = "menu"
                            else:
                                game_state = start_game(diff)
                
                elif game_state == "how_to":
                    back_rect = draw_how_to()
                    if back_rect.collidepoint(game_mouse_x, game_mouse_y):
                        game_state = "menu"
                
                elif game_state == "game":
                    if player and player.hp > 0 and player.cooldown <= 0:
                        if player.shoot():
                            player.shoot_count += 1
                            
                            # ДВОЙНОЙ ВЫСТРЕЛ (если активен)
                            is_double = DOUBLE_ACTIVE
                            
                            # Огненный или электрический эффект
                            bullet_color = BULLET_COLOR
                            if FIRE_ACTIVE:
                                bullet_color = COLOR_FIRE
                            elif ELECTRO_ACTIVE:
                                bullet_color = COLOR_ELECTRO
                            
                            # Создаём пулю (или две)
                            for i in range(2 if is_double else 1):
                                angle_offset = 0
                                if is_double:
                                    angle_offset = 0.15 if i == 0 else -0.15
                                
                                angle_spread = player.angle + angle_offset + random.uniform(-0.02, 0.02)
                                bullets.append({
                                    'x': player.x + math.cos(angle_spread) * 40,
                                    'y': player.y + math.sin(angle_spread) * 40,
                                    'dx': math.cos(angle_spread) * BULLET_SPEED,
                                    'dy': math.sin(angle_spread) * BULLET_SPEED,
                                    'owner': 'player',
                                    'trail': [],
                                    'color': bullet_color,
                                    'is_fire': FIRE_ACTIVE,
                                    'is_electro': ELECTRO_ACTIVE
                                })
                            
                            player.cooldown = 12
                            create_explosion(player.x + math.cos(player.angle) * 35, 
                                           player.y + math.sin(player.angle) * 35, (200, 200, 200), 15)

        if game_state == "menu":
            draw_menu()
            draw_game_surface()
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        elif game_state == "how_to":
            draw_how_to()
            draw_game_surface()
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        elif game_state == "difficulty":
            draw_difficulty()
            draw_game_surface()
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        elif game_state == "game":
            if not player or not bot:
                continue
            
            player.update_reload()
            bot.update_reload()
            
            # === ОБНОВЛЕНИЕ ТАЙМЕРОВ ОРУЖИЯ ===
            if FIRE_ACTIVE:
                FIRE_TIMER -= 1
                if FIRE_TIMER <= 0:
                    FIRE_ACTIVE = False
                    print("🔥 Огненное оружие закончилось!")
            
            if ELECTRO_ACTIVE:
                ELECTRO_TIMER -= 1
                if ELECTRO_TIMER <= 0:
                    ELECTRO_ACTIVE = False
                    print("⚡ Электрическое оружие закончилось!")
            
            if DOUBLE_ACTIVE:
                DOUBLE_TIMER -= 1
                if DOUBLE_TIMER <= 0:
                    DOUBLE_ACTIVE = False
                    print("✨ Двойной выстрел закончился!")
            
            if BOT_SLOW_TIMER > 0:
                BOT_SLOW_TIMER -= 1
                BOT_CURRENT_SPEED = 0.5
            else:
                BOT_CURRENT_SPEED = 1.5
            
            # === СПАВН БОНУСОВ ===
            bonus_timer += 1
            if bonus_timer % 1200 == 0:
                if len(bonuses) < 5:
                    spawn_bonus()
            
            # === ПОДБОР БОНУСОВ ===
            if player and player.hp > 0:
                player_rect = player.get_rect()
                for bonus in bonuses[:]:
                    bx, by = bonus['x'], bonus['y']
                    bonus_rect = pygame.Rect(bx - 15, by - 15, 30, 30)
                    if player_rect.colliderect(bonus_rect):
                        if bonus['type'] == "health":
                            if player.hp < 3:
                                player.hp += 1
                                create_explosion(bx, by, (0, 255, 0), 20)
                                bonuses.remove(bonus)
                        elif bonus['type'] == "shield":
                            SHIELD_ACTIVE = True
                            create_explosion(bx, by, (0, 150, 255), 20)
                            bonuses.remove(bonus)
                        elif bonus['type'] == "fire":
                            FIRE_ACTIVE = True
                            FIRE_TIMER = 480
                            create_explosion(bx, by, (255, 140, 0), 30)
                            bonuses.remove(bonus)
                            print("🔥 Подобрано ОГНЕННОЕ оружие!")
                        elif bonus['type'] == "electro":
                            ELECTRO_ACTIVE = True
                            ELECTRO_TIMER = 480
                            create_explosion(bx, by, (0, 200, 255), 30)
                            bonuses.remove(bonus)
                            print("⚡ Подобрано ЭЛЕКТРИЧЕСКОЕ оружие!")
                        elif bonus['type'] == "double":
                            DOUBLE_ACTIVE = True
                            DOUBLE_TIMER = 180
                            create_explosion(bx, by, (255, 50, 50), 30)
                            bonuses.remove(bonus)
                            print("✨ Подобрано ДВОЙНОЙ ВЫСТРЕЛ на 3 секунды!")
            
            # === УПРАВЛЕНИЕ ИГРОКОМ ===
            keys = pygame.key.get_pressed()
            speed = 4
            new_x, new_y = player.x, player.y
            if keys[pygame.K_w]:
                new_y -= speed
            if keys[pygame.K_s]:
                new_y += speed
            if keys[pygame.K_a]:
                new_x -= speed
            if keys[pygame.K_d]:
                new_x += speed
            if can_move_to(new_x, new_y, player):
                player.x, player.y = new_x, new_y
            
            player.angle = math.atan2(game_mouse_y - player.y, game_mouse_x - player.x)
            
            # === БОТ ===
            if bot.hp > 0:
                dx_bot = player.x - bot.x
                dy_bot = player.y - bot.y
                dist = math.sqrt(dx_bot**2 + dy_bot**2)
                
                if dist > 400:
                    bot.state = "chase"
                elif dist < 180:
                    bot.state = "retreat"
                else:
                    bot.state = "attack"
                
                if dist > 0:
                    target_angle = math.atan2(dy_bot, dx_bot)
                    
                    if difficulty == "easy":
                        angle_diff = target_angle - bot.angle
                        while angle_diff > math.pi:
                            angle_diff -= 2 * math.pi
                        while angle_diff < -math.pi:
                            angle_diff += 2 * math.pi
                        bot.angle += angle_diff * 0.06
                        
                        if bot.state == "chase":
                            dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                            if dx_move and dy_move:
                                new_x, new_y = bot.x + dx_move * 1.0, bot.y + dy_move * 1.0
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                                else:
                                    for angle_try in [0.5, -0.5, 1.0, -1.0]:
                                        try_angle = target_angle + angle_try
                                        try_x = bot.x + math.cos(try_angle) * 2
                                        try_y = bot.y + math.sin(try_angle) * 2
                                        if can_move_to(try_x, try_y, bot):
                                            bot.x, bot.y = try_x, try_y
                                            break
                        elif bot.state == "retreat":
                            dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                            if dx_move and dy_move:
                                new_x, new_y = bot.x - dx_move * 0.8, bot.y - dy_move * 0.8
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                        
                        if bot.cooldown <= 0 and dist < 500:
                            check_x = bot.x + math.cos(bot.angle) * 60
                            check_y = bot.y + math.sin(bot.angle) * 60
                            gx = int(check_x // CELL_SIZE)
                            gy = int(check_y // CELL_SIZE)
                            if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                                if game_map[gy][gx] not in [1, 2]:
                                    if bot.shoot():
                                        bullets.append({
                                            'x': bot.x + math.cos(bot.angle) * 40,
                                            'y': bot.y + math.sin(bot.angle) * 40,
                                            'dx': math.cos(bot.angle) * BULLET_SPEED * 0.7,
                                            'dy': math.sin(bot.angle) * BULLET_SPEED * 0.7,
                                            'owner': 'bot',
                                            'trail': [],
                                            'color': BULLET_COLOR,
                                            'is_fire': False,
                                            'is_electro': False
                                        })
                                        bot.cooldown = 30
                                        bot.shoot_count += 1
                    
                    elif difficulty == "normal":
                        bot.angle = target_angle
                        
                        if bot.state == "chase":
                            dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                            if dx_move and dy_move:
                                new_x, new_y = bot.x + dx_move * 1.5, bot.y + dy_move * 1.5
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                                else:
                                    for angle_try in [0.5, -0.5, 1.0, -1.0]:
                                        try_angle = target_angle + angle_try
                                        try_x = bot.x + math.cos(try_angle) * 2
                                        try_y = bot.y + math.sin(try_angle) * 2
                                        if can_move_to(try_x, try_y, bot):
                                            bot.x, bot.y = try_x, try_y
                                            break
                        elif bot.state == "retreat":
                            dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                            if dx_move and dy_move:
                                new_x, new_y = bot.x - dx_move * 1.0, bot.y - dy_move * 1.0
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                        else:
                            angle_to_player = math.atan2(dy_bot, dx_bot)
                            flank_angle = angle_to_player + 0.7 if bot_timer % 150 < 75 else angle_to_player - 0.7
                            new_x = bot.x + math.cos(flank_angle) * 2.0
                            new_y = bot.y + math.sin(flank_angle) * 2.0
                            if can_move_to(new_x, new_y, bot):
                                bot.x, bot.y = new_x, new_y
                            else:
                                dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                                if dx_move and dy_move:
                                    new_x, new_y = bot.x + dx_move * 1.0, bot.y + dy_move * 1.0
                                    if can_move_to(new_x, new_y, bot):
                                        bot.x, bot.y = new_x, new_y
                        
                        if bot.cooldown <= 0 and dist < 550:
                            check_x = bot.x + math.cos(bot.angle) * 60
                            check_y = bot.y + math.sin(bot.angle) * 60
                            gx = int(check_x // CELL_SIZE)
                            gy = int(check_y // CELL_SIZE)
                            if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                                if game_map[gy][gx] not in [1, 2]:
                                    if bot.shoot():
                                        if random.random() < 0.08:
                                            wrong_angle = bot.angle + random.uniform(-0.2, 0.2)
                                        else:
                                            wrong_angle = bot.angle
                                        bullets.append({
                                            'x': bot.x + math.cos(wrong_angle) * 40,
                                            'y': bot.y + math.sin(wrong_angle) * 40,
                                            'dx': math.cos(wrong_angle) * BULLET_SPEED * 0.95,
                                            'dy': math.sin(wrong_angle) * BULLET_SPEED * 0.95,
                                            'owner': 'bot',
                                            'trail': [],
                                            'color': BULLET_COLOR,
                                            'is_fire': False,
                                            'is_electro': False
                                        })
                                        bot.cooldown = 18
                                        bot.shoot_count += 1
                    
                    else:  # hard
                        bot.angle = target_angle
                        
                        if bot.state == "chase":
                            dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                            if dx_move and dy_move:
                                new_x, new_y = bot.x + dx_move * 2.2, bot.y + dy_move * 2.2
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                                else:
                                    for angle_try in [0.3, -0.3, 0.6, -0.6, 0.9, -0.9, 1.2, -1.2]:
                                        try_angle = target_angle + angle_try
                                        try_x = bot.x + math.cos(try_angle) * 2.5
                                        try_y = bot.y + math.sin(try_angle) * 2.5
                                        if can_move_to(try_x, try_y, bot):
                                            bot.x, bot.y = try_x, try_y
                                            break
                        elif bot.state == "retreat":
                            dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                            if dx_move and dy_move:
                                new_x, new_y = bot.x - dx_move * 1.5, bot.y - dy_move * 1.5
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                                else:
                                    for angle_try in [0.5, -0.5, 1.0, -1.0]:
                                        try_angle = target_angle + math.pi + angle_try
                                        try_x = bot.x + math.cos(try_angle) * 2
                                        try_y = bot.y + math.sin(try_angle) * 2
                                        if can_move_to(try_x, try_y, bot):
                                            bot.x, bot.y = try_x, try_y
                                            break
                        else:
                            angle_to_player = math.atan2(dy_bot, dx_bot)
                            flank_angle = angle_to_player + 1.0 if bot_timer % 200 < 100 else angle_to_player - 1.0
                            new_x = bot.x + math.cos(flank_angle) * 2.5
                            new_y = bot.y + math.sin(flank_angle) * 2.5
                            if can_move_to(new_x, new_y, bot):
                                bot.x, bot.y = new_x, new_y
                            else:
                                flank_angle = angle_to_player - 1.0 if bot_timer % 200 < 100 else angle_to_player + 1.0
                                new_x = bot.x + math.cos(flank_angle) * 2.5
                                new_y = bot.y + math.sin(flank_angle) * 2.5
                                if can_move_to(new_x, new_y, bot):
                                    bot.x, bot.y = new_x, new_y
                                else:
                                    dx_move, dy_move = find_path_towards(bot.x, bot.y, player.x, player.y)
                                    if dx_move and dy_move:
                                        new_x, new_y = bot.x + dx_move * 1.5, bot.y + dy_move * 1.5
                                        if can_move_to(new_x, new_y, bot):
                                            bot.x, bot.y = new_x, new_y
                        
                        if bot.cooldown <= 0 and dist < 650:
                            check_x = bot.x + math.cos(bot.angle) * 60
                            check_y = bot.y + math.sin(bot.angle) * 60
                            gx = int(check_x // CELL_SIZE)
                            gy = int(check_y // CELL_SIZE)
                            if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                                if game_map[gy][gx] not in [1, 2]:
                                    if bot.shoot():
                                        if random.random() < 0.05:
                                            wrong_angle = bot.angle + random.uniform(-0.15, 0.15)
                                        else:
                                            wrong_angle = bot.angle
                                        bullets.append({
                                            'x': bot.x + math.cos(wrong_angle) * 40,
                                            'y': bot.y + math.sin(wrong_angle) * 40,
                                            'dx': math.cos(wrong_angle) * BULLET_SPEED * 1.05,
                                            'dy': math.sin(wrong_angle) * BULLET_SPEED * 1.05,
                                            'owner': 'bot',
                                            'trail': [],
                                            'color': BULLET_COLOR,
                                            'is_fire': False,
                                            'is_electro': False
                                        })
                                        bot.cooldown = 13
                                        bot.shoot_count += 1
                                        create_explosion(bot.x + math.cos(bot.angle) * 35, 
                                                       bot.y + math.sin(bot.angle) * 35, (200, 150, 50), 12)

            if player.cooldown > 0:
                player.cooldown -= 1
            if bot.cooldown > 0:
                bot.cooldown -= 1
            bot_timer += 1

            # === ПУЛИ ===
            for bullet in bullets[:]:
                bullet['trail'].append((bullet['x'], bullet['y']))
                if len(bullet['trail']) > 8:
                    bullet['trail'].pop(0)
                    
                bullet['x'] += bullet['dx']
                bullet['y'] += bullet['dy']
                
                if bullet['x'] < 0 or bullet['x'] > GAME_WIDTH or bullet['y'] < 0 or bullet['y'] > GAME_HEIGHT:
                    create_explosion(bullet['x'], bullet['y'], (100, 100, 200), 15)
                    bullets.remove(bullet)
                    continue

                gx = int(bullet['x'] // CELL_SIZE)
                gy = int(bullet['y'] // CELL_SIZE)
                if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                    cell = game_map[gy][gx]
                    
                    # Огненная пуля прожигает металл!
                    if bullet.get('is_fire', False) and cell == 2:
                        game_map[gy][gx] = 0
                        create_explosion(bullet['x'], bullet['y'], (255, 140, 0), 30)
                        bullets.remove(bullet)
                        continue
                    
                    if cell == 1:
                        game_map[gy][gx] = 0
                        create_explosion(bullet['x'], bullet['y'], (200, 100, 50), 20)
                        bullets.remove(bullet)
                        continue
                    elif cell == 2:
                        create_explosion(bullet['x'], bullet['y'], (150, 150, 150), 15)
                        bullets.remove(bullet)
                        continue

                # === ПОПАДАНИЕ В ИГРОКА ===
                if bullet['owner'] == 'bot' and player.hp > 0:
                    if player.get_rect().collidepoint(bullet['x'], bullet['y']):
                        if SHIELD_ACTIVE:
                            SHIELD_ACTIVE = False
                            create_explosion(bullet['x'], bullet['y'], (0, 150, 255), 30)
                            bullets.remove(bullet)
                            continue
                        else:
                            player.hp -= 1
                            player.hit_effect = 10
                            create_explosion(bullet['x'], bullet['y'], (255, 100, 100), 30)
                            bullets.remove(bullet)
                            continue

                # === ПОПАДАНИЕ В БОТА ===
                if bullet['owner'] == 'player' and bot.hp > 0:
                    if bot.get_rect().collidepoint(bullet['x'], bullet['y']):
                        bot.hp -= 1
                        bot.hit_effect = 10
                        
                        # Электрическая пуля замедляет бота
                        if bullet.get('is_electro', False):
                            BOT_SLOW_TIMER = 120
                            print("⚡ Бот замедлен на 2 секунды!")
                            create_explosion(bullet['x'], bullet['y'], (0, 200, 255), 40)
                        else:
                            create_explosion(bullet['x'], bullet['y'], (255, 215, 0), 30)
                        
                        bullets.remove(bullet)
                        continue

            for particle in particles[:]:
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                particle['life'] -= 1
                particle['dx'] *= 0.95
                particle['dy'] *= 0.95
                if particle['life'] <= 0:
                    particles.remove(particle)

            # === ОТРИСОВКА ===
            game_surface.fill(COLOR_GRASS)
            
            for x in range(0, GAME_WIDTH, CELL_SIZE):
                pygame.draw.line(game_surface, (180, 220, 180), (x, 0), (x, GAME_HEIGHT), 1)
            for y in range(0, GAME_HEIGHT, CELL_SIZE):
                pygame.draw.line(game_surface, (180, 220, 180), (0, y), (GAME_WIDTH, y), 1)
            
            draw_map()
            draw_bonuses()
            
            player.draw(game_surface)
            bot.draw(game_surface)
            
            for bullet in bullets:
                color = bullet.get('color', BULLET_COLOR)
                for i, (tx, ty) in enumerate(bullet['trail']):
                    alpha = i / len(bullet['trail'])
                    size = int(BULLET_RADIUS * alpha * 0.7)
                    if size > 0:
                        pygame.draw.circle(game_surface, color, (int(tx), int(ty)), size)
                pygame.draw.circle(game_surface, color, (int(bullet['x']), int(bullet['y'])), BULLET_RADIUS + 3)
                pygame.draw.circle(game_surface, WHITE, (int(bullet['x']), int(bullet['y'])), BULLET_RADIUS)
                pygame.draw.circle(game_surface, (255, 255, 200), (int(bullet['x']), int(bullet['y'])), BULLET_RADIUS//2)
            
            for particle in particles:
                alpha = particle['life'] / 35
                size = int(particle['size'] * alpha)
                if size > 0:
                    pygame.draw.circle(game_surface, particle['color'], (int(particle['x']), int(particle['y'])), size)
            
            # === ИНТЕРФЕЙС ===
            hp_color_player = (255, 50, 50) if player.hp == 1 else (50, 255, 50)
            hp_color_bot = (255, 50, 50) if bot.hp == 1 else (50, 255, 50)
            
            player_hp_text = font_large.render(f"ИГРОК HP: {player.hp}/3", True, hp_color_player)
            game_surface.blit(player_hp_text, (10, 10))
            
            bot_hp_text = font_large.render(f"БОТ HP: {bot.hp}/3", True, hp_color_bot)
            game_surface.blit(bot_hp_text, (GAME_WIDTH - 10 - bot_hp_text.get_width(), 10))
            
            ammo_color = (255, 255, 0) if player.ammo <= 1 else (255, 255, 255)
            ammo_text = font_medium.render(f"ПАТРОНЫ: {player.ammo}/{MAX_AMMO}", True, ammo_color)
            game_surface.blit(ammo_text, (10, 60))
            
            if player.is_reloading:
                reload_text = font_medium.render("ПЕРЕЗАРЯДКА...", True, (255, 100, 100))
                game_surface.blit(reload_text, (10, 100))
            
            if SHIELD_ACTIVE:
                shield_text = font_medium.render("🛡️ ЩИТ АКТИВЕН", True, (0, 150, 255))
                game_surface.blit(shield_text, (10, 140))
            
            if FIRE_ACTIVE:
                fire_text = font_medium.render("🔥 ОГНЕННОЕ", True, (255, 140, 0))
                game_surface.blit(fire_text, (10, 180))
                fire_timer_text = font_small.render(f"{FIRE_TIMER // 60 + 1} сек", True, (255, 200, 100))
                game_surface.blit(fire_timer_text, (180, 184))
            
            if ELECTRO_ACTIVE:
                electro_text = font_medium.render("⚡ ЭЛЕКТРИЧЕСКОЕ", True, (0, 200, 255))
                game_surface.blit(electro_text, (10, 220))
                electro_timer_text = font_small.render(f"{ELECTRO_TIMER // 60 + 1} сек", True, (100, 200, 255))
                game_surface.blit(electro_timer_text, (260, 224))
            
            if DOUBLE_ACTIVE:
                double_text = font_medium.render("✨ ДВОЙНОЙ", True, (255, 50, 50))
                game_surface.blit(double_text, (10, 260))
                double_timer_text = font_small.render(f"{DOUBLE_TIMER // 60 + 1} сек", True, (255, 100, 100))
                game_surface.blit(double_timer_text, (200, 264))
            
            state_names = {"idle": "ОЖИДАНИЕ", "chase": "ПРЕСЛЕДОВАНИЕ", "attack": "АТАКА", "retreat": "ОТСТУПЛЕНИЕ"}
            state_text = font_small.render(f"БОТ: {state_names.get(bot.state, '')}", True, (200, 200, 200))
            game_surface.blit(state_text, (GAME_WIDTH // 2 - state_text.get_width() // 2, 10))
            
            if BOT_SLOW_TIMER > 0:
                slow_text = font_small.render("⚡ ЗАМЕДЛЕН", True, (0, 200, 255))
                game_surface.blit(slow_text, (GAME_WIDTH // 2 + 100, 10))
            
            # === ПРОВЕРКА ПОБЕДЫ ===
            if player.hp <= 0:
                overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill((0, 0, 0))
                game_surface.blit(overlay, (0, 0))
                
                win_text = font_title.render("БОТ ПОБЕДИЛ!", True, (255, 215, 0))
                game_surface.blit(win_text, (GAME_WIDTH//2 - win_text.get_width()//2, GAME_HEIGHT//2 - 60))
                restart_text = font_medium.render("Нажми ПРОБЕЛ для реванша или ESC для выхода", True, WHITE)
                game_surface.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, GAME_HEIGHT//2 + 30))
                
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            player.hp = 3
                            bot.hp = 3
                            player.ammo = MAX_AMMO
                            player.is_reloading = False
                            bot.ammo = MAX_AMMO
                            bot.is_reloading = False
                            player.x, player.y = CELL_SIZE * 1 + CELL_SIZE//2, CELL_SIZE * 7 + CELL_SIZE//2
                            bot.x, bot.y = CELL_SIZE * 14 + CELL_SIZE//2, CELL_SIZE * 7 + CELL_SIZE//2
                            bullets.clear()
                            particles.clear()
                            bonuses.clear()
                            player.shoot_count = 0
                            bot.shoot_count = 0
                            SHIELD_ACTIVE = False
                            FIRE_ACTIVE = False
                            ELECTRO_ACTIVE = False
                            DOUBLE_ACTIVE = False
                            FIRE_TIMER = 0
                            ELECTRO_TIMER = 0
                            DOUBLE_TIMER = 0
                            BOT_SLOW_TIMER = 0
                            BOT_CURRENT_SPEED = 1.5
                            game_map = generate_map()
                        elif event.key == pygame.K_ESCAPE:
                            game_state = "menu"
                            
            elif bot.hp <= 0:
                overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill((0, 0, 0))
                game_surface.blit(overlay, (0, 0))
                
                win_text = font_title.render("ИГРОК ПОБЕДИЛ!", True, (148, 0, 211))
                game_surface.blit(win_text, (GAME_WIDTH//2 - win_text.get_width()//2, GAME_HEIGHT//2 - 60))
                restart_text = font_medium.render("Нажми ПРОБЕЛ для реванша или ESC для выхода", True, WHITE)
                game_surface.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, GAME_HEIGHT//2 + 30))
                
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            player.hp = 3
                            bot.hp = 3
                            player.ammo = MAX_AMMO
                            player.is_reloading = False
                            bot.ammo = MAX_AMMO
                            bot.is_reloading = False
                            player.x, player.y = CELL_SIZE * 1 + CELL_SIZE//2, CELL_SIZE * 7 + CELL_SIZE//2
                            bot.x, bot.y = CELL_SIZE * 14 + CELL_SIZE//2, CELL_SIZE * 7 + CELL_SIZE//2
                            bullets.clear()
                            particles.clear()
                            bonuses.clear()
                            player.shoot_count = 0
                            bot.shoot_count = 0
                            SHIELD_ACTIVE = False
                            FIRE_ACTIVE = False
                            ELECTRO_ACTIVE = False
                            DOUBLE_ACTIVE = False
                            FIRE_TIMER = 0
                            ELECTRO_TIMER = 0
                            DOUBLE_TIMER = 0
                            BOT_SLOW_TIMER = 0
                            BOT_CURRENT_SPEED = 1.5
                            game_map = generate_map()
                        elif event.key == pygame.K_ESCAPE:
                            game_state = "menu"
            
            draw_game_surface()
            pygame.display.flip()
            clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()