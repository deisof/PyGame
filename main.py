import pygame
from pygame import mixer
import sys
import os
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

# устанавливаем значение FPS
clock = pygame.time.Clock()
FPS = 60

# задаём размеры окна
WIDTH = 675
HEIGHT = 675

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Galaxy Platformer')

# определяем стиль текста
font1 = pygame.font.SysFont('arial', 70)
font2 = pygame.font.SysFont('arial', 50)

# определяем переменные, которые будем использовать в игре
tile_size = 45
game_over = 0
main_menu = True
level = 1
max_levels = 4
score = 0
best_score = score

# определяем цвета
WHITE = (255, 255, 255)
PURPLE = (195, 5, 248)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
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


# загружаем изображения
restart_img = load_image('restart_btn.png')
start_img = load_image('start.png')
exit_img = load_image('exit_btn.png')
bg_img = load_image('6bg.jpg')
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
start_img = pygame.transform.scale(start_img, (300, 300))
exit_img = pygame.transform.scale(exit_img, (300, 300))
restart_img = pygame.transform.scale(restart_img, (300, 300))

# загружаем музыку
pygame.mixer.music.load('data/game.mp3')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('data/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('data/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('data/game_over.wav')
game_over_fx.set_volume(0.5)


# функция для отрисовки текста
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# функция для того, чтобы сбросить уровень
def reset_level(level):
    player.reset(100, HEIGHT - 130)
    blob_group.empty()
    platform_group.empty()
    crystal_group.empty()
    spikes_group.empty()
    exit_group.empty()

    # загрузка уровня
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)
    # create dummy coin for showing the score
    score_coin = Crystal(tile_size // 2, tile_size // 2)
    crystal_group.add(score_coin)
    return world


class Button:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        # позиция мыши
        pos = pygame.mouse.get_pos()
        # проверка события
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        # отрисовка кнопки
        screen.blit(self.image, self.rect)
        return action


class Player:
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20

        if game_over == 0:
            # нажатие кнопки
            key = pygame.key.get_pressed()
            # прыжок
            if key[pygame.K_SPACE] and self.jumped == False and \
                    self.in_air == False or key[pygame.K_w] and \
                    self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False and key[pygame.K_w] == False:
                self.jumped = False
            # перемещение влево
            if key[pygame.K_LEFT] or key[pygame.K_a]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            # перемещение вправо
            if key[pygame.K_RIGHT] or key[pygame.K_d]:
                dx += 5
                self.counter += 1
                self.direction = 1
            # направление
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False \
                    and key[pygame.K_d] == False and key[pygame.K_a] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # анимация
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # гравитация
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # проверка на столкновение
            self.in_air = True
            for tile in world.tile_list:
                # проверка на столкновение по x
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # проверка на столкновение по y
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # проверка на столкновение с врагами
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                game_over_fx.play()

            # проверка на столкновение с шипами
            if pygame.sprite.spritecollide(self, spikes_group, False):
                game_over = -1
                game_over_fx.play()

            # проверка на столкновение с порталом (выход)
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            # проверка на столкновение с платформами
            for platform in platform_group:
                # по x
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # по y
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # ниже платфомы
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # выше платформы
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # перемещение вместе с платформой
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction
            # обновление координат игрока
            self.rect.x += dx
            self.rect.y += dy
        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font1, PURPLE, (WIDTH // 4 - 25), HEIGHT // 2 - 75)
            if self.rect.y > 200:
                self.rect.y -= 5

        # отрисовка игрока на экран
        screen.blit(self.image, self.rect)
        return game_over

    # функция сброса
    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = load_image(f'guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = load_image('ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True


class World:
    def __init__(self, data):
        self.tile_list = []

        # загрузка изображений
        stone_center = load_image('stoneCenter.png')
        stone_mid = load_image('stoneMid.png')
        # расшифровка заданного уровня
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(stone_center, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(stone_mid, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Spikes1(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    spikes_group.add(lava)
                if tile == 7:
                    coin = Crystal(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    crystal_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                if tile == 9:
                    enemystop = EnemyStop(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    blob_group.add(enemystop)
                if tile == 10:
                    enemyfast = EnemyFast(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(enemyfast)
                if tile == 11:
                    spikectop = Spikes(col_count * tile_size, row_count * tile_size + (tile_size // 35))
                    spikes_group.add(spikectop)
                col_count += 1
            row_count += 1

    # отрисовка
    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image('snailWalk1.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 60:
            self.move_direction *= -1
            self.move_counter *= -1


class EnemyFast(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image('slimeWalk1.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 3
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 60:
            self.move_direction *= -1
            self.move_counter *= -1


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = load_image('stoneHalf.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Spikes1(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = load_image('spikes.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Spikes(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = load_image('spikestop.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class EnemyStop(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = load_image('pokerMad.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size * 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Crystal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = load_image('coin.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = load_image('exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 2)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


player = Player(100, HEIGHT - 130)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
spikes_group = pygame.sprite.Group()
crystal_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# создание кристаллов
score_crystal = Crystal(tile_size // 2, tile_size // 2)
crystal_group.add(score_crystal)

# загрузка карт уровня
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

# создание кнопок
restart_button = Button(WIDTH // 4, HEIGHT // 2, restart_img)
start_button = Button(WIDTH // 2 - 337, HEIGHT // 2, start_img)
exit_button = Button(WIDTH // 2, HEIGHT // 2, exit_img)

run = True
while run:
    clock.tick(FPS)

    screen.blit(bg_img, (0, 0))

    if main_menu == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:
        world.draw()
        if game_over == 0:
            blob_group.update()
            platform_group.update()
            # обновление score
            # проверка был ли собран кристалл
            if pygame.sprite.spritecollide(player, crystal_group, True):
                score += 1
                coin_fx.play()
            draw_text('X ' + str(score), font2, WHITE, tile_size - 10, 10)

        blob_group.draw(screen)
        platform_group.draw(screen)
        spikes_group.draw(screen)
        crystal_group.draw(screen)
        exit_group.draw(screen)

        game_over = player.update(game_over)

        # в случае поражения
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0
        # если игрок прошёл уровень
        if game_over == 1:
            # заканчиваем уровень и переходим на следующий
            level += 1
            if level <= max_levels:
                # reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', font1, PURPLE, (WIDTH // 2) - 140, HEIGHT // 2)
                if restart_button.draw():
                    level = 1
                    # reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()
pygame.quit()
