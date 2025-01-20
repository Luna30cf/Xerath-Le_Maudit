import pygame
import pytmx
import json
import teleport as t

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

    def load_layers(self, json_layers_file):
        with open(json_layers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        collidable_layer_names = set(data.get("layers", []))
        teleporters_layer_name = data.get("teleporters_layer", "teleporters")

        collidable_tiles = set()
        total_count = 0  # Initialisation du comptage total des tuiles bloquantes

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if layer.name in collidable_layer_names:
                    count_added = 0
                    for x, y, gid in layer:
                        if gid != 0:
                            collidable_tiles.add((x, y-1))  # Ajout sans -1
                            count_added += 1
                            total_count += 1
                    print(f"[DEBUG] Layer '{layer.name}' => {count_added} tuiles ajoutées comme bloquantes.")
                else:
                    print(f"[DEBUG] Layer '{layer.name}' ignoré pour collisions.")

        print(f"[DEBUG] Nombre total de tuiles bloquantes = {total_count}")
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