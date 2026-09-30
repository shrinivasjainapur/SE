import random
import pygame
from game.block import Block, Debris


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.game_over = False

        self.perfect_streak = 0
        self.perfect_message_timer = 0
        self.debris = []

        base_x = (self.width - self.base_width) // 2
        base_y = self.height - 60
        base_block = Block(base_x, base_y, self.base_width, self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - 4
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        start_x = 25 if random.choice([True, False]) else self.width - 25 - top_block.width
        self.active_block = Block(start_x, next_y, top_block.width, self.block_height, color, speed=speed)

    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left
        
        # BUG SYMPTOM: 
        # Overlap condition is inverted so hitting empty air succeeds while landing on the tower fails.
        is_successful_drop = overlap > 0
        
        if is_successful_drop:
            if abs(act.x - top_block.x) <= 3:
                new_block = Block(top_block.x, act.y, act.width, self.block_height, act.color, speed=0)
                self.stack.append(new_block)
                self.score += 3
                self.perfect_streak += 1
                self.perfect_message_timer = 60

                if self.perfect_streak >= 3:
                    new_block.width = min(self.base_width, new_block.width + 10)
                    self.perfect_streak = 0
            else:
                trimmed_width = max(10.0, overlap)
                new_block = Block(left, act.y, trimmed_width, self.block_height, act.color, speed=0)
                self.stack.append(new_block)
                self.score += 1
                self.perfect_streak = 0

                if act.x < top_block.x:
                    debris_x = act.x
                    debris_width = top_block.x - act.x
                    velocity_x = -2.5
                else:
                    debris_x = top_block.x + top_block.width
                    debris_width = (act.x + act.width) - (top_block.x + top_block.width)
                    velocity_x = 2.5

                if debris_width > 0:
                    self.debris.append(
                        Debris(
                            debris_x,
                            act.y,
                            debris_width,
                            self.block_height,
                            act.color,
                            velocity_x,
                            -2.5
                        )
                    )

            if new_block.y < 180:
                shift_amount = self.block_height + 4
                for b in self.stack:
                    b.y += shift_amount

            self.spawn_active_block()
        else:
            self.game_over = True

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_r) or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)

        for debris in self.debris:
            debris.update()

        self.debris = [
            debris for debris in self.debris
            if debris.y < self.height + 100
        ]

    def draw_background(self, screen):
        height = len(self.stack) - 1

        if height < 5:
            start_color = (35, 70, 120)
            end_color = (80, 110, 170)
        elif height < 10:
            start_color = (65, 45, 110)
            end_color = (110, 65, 140)
        elif height < 20:
            start_color = (20, 25, 65)
            end_color = (45, 35, 90)
        else:
            start_color = (5, 8, 20)
            end_color = (15, 18, 35)

        for y in range(self.height):
            ratio = y / self.height

            r = int(
                start_color[0] +
                (end_color[0] - start_color[0]) * ratio
            )

            g = int(
                start_color[1] +
                (end_color[1] - start_color[1]) * ratio
            )

            b = int(
                start_color[2] +
                (end_color[2] - start_color[2]) * ratio
            )

            pygame.draw.line(
                screen,
                (r, g, b),
                (0, y),
                (self.width, y)
            )

        if height >= 10:
            random.seed(10)

            for _ in range(min(50, height * 2)):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                pygame.draw.circle(screen, (220, 225, 245), (x, y), 1)

            random.seed()

    def render(self, screen):
        self.draw_background(screen)

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(f"Height: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 54))

        if self.perfect_message_timer > 0:
            perfect_surf = self.font_hud.render("PERFECT!", True, (255, 215, 50))
            screen.blit(perfect_surf, (self.width // 2 - perfect_surf.get_width() // 2, 90))
            self.perfect_message_timer -= 1

        for b in self.stack:
            b.render(screen)

        for debris in self.debris:
            debris.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_surf = self.font_hud.render(f"Final Height: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_hud.render("Press [Space] or [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))
            
