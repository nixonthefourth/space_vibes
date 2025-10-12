import pygame
import numpy as np

pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 800, 600
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
SPEED = 30.0        # units per second
CAM_DISTANCE = 20
MAX_YAW_VISUAL = 0.25      # max visual yaw per press
BANK_AMOUNT = 0.8           # visual bank amount
TURN_SPEED = 3.0            # speed of visual tilt
HEADING_SPEED = 1.5         # speed of actual heading rotation
MAX_ROTATION_LEFT = -0.5    # radians, absolute left limit
MAX_ROTATION_RIGHT = 0.5    # radians, absolute right limit

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


# --- Math ---
def rotation_matrix_x(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[1, 0, 0],[0, c, -s],[0, s, c]])


def rotation_matrix_y(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


def project(points):
    z = points[:,2] + CAM_DISTANCE
    z = np.where(z <= 0.01, 0.01, z)
    factor = 5 / z
    x_proj = points[:,0] * factor * WIDTH/2 + WIDTH/2
    y_proj = -points[:,1] * factor * HEIGHT/2 + HEIGHT/2
    return np.column_stack((x_proj,y_proj)).astype(int)


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
            (0,1),(0,2),(1,2),
            (3,4),(3,5),(4,5),
            (0,3),(1,4),(2,5),
            (1,5),(2,4)
        ]

    def draw(self, surface, angle_x, yaw, bank):
        rot_x = rotation_matrix_x(angle_x)
        rot_y = rotation_matrix_y(yaw)
        rotation = rot_y @ rot_x
        rotated = self.vertices @ rotation.T
        rotated[:,0] += bank
        verts_2d = project(rotated)
        for a,b in self.edges:
            pygame.draw.line(surface, WHITE, verts_2d[a], verts_2d[b],1)


# --- Scene ---
class Scene:
    def __init__(self):
        self.ship = Ship()
        self.angle_x = -0.2
        self.rotation_yaw = 0.0   # actual heading
        self.forward = np.array([0,0,1.0])
        self.pos = np.array([0.0,0.0,0.0])
        self.stars = np.random.rand(2000,3)*[1000,600,1000]-[500,300,0]

        self.turn_value = 0.0     # current visual tilt
        self.turn_target = 0.0    # target visual tilt
        self.bank_amount = BANK_AMOUNT

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.turn_target = -MAX_YAW_VISUAL
            elif event.key == pygame.K_d:
                self.turn_target = MAX_YAW_VISUAL
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_a, pygame.K_d):
                self.turn_target = 0.0

    def update(self, dt, keys):
        # Smoothly update visual tilt
        diff = self.turn_target - self.turn_value
        self.turn_value += diff * min(1.0, TURN_SPEED*dt)
        # Clamp visual tilt
        self.turn_value = max(min(self.turn_value, MAX_ROTATION_RIGHT), MAX_ROTATION_LEFT)

        # Update actual heading gradually based on tilt
        if abs(self.turn_value) > 0.001:
            heading_change = (self.turn_value/MAX_YAW_VISUAL)*HEADING_SPEED*dt
            self.rotation_yaw += heading_change
            # Clamp actual heading
            self.rotation_yaw = max(min(self.rotation_yaw, MAX_ROTATION_RIGHT), MAX_ROTATION_LEFT)

        # Forward/backward movement along current heading
        move_input = 0.0
        if keys[pygame.K_w]:
            move_input += 1.0
        if keys[pygame.K_s]:
            move_input -= 1.0
        self.pos += self.forward * SPEED * dt * move_input

        # Update forward vector
        c,s = np.cos(self.rotation_yaw), np.sin(self.rotation_yaw)
        self.forward = np.array([s,0,c])

    def draw(self,surface):
        total_yaw = self.rotation_yaw + self.turn_value
        bank = self.turn_value*self.bank_amount

        # Stars
        rot_y = rotation_matrix_y(total_yaw)
        rot_x = rotation_matrix_x(self.angle_x)
        rotation = rot_x @ rot_y
        relative_stars = self.stars - self.pos
        rotated_stars = relative_stars @ rotation.T
        star_points = project(rotated_stars)
        for x,y in star_points:
            if 0<=x<WIDTH and 0<=y<HEIGHT:
                surface.set_at((x,y),WHITE)

        # Wrap stars
        for i in range(len(self.stars)):
            if self.stars[i,2]-self.pos[2]<-10:
                self.stars[i,2]+=1000

        # Draw ship
        self.ship.draw(surface, self.angle_x, total_yaw, bank)


# --- Main Loop ---
scene = Scene()
running = True
last_time = pygame.time.get_ticks()/1000.0

while running:
    now = pygame.time.get_ticks()/1000.0
    dt = now - last_time
    last_time = now

    screen.fill(BLACK)

    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        scene.handle_input(event)

    scene.update(dt,keys)
    scene.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
