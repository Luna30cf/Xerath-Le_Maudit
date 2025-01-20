import pygame
import pytmx
import time
import json
import sys

class Map:
    def __init__(self, tmx_file, collidable_json):
        """
        Initialise la carte en chargeant le fichier TMX et les calques bloquants ainsi que les téléporteurs depuis un JSON.
        """
        self.tmx_data = pytmx.util_pygame.load_pygame(tmx_file)
        self.tile_width = self.tmx_data.tilewidth
        self.tile_height = self.tmx_data.tileheight
        self.map_width = self.tmx_data.width
        self.map_height = self.tmx_data.height
        self.collidable_tiles, self.teleporters_layer = self.load_layers(collidable_json)
        self.scaled_tiles_cache = {}
        self.teleporters = self.load_teleporters(collidable_json)
        print(f"[DEBUG] Nombre total de tuiles bloquantes = {len(self.collidable_tiles)}")
        print(f"[DEBUG] Nombre total de téléporteurs = {len(self.teleporters)}")

    def load_layers(self, json_layers_file):
        """
        Charge les calques bloquants et identifie le calque des téléporteurs.
        Retourne un tuple (collidable_tiles, teleporters_layer_name).
        """
        with open(json_layers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        collidable_layer_names = set(data.get("layers", []))
        teleporters_layer_name = data.get("teleporters_layer", "teleporters")

        collidable_tiles = set()

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if layer.name in collidable_layer_names:
                    count_added = 0
                    for x, y, gid in layer:
                        if gid != 0:
                            collidable_tiles.add((x, y - 1))  # Ajustez selon vos besoins
                            count_added += 1
                    print(f"[DEBUG] Layer '{layer.name}' => {count_added} tuiles ajoutées comme bloquantes.")
                else:
                    print(f"[DEBUG] Layer '{layer.name}' ignoré pour collisions.")

        return collidable_tiles, teleporters_layer_name

    def load_teleporters(self, json_layers_file):
        """
        Charge les téléporteurs depuis un fichier JSON.
        Retourne une liste de téléporteurs avec leurs zones et destinations.
        """
        with open(json_layers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        teleporters_data = data.get("teleporters", [])

        teleporters = []
        for teleporter in teleporters_data:
            zone = teleporter.get("zone", {})
            target_map = teleporter.get("target_map")
            target_spawn = teleporter.get("target_spawn", {})
            if zone and target_map and target_spawn:
                teleporter_rect = pygame.Rect(
                    zone.get("x", 0),
                    zone.get("y", 0),
                    zone.get("width", 1),
                    zone.get("height", 1)
                )
                teleporters.append({
                    "zone": teleporter_rect,
                    "target_map": target_map,
                    "target_spawn": (target_spawn.get("x", 0), target_spawn.get("y", 0))
                })
                print(f"[DEBUG] Téléporteur ajouté: Zone={zone}, Target Map={target_map}, Target Spawn={target_spawn}")
            else:
                print(f"[WARNING] Téléporteur mal configuré dans le JSON: {teleporter}")

        return teleporters

    def get_scaled_tile_image(self, gid, zoom):
        """
        Récupère et redimensionne l'image d'une tuile en utilisant le cache.
        """
        if (gid, zoom) in self.scaled_tiles_cache:
            return self.scaled_tiles_cache[(gid, zoom)]

        original_image = self.tmx_data.get_tile_image_by_gid(gid)
        if original_image is None:
            return None

        scaled_image = pygame.transform.scale(
            original_image,
            (int(self.tile_width * zoom), int(self.tile_height * zoom))
        )
        self.scaled_tiles_cache[(gid, zoom)] = scaled_image
        return scaled_image

    def render(self, screen, camera_x, camera_y, zoom, debug=False, show_teleporters=False):
        """
        Rend toutes les tuiles visibles à l'écran en fonction de la position de la caméra et du zoom.
        Si debug=True, dessine des rectangles rouges sur les tuiles bloquantes.
        Si show_teleporters=True, dessine des rectangles bleus sur les zones de téléportation.
        """
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid != 0:
                        tile_img = self.get_scaled_tile_image(gid, zoom)
                        if tile_img:
                            draw_x = x * self.tile_width * zoom - camera_x
                            draw_y = y * self.tile_height * zoom - camera_y
                            screen.blit(tile_img, (draw_x, draw_y))
        if debug:
            for (x, y) in self.collidable_tiles:
                rect = pygame.Rect(
                    x * self.tile_width * zoom - camera_x,
                    y * self.tile_height * zoom - camera_y,
                    self.tile_width * zoom,
                    self.tile_height * zoom
                )
                pygame.draw.rect(screen, (255, 0, 0), rect, 2)  # Dessine un contour rouge

        if show_teleporters:
            for teleporter in self.teleporters:
                zone = teleporter["zone"]
                rect = pygame.Rect(
                    zone.x * self.tile_width * zoom - camera_x,
                    zone.y * self.tile_height * zoom - camera_y,
                    zone.width * self.tile_width * zoom,
                    zone.height * self.tile_height * zoom
                )
                pygame.draw.rect(screen, (0, 0, 255), rect, 2)  # Dessine un contour bleu

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
        self.map = Map(self.current_map_file, "Python-Karl/collidable_layers.json")

        # Déterminer un spawn valide
        spawn_x, spawn_y = self.find_valid_spawn(22, 57)
        print(f"[DEBUG] Spawn validé : ({spawn_x},{spawn_y})")

        # Charger les animations du joueur
        self.animations = self.load_animations()

        # Initialiser le joueur
        self.player = Player(
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
                path = f"Python-Karl/sprites/{direction}/{direction}_{i}.png"
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
        Vérifie si le joueur est dans une zone de téléportation et effectue le téléport si nécessaire.
        """
        player_tile_x = int(round(self.player.position_x))
        player_tile_y = int(round(self.player.position_y))

        for teleporter in self.map.teleporters:
            zone = teleporter["zone"]
            # Vérifie si la position du joueur est à l'intérieur de la zone de téléportation
            if zone.collidepoint(player_tile_x, player_tile_y):
                print(f"[DEBUG] Téléportation déclenchée vers {teleporter['target_map']} à {teleporter['target_spawn']}")
                self.load_map(teleporter["target_map"], teleporter["target_spawn"])
                break  # Téléportation unique par mise à jour

    def load_map(self, map_file, spawn_coords):
        """
        Charge une nouvelle carte et positionne le joueur aux coordonnées de spawn spécifiées.
        """
        self.current_map_file = map_file
        self.map = Map(self.current_map_file, "Python-Karl/collidable_layers.json")
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
            self.zoom,
            debug=False,  # Changez en True pour afficher les tuiles bloquantes
            show_teleporters=self.show_teleporters
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

if __name__ == "__main__":
    game = Game()
    game.run()
