import pygame
import time

class Player:
    def __init__(self, animations, spawn_x, spawn_y, tile_width, tile_height, zoom, sprite_scale):
        """
        Initialise le joueur avec les animations, la position de spawn, et les paramètres de zoom et d'échelle.
        """
        self.animations = animations
        self.direction = "down"
        self.position_x = spawn_x
        self.position_y = spawn_y
        self.zoom = zoom
        self.sprite_scale = sprite_scale
        self.tile_width = tile_width
        self.tile_height = tile_height

        # Initialiser les attributs de mouvement avant d'appeler get_current_frame
        self.is_moving = False
        self.move_start_x = 0.0
        self.move_start_y = 0.0
        self.move_target_x = 0.0
        self.move_target_y = 0.0
        self.move_start_time = 0
        self.move_duration = 0.1
        self.anim_speed = 0.3

        self.scaled_player_image = self.get_current_frame()

    def get_current_frame(self):
        """
        Obtient le cadre actuel de l'animation en fonction de la direction et du temps.
        """
        frames = self.animations[self.direction]
        nb_frames = len(frames)
        current_frame = frames[0]  # Par défaut, le premier cadre

        if self.is_moving:
            elapsed = time.time() - self.move_start_time
            ratio = elapsed / self.move_duration
            anim_progress = ratio * self.anim_speed
            frame_index = int(anim_progress * nb_frames)
            if frame_index >= nb_frames:
                frame_index = nb_frames - 1
            current_frame = frames[frame_index]

        # Redimensionner l'image du joueur
        scaled_width = int(self.tile_width * self.zoom * self.sprite_scale)
        scaled_height = int(self.tile_height * self.zoom * self.sprite_scale)
        return pygame.transform.scale(current_frame, (scaled_width, scaled_height))

    def start_move(self, direction):
        """
        Démarre un déplacement dans une direction donnée.
        """
        if not self.is_moving:
            self.direction = direction
            self.is_moving = True
            self.move_start_time = time.time()
            self.move_start_x = self.position_x
            self.move_start_y = self.position_y
            if direction == "left":
                self.move_target_x = self.position_x - 1
                self.move_target_y = self.position_y
            elif direction == "right":
                self.move_target_x = self.position_x + 1
                self.move_target_y = self.position_y
            elif direction == "up":
                self.move_target_x = self.position_x
                self.move_target_y = self.position_y - 1
            elif direction == "down":
                self.move_target_x = self.position_x
                self.move_target_y = self.position_y + 1

    def update_position(self):
        """
        Met à jour la position du joueur en fonction du temps pour l'interpolation.
        """
        if self.is_moving:
            elapsed = time.time() - self.move_start_time
            if elapsed >= self.move_duration:
                self.position_x = self.move_target_x
                self.position_y = self.move_target_y
                self.is_moving = False
            else:
                ratio = elapsed / self.move_duration
                self.position_x = self.move_start_x + ratio * (self.move_target_x - self.move_start_x)
                self.position_y = self.move_start_y + ratio * (self.move_target_y - self.move_start_y)

    def render(self, screen, camera_x, camera_y):
        """
        Rends le joueur à l'écran.
        """
        self.scaled_player_image = self.get_current_frame()
        player_px = self.position_x * self.tile_width * self.zoom
        player_py = self.position_y * self.tile_height * self.zoom

        draw_x = player_px - camera_x
        draw_y = player_py - camera_y

        # Centrer le sprite si agrandi
        draw_x -= (self.scaled_player_image.get_width() - self.tile_width * self.zoom) / 2
        # draw_y -= (self.scaled_player_image.get_height() - self.tile_height * self.zoom) / 2  # Décommentez si besoin

        screen.blit(self.scaled_player_image, (draw_x, draw_y))