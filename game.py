import pygame
import sys
import map as m
import player as p
import teleport as t
import json

class Game:
    def __init__(self, screen_width=1280, screen_height=720):
        """
        Initialise le jeu, y compris Pygame, la carte, le joueur, et les joysticks.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Les échos de Xerath")
        self.clock = pygame.time.Clock()

        # Charger la carte initiale
        self.current_map_file = "Assets/assets tiled/mapv2.tmx"
        self.map = m.Map(self.current_map_file, "collidable_layers.json")

        # Charger les zones de téléportation
        self.teleporter = t.Teleporter("teleport-zones.json")


        # Déterminer un spawn valide
        spawn_x, spawn_y = self.find_valid_spawn(22, 58)
        print(f"[DEBUG] Spawn validé : ({spawn_x},{spawn_y})")

        # Charger les animations du joueur
        self.animations = self.load_animations()

        # Initialiser le joueur
        self.player = p.Player(
            animations=self.animations,
            spawn_x=spawn_x,
            spawn_y=spawn_y,
            tile_width=self.map.tile_width,
            tile_height=self.map.tile_height,
            zoom=4.0,
            sprite_scale=2
        )

        # Paramètres de zoom
        self.zoom = 4.0
        self.sprite_scale = 2

        # Mode collision
        self.collision_enabled = True

        # Initialiser les joysticks
        self.joysticks = self.init_joysticks()

        # Pour répéter les KEYDOWN si on maintient la flèche
        pygame.key.set_repeat(200, 80)

        # Affichage des téléporteurs (débogage)
        self.show_teleporters = False  # Par défaut, les téléporteurs ne sont pas affichés

    def load_animations(self):
        """
        Charge les sprites d’animation pour chaque direction du joueur.
        """
        directions = ["down", "up", "left", "right"]
        animations = {}
        for direction in directions:
            frames = []
            for i in range(4):  # Supposons 4 frames par direction
                path = f"Assets/sprites/{direction}/{direction}_{i}.png"
                try:
                    image = pygame.image.load(path).convert_alpha()
                    frames.append(image)
                except pygame.error as e:
                    print(f"[ERROR] Impossible de charger {path}: {e}")
            animations[direction] = frames
        return animations

    def init_joysticks(self):
        """
        Initialise les joysticks/gamepads disponibles.
        """
        pygame.joystick.init()
        joysticks = []
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            joysticks.append(joystick)
            print(f"[DEBUG] Joystick détecté : {joystick.get_name()}")
        return joysticks

    def find_valid_spawn(self, preferred_x, preferred_y):
        """
        Recherche une tuile de spawn valide, en évitant les tuiles bloquantes.
        """
        collidable = self.map.collidable_tiles
        map_w = self.map.map_width
        map_h = self.map.map_height

        if (0 <= preferred_x < map_w and
                0 <= preferred_y < map_h and
                (preferred_x, preferred_y) not in collidable):
            return float(preferred_x), float(preferred_y)
        else:
            print(f"[DEBUG] (preferred_x, preferred_y)=({preferred_x},{preferred_y}) est bloquant ou hors map.")
            for ty in range(map_h):
                for tx in range(map_w):
                    if (tx, ty) not in collidable:
                        print(f"[DEBUG] Trouvé spawn libre => ({tx},{ty})")
                        return float(tx), float(ty)
            print("[DEBUG] Aucune tuile libre trouvée dans la map ! Spawn en (0,0)")
            return 0.0, 0.0

    def handle_keyboard_input(self):
        """
        Gère l'entrée clavier pour le déplacement et le zoom.
        """
        keys = pygame.key.get_pressed()
        direction_x = 0
        direction_y = 0

        if keys[pygame.K_LEFT]:
            direction_x = -1
            self.player.direction = "left"
        elif keys[pygame.K_RIGHT]:
            direction_x = 1
            self.player.direction = "right"
        elif keys[pygame.K_UP]:
            direction_y = -1
            self.player.direction = "up"
        elif keys[pygame.K_DOWN]:
            direction_y = 1
            self.player.direction = "down"

        return direction_x, direction_y

    def handle_joystick_input(self):
        """
        Gère l'entrée de la manette pour le déplacement.
        """
        direction_x = 0
        direction_y = 0
        if len(self.joysticks) > 0:
            joystick = self.joysticks[0]  # Utiliser le premier joystick
            axis_x = joystick.get_axis(0)  # Axe horizontal
            axis_y = joystick.get_axis(1)  # Axe vertical

            deadzone = 0.5  # Seuil pour éviter le drift

            if axis_x < -deadzone:
                direction_x = -1
                self.player.direction = "left"
            elif axis_x > deadzone:
                direction_x = 1
                self.player.direction = "right"

            if axis_y < -deadzone:
                direction_y = -1
                self.player.direction = "up"
            elif axis_y > deadzone:
                direction_y = 1
                self.player.direction = "down"

        return direction_x, direction_y
    
    def handle_events(self):
        """
        Gère tous les événements Pygame, y compris les entrées clavier et manette.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.zoom += 0.1
                    if self.zoom > 5.0:
                        self.zoom = 5.0
                    self.map.scaled_tiles_cache.clear()
                    print(f"[DEBUG] Zoom augmenté à {self.zoom}")
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.zoom -= 0.1
                    if self.zoom < 0.1:
                        self.zoom = 0.1
                    self.map.scaled_tiles_cache.clear()
                    print(f"[DEBUG] Zoom diminué à {self.zoom}")
                elif event.key == pygame.K_c:
                    self.collision_enabled = not self.collision_enabled
                    print(f"[DEBUG] Collisions {'activées' if self.collision_enabled else 'désactivées'}")
                elif event.key == pygame.K_t:
                    self.show_teleporters = not self.show_teleporters
                    print(f"[DEBUG] Affichage des téléporteurs {'activé' if self.show_teleporters else 'désactivé'}")

            elif event.type == pygame.JOYBUTTONDOWN:
                # Exemple : Toggle collision avec le bouton 0 (A sur manette Xbox)
                if event.button == 0:
                    self.collision_enabled = not self.collision_enabled
                    print(f"[DEBUG] Collisions {'activées' if self.collision_enabled else 'désactivées'} via manette")


    def check_teleporters(self):
        """
        Vérifie si le joueur doit être téléporté.
        """
        new_map, new_position = self.teleporter.check_teleportation(self.player)
        if new_map:
            self.map = new_map
            self.player.position_x, self.player.position_y = new_position
            print(f"[INFO] Joueur téléporté à la carte {self.map} avec position {new_position}")
            

    def load_map(self, map_file, spawn_coords):
        """
        Charge une nouvelle carte et positionne le joueur aux coordonnées de spawn spécifiées.
        """
        self.current_map_file = map_file
        self.map = m.Map(self.current_map_file, "collidable_layers.json")
        self.player.tile_width = self.map.tile_width
        self.player.tile_height = self.map.tile_height
        self.player.position_x, self.player.position_y = spawn_coords
        self.player.move_start_x = self.player.position_x
        self.player.move_start_y = self.player.position_y
        self.player.move_target_x = self.player.position_x
        self.player.move_target_y = self.player.position_y
        self.player.is_moving = False
        print(f"[DEBUG] Carte chargée : {map_file}, Spawn position : {spawn_coords}")

    def update(self, direction_x, direction_y):
        """
        Met à jour l'état du jeu, y compris le déplacement du joueur.
        """
        if not self.player.is_moving:
            if direction_x != 0 or direction_y != 0:
                current_x = int(round(self.player.position_x))
                current_y = int(round(self.player.position_y))
                target_x = current_x + direction_x
                target_y = current_y + direction_y

                # Vérifier les limites de la map
                if 0 <= target_x < self.map.map_width and 0 <= target_y < self.map.map_height:
                    if self.collision_enabled and (target_x, target_y) in self.map.collidable_tiles:
                        print(f"[DEBUG] Tuile bloquante: ({target_x},{target_y}). Mouvement annulé.")
                    else:
                        print(f"[DEBUG] Déplacement validé: ({current_x},{current_y}) -> ({target_x},{target_y})")
                        self.player.start_move(self.player.direction)
                else:
                    print(f"[DEBUG] Hors map: ({target_x},{target_y})")

        self.player.update_position()
        self.check_teleporters()


    def render(self):
        """
        Rend tous les éléments du jeu à l'écran.
        """
        self.screen.fill((0, 0, 0))

        # Calculer la position de la caméra
        player_px = self.player.position_x * self.map.tile_width * self.zoom
        player_py = self.player.position_y * self.map.tile_height * self.zoom
        camera_x = player_px - self.screen.get_width() / 2
        camera_y = player_py - self.screen.get_height() / 2

        # Rendre la carte avec les options de débogage
        self.map.render(
            self.screen,
            camera_x,
            camera_y,
            self.zoom
        )

        # Rendre le joueur
        self.player.render(self.screen, camera_x, camera_y)

        pygame.display.flip()

    def run(self):
        """
        Lance la boucle principale du jeu.
        """
        while True:
            self.clock.tick(60)  # Limiter à 60 FPS
            self.handle_events()

            # Gérer les entrées clavier et manette
            direction_x_kb, direction_y_kb = self.handle_keyboard_input()
            direction_x_js, direction_y_js = self.handle_joystick_input()

            # Prioriser les entrées clavier sur la manette
            direction_x = direction_x_kb if direction_x_kb != 0 else direction_x_js
            direction_y = direction_y_kb if direction_y_kb != 0 else direction_y_js

            self.update(direction_x, direction_y)
            self.render()
