import pygame
import sys
import os
from pygame.locals import *

pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 500
screen_height = 500

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

# define game variables
tile_size = 100


# load images
# sun_img = pygame.image.load('data/arrow.png')
# bg_img = pygame.image.load('data/fon.jpg')
# image = load_image("owls.png")
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# def draw_grid():
#     for line in range(0, 6):
#         pygame.draw.line(screen, (255, 255, 255), (0, line * tile_size), (screen_width, line * tile_size))
#         pygame.draw.line(screen, (255, 255, 255), (line * tile_size, 0), (line * tile_size, screen_height))


class Player:
    def __init__(self, x, y):
        # img = pygame.image.load('data/mar.png')
        # image = load_image("owls.png")
        self.image = pygame.transform.scale(img, (40, 80))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.jumped = False

    def update(self):
        dx = 0
        dy = 0

        # get Keypresses
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            dx -= 5
        if key[pygame.K_RIGHT]:
            dx += 5
        if key[pygame.K_SPACE] and self.jumped == False:
            self.vel_y = -15
            self.jumped = True
        if key[pygame.K_SPACE] == False:
            self.jumped = False
        
        # add gravity
        self.vel_y += 1
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        # check for collision

        # update player coordinates
        self.rect.x += dx
        self.rect.y += dy

        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height
            dy = 0

        # draw player onto screen
        screen.blit(self.image, self.rect)


class World:
    def __init__(self, data):
        self.tile_list = []
        # load image
        # dirt_img = pygame.image.load('data/box.png')
        # grass_img = pygame.image.load('data/grass.png')
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])


world_data = [
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1],
    [1, 2, 2, 2, 1],
    [1, 1, 1, 1, 1]
]

# player = Player(1000, screen_height * 130)
player = Player(200, 200)
world = World(world_data)

run = True
while run:
    clock.tick(fps)
    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (200, 200))
    world.draw()
    player.update()
    # draw_grid()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    pygame.display.update()

pygame.quit()
