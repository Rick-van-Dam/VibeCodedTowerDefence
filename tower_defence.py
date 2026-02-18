#!/usr/bin/env python3
"""
Tower Defence Game
A simple but complete tower defence game built with Pygame
"""

import pygame
import math
import random
from enum import Enum
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GREEN = (0, 128, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Game settings
STARTING_MONEY = 500
STARTING_LIVES = 20
TOWER_COST = 100
UPGRADE_COST = 150


class GameState(Enum):
    """Game state enumeration"""
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5


class EnemyType(Enum):
    """Enemy type enumeration"""
    BASIC = 1
    FAST = 2
    TANK = 3


class TowerType(Enum):
    """Tower type enumeration"""
    BASIC = 1
    SNIPER = 2
    SPLASH = 3


class Enemy:
    """Enemy class representing hostile units"""
    
    def __init__(self, enemy_type: EnemyType, path: List[Tuple[int, int]]):
        self.type = enemy_type
        self.path = path
        self.path_index = 0
        self.x, self.y = path[0]
        self.health = self._get_max_health()
        self.max_health = self.health
        self.speed = self._get_speed()
        self.reward = self._get_reward()
        self.color = self._get_color()
        self.radius = 8
        
    def _get_max_health(self) -> int:
        """Get max health based on enemy type"""
        if self.type == EnemyType.BASIC:
            return 100
        elif self.type == EnemyType.FAST:
            return 60
        elif self.type == EnemyType.TANK:
            return 250
        return 100
    
    def _get_speed(self) -> float:
        """Get speed based on enemy type"""
        if self.type == EnemyType.BASIC:
            return 2.0
        elif self.type == EnemyType.FAST:
            return 4.0
        elif self.type == EnemyType.TANK:
            return 1.0
        return 2.0
    
    def _get_reward(self) -> int:
        """Get money reward for killing this enemy"""
        if self.type == EnemyType.BASIC:
            return 20
        elif self.type == EnemyType.FAST:
            return 15
        elif self.type == EnemyType.TANK:
            return 50
        return 20
    
    def _get_color(self) -> Tuple[int, int, int]:
        """Get color based on enemy type"""
        if self.type == EnemyType.BASIC:
            return RED
        elif self.type == EnemyType.FAST:
            return ORANGE
        elif self.type == EnemyType.TANK:
            return PURPLE
        return RED
    
    def move(self) -> bool:
        """Move enemy along path. Returns True if reached end"""
        if self.path_index >= len(self.path) - 1:
            return True
        
        target_x, target_y = self.path[self.path_index + 1]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance <= self.speed:
            self.path_index += 1
            if self.path_index >= len(self.path) - 1:
                return True
            self.x, self.y = self.path[self.path_index]
        else:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        
        return False
    
    def take_damage(self, damage: int) -> bool:
        """Take damage. Returns True if enemy is killed"""
        self.health -= damage
        return self.health <= 0
    
    def draw(self, screen: pygame.Surface):
        """Draw enemy on screen"""
        # Draw enemy circle
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # Draw health bar
        bar_width = 20
        bar_height = 4
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, RED, 
                        (int(self.x - bar_width/2), int(self.y - self.radius - 8), 
                         bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, 
                        (int(self.x - bar_width/2), int(self.y - self.radius - 8), 
                         int(bar_width * health_ratio), bar_height))


class Projectile:
    """Projectile class for tower attacks"""
    
    def __init__(self, x: float, y: float, target: Enemy, damage: int, speed: float = 8.0):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.radius = 4
    
    def move(self) -> bool:
        """Move towards target. Returns True if hit target"""
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance <= self.speed:
            return True
        
        self.x += (dx / distance) * self.speed
        self.y += (dy / distance) * self.speed
        return False
    
    def draw(self, screen: pygame.Surface):
        """Draw projectile on screen"""
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)


class Tower:
    """Tower class for defensive structures"""
    
    def __init__(self, x: int, y: int, tower_type: TowerType = TowerType.BASIC):
        self.x = x
        self.y = y
        self.type = tower_type
        self.level = 1
        self.range = self._get_range()
        self.damage = self._get_damage()
        self.fire_rate = self._get_fire_rate()
        self.last_shot = 0
        self.target: Optional[Enemy] = None
        self.color = self._get_color()
        self.radius = 15
    
    def _get_range(self) -> int:
        """Get range based on tower type and level"""
        base_range = 150 if self.type == TowerType.SNIPER else 120 if self.type == TowerType.BASIC else 100
        return base_range + (self.level - 1) * 20
    
    def _get_damage(self) -> int:
        """Get damage based on tower type and level"""
        base_damage = 50 if self.type == TowerType.SNIPER else 30 if self.type == TowerType.BASIC else 20
        return base_damage + (self.level - 1) * 15
    
    def _get_fire_rate(self) -> int:
        """Get fire rate (frames between shots) based on tower type"""
        if self.type == TowerType.BASIC:
            return 30  # Shoots every 30 frames (0.5 seconds at 60 FPS)
        elif self.type == TowerType.SNIPER:
            return 90  # Slower fire rate
        elif self.type == TowerType.SPLASH:
            return 60  # Medium fire rate
        return 30
    
    def _get_color(self) -> Tuple[int, int, int]:
        """Get color based on tower type"""
        if self.type == TowerType.BASIC:
            return BLUE
        elif self.type == TowerType.SNIPER:
            return DARK_GREEN
        elif self.type == TowerType.SPLASH:
            return PURPLE
        return BLUE
    
    def upgrade(self):
        """Upgrade tower to next level"""
        if self.level < 3:
            self.level += 1
            self.range = self._get_range()
            self.damage = self._get_damage()
    
    def can_upgrade(self) -> bool:
        """Check if tower can be upgraded"""
        return self.level < 3
    
    def find_target(self, enemies: List[Enemy]) -> Optional[Enemy]:
        """Find closest enemy in range"""
        closest = None
        min_distance = float('inf')
        
        for enemy in enemies:
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance <= self.range and distance < min_distance:
                closest = enemy
                min_distance = distance
        
        return closest
    
    def shoot(self, current_frame: int) -> Optional[Projectile]:
        """Attempt to shoot at target. Returns projectile if shot"""
        if current_frame - self.last_shot >= self.fire_rate and self.target:
            self.last_shot = current_frame
            return Projectile(self.x, self.y, self.target, self.damage)
        return None
    
    def draw(self, screen: pygame.Surface, show_range: bool = False):
        """Draw tower on screen"""
        if show_range:
            # Draw range circle
            pygame.draw.circle(screen, LIGHT_GRAY, (self.x, self.y), self.range, 1)
        
        # Draw tower
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), self.radius, 2)
        
        # Draw level indicator
        font = pygame.font.Font(None, 20)
        level_text = font.render(str(self.level), True, WHITE)
        text_rect = level_text.get_rect(center=(self.x, self.y))
        screen.blit(level_text, text_rect)


class Wave:
    """Wave class for managing enemy spawns"""
    
    def __init__(self, wave_number: int, path: List[Tuple[int, int]]):
        self.wave_number = wave_number
        self.path = path
        self.enemies_to_spawn = self._generate_enemies()
        self.spawn_timer = 0
        self.spawn_delay = 60  # Frames between spawns
        self.complete = False
    
    def _generate_enemies(self) -> List[EnemyType]:
        """Generate enemy list for this wave"""
        enemies = []
        # Basic enemies
        basic_count = min(5 + self.wave_number * 2, 20)
        enemies.extend([EnemyType.BASIC] * basic_count)
        
        # Add fast enemies after wave 2
        if self.wave_number >= 2:
            fast_count = min(self.wave_number, 10)
            enemies.extend([EnemyType.FAST] * fast_count)
        
        # Add tank enemies after wave 4
        if self.wave_number >= 4:
            tank_count = min((self.wave_number - 3) // 2, 5)
            enemies.extend([EnemyType.TANK] * tank_count)
        
        random.shuffle(enemies)
        return enemies
    
    def update(self, current_frame: int) -> Optional[Enemy]:
        """Update wave and spawn enemies. Returns enemy if spawned"""
        if not self.enemies_to_spawn:
            self.complete = True
            return None
        
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            enemy_type = self.enemies_to_spawn.pop(0)
            return Enemy(enemy_type, self.path)
        
        return None


class Game:
    """Main game class"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tower Defence")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.state = GameState.MENU
        self.frame_count = 0
        
        # Path for enemies
        self.path = [
            (0, 200), (200, 200), (200, 400), (400, 400),
            (400, 200), (600, 200), (600, 500), (800, 500),
            (800, 300), (1000, 300)
        ]
        
        # Game objects
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        
        # Game variables
        self.money = STARTING_MONEY
        self.lives = STARTING_LIVES
        self.current_wave = 0
        self.wave: Optional[Wave] = None
        self.wave_active = False
        
        # UI state
        self.selected_tower: Optional[Tower] = None
        self.placing_tower = False
        self.hover_pos: Optional[Tuple[int, int]] = None
    
    def reset_game(self):
        """Reset game to initial state"""
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.money = STARTING_MONEY
        self.lives = STARTING_LIVES
        self.current_wave = 0
        self.wave = None
        self.wave_active = False
        self.selected_tower = None
        self.placing_tower = False
        self.frame_count = 0
        self.state = GameState.PLAYING
    
    def start_next_wave(self):
        """Start the next wave of enemies"""
        self.current_wave += 1
        self.wave = Wave(self.current_wave, self.path)
        self.wave_active = True
        # Bonus money for completing previous wave
        if self.current_wave > 1:
            self.money += 50
    
    def can_place_tower(self, x: int, y: int) -> bool:
        """Check if tower can be placed at position"""
        # Check if too close to path
        for px, py in self.path:
            if math.sqrt((x - px)**2 + (y - py)**2) < 40:
                return False
        
        # Check if too close to other towers
        for tower in self.towers:
            if math.sqrt((x - tower.x)**2 + (y - tower.y)**2) < 50:
                return False
        
        # Check if in game area (not in UI panel)
        if y > SCREEN_HEIGHT - 100:
            return False
        
        return True
    
    def place_tower(self, x: int, y: int):
        """Place a tower at the given position"""
        if self.money >= TOWER_COST and self.can_place_tower(x, y):
            self.towers.append(Tower(x, y))
            self.money -= TOWER_COST
            self.placing_tower = False
    
    def get_tower_at_pos(self, x: int, y: int) -> Optional[Tower]:
        """Get tower at position if exists"""
        for tower in self.towers:
            if math.sqrt((x - tower.x)**2 + (y - tower.y)**2) <= tower.radius:
                return tower
        return None
    
    def upgrade_tower(self, tower: Tower):
        """Upgrade the specified tower"""
        if self.money >= UPGRADE_COST and tower.can_upgrade():
            tower.upgrade()
            self.money -= UPGRADE_COST
    
    def update(self):
        """Update game state"""
        if self.state != GameState.PLAYING:
            return
        
        self.frame_count += 1
        
        # Update wave
        if self.wave and not self.wave.complete:
            enemy = self.wave.update(self.frame_count)
            if enemy:
                self.enemies.append(enemy)
        elif self.wave and self.wave.complete and not self.enemies:
            # Wave complete, check victory
            if self.current_wave >= 10:
                self.state = GameState.VICTORY
            else:
                self.wave_active = False
        
        # Update enemies
        for enemy in self.enemies[:]:
            if enemy.move():
                self.lives -= 1
                self.enemies.remove(enemy)
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
        
        # Update towers
        for tower in self.towers:
            tower.target = tower.find_target(self.enemies)
            projectile = tower.shoot(self.frame_count)
            if projectile:
                self.projectiles.append(projectile)
        
        # Update projectiles
        for projectile in self.projectiles[:]:
            if projectile.move() or projectile.target not in self.enemies:
                if projectile.target in self.enemies:
                    if projectile.target.take_damage(projectile.damage):
                        self.money += projectile.target.reward
                        self.enemies.remove(projectile.target)
                self.projectiles.remove(projectile)
    
    def draw_path(self):
        """Draw the enemy path"""
        for i in range(len(self.path) - 1):
            pygame.draw.line(self.screen, GRAY, self.path[i], self.path[i + 1], 30)
    
    def draw_ui(self):
        """Draw UI elements"""
        # UI panel background
        pygame.draw.rect(self.screen, LIGHT_GRAY, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        
        # Money
        money_text = self.font.render(f"Money: ${self.money}", True, BLACK)
        self.screen.blit(money_text, (20, SCREEN_HEIGHT - 80))
        
        # Lives
        lives_text = self.font.render(f"Lives: {self.lives}", True, BLACK)
        self.screen.blit(lives_text, (20, SCREEN_HEIGHT - 40))
        
        # Wave
        wave_text = self.font.render(f"Wave: {self.current_wave}", True, BLACK)
        self.screen.blit(wave_text, (250, SCREEN_HEIGHT - 80))
        
        # Next wave button
        button_color = GREEN if not self.wave_active else GRAY
        pygame.draw.rect(self.screen, button_color, (250, SCREEN_HEIGHT - 50, 150, 35))
        button_text = self.small_font.render("Next Wave" if not self.wave_active else "Wave Active", True, BLACK)
        self.screen.blit(button_text, (260, SCREEN_HEIGHT - 45))
        
        # Place tower button
        button_color = BLUE if self.money >= TOWER_COST else GRAY
        pygame.draw.rect(self.screen, button_color, (450, SCREEN_HEIGHT - 80, 150, 35))
        tower_text = self.small_font.render(f"Tower (${TOWER_COST})", True, WHITE)
        self.screen.blit(tower_text, (460, SCREEN_HEIGHT - 75))
        
        # Upgrade button
        if self.selected_tower and self.selected_tower.can_upgrade():
            button_color = YELLOW if self.money >= UPGRADE_COST else GRAY
            pygame.draw.rect(self.screen, button_color, (450, SCREEN_HEIGHT - 40, 150, 35))
            upgrade_text = self.small_font.render(f"Upgrade (${UPGRADE_COST})", True, BLACK)
            self.screen.blit(upgrade_text, (455, SCREEN_HEIGHT - 35))
        
        # Instructions
        inst_text = self.small_font.render("Click tower to select/upgrade | Right-click to deselect", True, BLACK)
        self.screen.blit(inst_text, (650, SCREEN_HEIGHT - 60))
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BLACK)
        
        title = self.font.render("TOWER DEFENCE", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        # Start button
        pygame.draw.rect(self.screen, GREEN, (SCREEN_WIDTH // 2 - 100, 300, 200, 50))
        start_text = self.font.render("START GAME", True, BLACK)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 325))
        self.screen.blit(start_text, start_rect)
        
        # Instructions
        instructions = [
            "Build towers to defend against enemies",
            "Survive 10 waves to win",
            "Click to place towers, upgrade by selecting them",
            "Don't let enemies reach the end!"
        ]
        
        y_offset = 400
        for inst in instructions:
            inst_text = self.small_font.render(inst, True, WHITE)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(inst_text, inst_rect)
            y_offset += 30
    
    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(game_over_text, game_over_rect)
        
        wave_text = self.small_font.render(f"You survived {self.current_wave} waves", True, WHITE)
        wave_rect = wave_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(wave_text, wave_rect)
        
        # Restart button
        pygame.draw.rect(self.screen, GREEN, (SCREEN_WIDTH // 2 - 100, 350, 200, 50))
        restart_text = self.font.render("RESTART", True, BLACK)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 375))
        self.screen.blit(restart_text, restart_rect)
    
    def draw_victory(self):
        """Draw victory screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        victory_text = self.font.render("VICTORY!", True, GREEN)
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(victory_text, victory_rect)
        
        congrats_text = self.small_font.render("You successfully defended against all waves!", True, WHITE)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(congrats_text, congrats_rect)
        
        # Restart button
        pygame.draw.rect(self.screen, BLUE, (SCREEN_WIDTH // 2 - 100, 350, 200, 50))
        restart_text = self.font.render("PLAY AGAIN", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 375))
        self.screen.blit(restart_text, restart_rect)
    
    def draw(self):
        """Draw everything"""
        if self.state == GameState.MENU:
            self.draw_menu()
        else:
            self.screen.fill(WHITE)
            
            # Draw path
            self.draw_path()
            
            # Draw towers
            for tower in self.towers:
                show_range = tower == self.selected_tower
                tower.draw(self.screen, show_range)
            
            # Draw enemies
            for enemy in self.enemies:
                enemy.draw(self.screen)
            
            # Draw projectiles
            for projectile in self.projectiles:
                projectile.draw(self.screen)
            
            # Draw placement preview
            if self.placing_tower and self.hover_pos:
                x, y = self.hover_pos
                color = GREEN if self.can_place_tower(x, y) else RED
                pygame.draw.circle(self.screen, color, (x, y), 15, 2)
                pygame.draw.circle(self.screen, LIGHT_GRAY, (x, y), 120, 1)
            
            # Draw UI
            self.draw_ui()
            
            # Draw overlays
            if self.state == GameState.GAME_OVER:
                self.draw_game_over()
            elif self.state == GameState.VICTORY:
                self.draw_victory()
        
        pygame.display.flip()
    
    def handle_menu_click(self, pos: Tuple[int, int]):
        """Handle clicks on menu screen"""
        x, y = pos
        # Start button
        if SCREEN_WIDTH // 2 - 100 <= x <= SCREEN_WIDTH // 2 + 100 and 300 <= y <= 350:
            self.reset_game()
    
    def handle_game_click(self, pos: Tuple[int, int], button: int):
        """Handle clicks during gameplay"""
        x, y = pos
        
        # Right click - deselect
        if button == 3:
            self.selected_tower = None
            self.placing_tower = False
            return
        
        # Check UI buttons
        if y > SCREEN_HEIGHT - 100:
            # Next wave button
            if 250 <= x <= 400 and SCREEN_HEIGHT - 50 <= y <= SCREEN_HEIGHT - 15:
                if not self.wave_active:
                    self.start_next_wave()
            # Place tower button
            elif 450 <= x <= 600 and SCREEN_HEIGHT - 80 <= y <= SCREEN_HEIGHT - 45:
                if self.money >= TOWER_COST:
                    self.placing_tower = True
                    self.selected_tower = None
            # Upgrade button
            elif 450 <= x <= 600 and SCREEN_HEIGHT - 40 <= y <= SCREEN_HEIGHT - 5:
                if self.selected_tower and self.selected_tower.can_upgrade():
                    self.upgrade_tower(self.selected_tower)
        else:
            # Game area click
            if self.placing_tower:
                self.place_tower(x, y)
            else:
                # Select tower
                tower = self.get_tower_at_pos(x, y)
                self.selected_tower = tower
    
    def handle_end_screen_click(self, pos: Tuple[int, int]):
        """Handle clicks on game over/victory screen"""
        x, y = pos
        # Restart button
        if SCREEN_WIDTH // 2 - 100 <= x <= SCREEN_WIDTH // 2 + 100 and 350 <= y <= 400:
            self.reset_game()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == GameState.MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == GameState.PLAYING:
                        self.handle_game_click(event.pos, event.button)
                    elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                        self.handle_end_screen_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.hover_pos = event.pos
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


def main():
    """Main entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
