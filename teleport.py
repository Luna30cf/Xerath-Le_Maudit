import json
import map as m

class Teleporter:
    def __init__(self, json_file):
        """
        Initialise les téléporteurs en chargeant les données à partir d'un fichier JSON.
        """
        self.teleport_zones = self.load_teleport_zones(json_file)

    def load_teleport_zones(self, json_file):
        """
        Charge les zones de téléportation à partir d'un fichier JSON.
        """
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        teleport_zones = []
        for zone in data["zones"]:
            coordinates = [tuple(coord) for coord in zone["coordinates"]]
            teleport_zones.append({
                "coordinates": coordinates,
                "target_map": zone["target_map"],
                "spawn_position": tuple(zone["spawn_position"])
            })

        return teleport_zones

    def check_teleportation(self, player):
        """
        Vérifie si le joueur est dans une zone de téléportation et retourne la nouvelle carte et position.
        """
        player_coords = (int(player.position_x), int(player.position_y))

        for zone in self.teleport_zones:
            if player_coords in zone["coordinates"]:
                print(f"[INFO] Téléportation déclenchée vers {zone['target_map']} aux coordonnées {zone['spawn_position']}")
                new_map = m.Map(zone["target_map"], "collidable_layers.json")
                new_position = zone["spawn_position"]
                return new_map, new_position

        return None, None

