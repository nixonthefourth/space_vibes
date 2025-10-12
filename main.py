import pygame
import numpy as np
import math

pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 800, 600
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
SPEED = 1
CAM_DISTANCE = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


# --- Math ---
def rotation_matrix_x(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s, c]
    ])


def rotation_matrix_y(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ])


def project(points):
    """3D → 2D perspective projection"""
    z = points[:, 2] + CAM_DISTANCE
    z = np.where(z <= 0.01, 0.01, z)
    factor = 5 / z
    x_proj = points[:, 0] * factor * WIDTH / 2 + WIDTH / 2
    y_proj = -points[:, 1] * factor * HEIGHT / 2 + HEIGHT / 2
    return np.column_stack((x_proj, y_proj)).astype(int)


# --- Ship ---
class Ship:
    def __init__(self):
        self.vertices = np.array([
            [0, -0.2, 2.0],
            [-1.5, -0.2, -2.0],
            [1.5, -0.2, -2.0],
            [0, 0.2, 2.0],
            [-1.0, 0.2, -2.0],
            [1.0, 0.2, -2.0],
        ])
        self.edges = [
            (0,1), (0,2), (1,2),
            (3,4), (3,5), (4,5),
            (0,3), (1,4), (2,5),
            (1,5), (2,4)
        ]

    def draw(self, surface, angle_x, yaw, bank):
        # Rotation matrices
        rot_x = rotation_matrix_x(angle_x)
        rot_y = rotation_matrix_y(yaw)
        rotation = rot_y @ rot_x

        # Apply rotation
        rotated = self.vertices @ rotation.T
        # Apply bank offset visually
        rotated[:, 0] += bank

        verts_2d = project(rotated)
        for a, b in self.edges:
            pygame.draw.line(surface, WHITE, verts_2d[a], verts_2d[b], 1)


# --- Scene ---
class Scene:
    def __init__(self):
        self.ship = Ship()
        self.angle_x = -0.2      # fixed downward look
        self.yaw = 0.0           # momentary yaw for cinematic turn
        self.pos = np.array([0.0, 0.0, 0.0])
        # Spread over a big 3D space
        self.stars = np.random.rand(1000, 3) * [1000, 600, 1000] - [500, 300, 0]

        # Turning animation
        self.turn_target = 0.0
        self.turn_value = 0.0
        self.turn_speed = 5.0
        self.turn_angle = 0.25   # visual yaw when turning
        self.bank_amount = 0.8   # lateral visual offset

    def handle_input(self, event):
        """Trigger on key press/release"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                self.turn_target = -1
            elif event.key == pygame.K_a:
                self.turn_target = 1
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_a, pygame.K_d):
                self.turn_target = 0

    def update(self, dt, keys):
        # Smooth turn animation
        alpha = 1 - math.exp(-self.turn_speed * dt)
        self.turn_value += (self.turn_target - self.turn_value) * alpha

        # Forward/backward movement in world space (ignoring visual turn)
        forward = np.array([0.0, 0.0, 1.0])  # always along Z
        if keys[pygame.K_w]:
            self.pos += forward * SPEED
        if keys[pygame.K_s]:
            self.pos -= forward * SPEED

    def draw(self, surface):
        for i in range(len(self.stars)):
            if self.stars[i, 2] - self.pos[2] < -10:  # behind ship
                self.stars[i, 2] += 1000  # move star forward

        total_yaw = self.turn_value * self.turn_angle
        bank = self.turn_value * self.bank_amount

        # Stars relative to ship
        rot_y = rotation_matrix_y(total_yaw)
        rot_x = rotation_matrix_x(self.angle_x)
        rotation = rot_x @ rot_y

        relative_stars = self.stars - self.pos
        rotated_stars = relative_stars @ rotation.T
        star_points = project(rotated_stars)

        for s in star_points:
            x, y = s
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                surface.set_at((x, y), WHITE)

        # Draw ship
        self.ship.draw(surface, self.angle_x, total_yaw, bank)


# --- Main Loop ---
scene = Scene()
running = True
last_time = pygame.time.get_ticks() / 1000.0

while running:
    now = pygame.time.get_ticks() / 1000.0
    dt = now - last_time
    last_time = now

    screen.fill(BLACK)

    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        scene.handle_input(event)

    scene.update(dt, keys)
    scene.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
