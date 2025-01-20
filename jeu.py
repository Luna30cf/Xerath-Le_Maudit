import pygame
import pytmx

# Dimensions d'une tuile (selon votre map Tiled)
TILE_WIDTH = 32
TILE_HEIGHT = 32

# Vitesse du personnage en pixels par frame
PLAYER_SPEED = 3

def load_tmx_map(filename):
    """
    Charge le fichier Tiled (.tmx) à l'aide de pytmx.
    Retourne l'objet TiledMap (tmx_data).
    """
    tmx_data = pytmx.util_pygame.load_pygame(filename)
    return tmx_data

def draw_map(screen, tmx_data):
    """
    Dessine la carte Tiled à l'écran (layer par layer).
    """
    # Parcours toutes les couches
    for layer in tmx_data.visible_layers:
        # S’il s’agit d’un layer de type TiledTileLayer
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid != 0:  # 0 = pas de tuile
                    tile_image = tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        screen.blit(tile_image, (x * TILE_WIDTH, y * TILE_HEIGHT))

def get_colliding_tiles(tmx_data):
    """
    Récupère les coordonnées (x, y) des tuiles qui ont la propriété 'collides' = True.
    On retourne une liste de rectangles (pygame.Rect) correspondant à ces tuiles.
    """
    colliders = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid != 0:
                    tile_props = tmx_data.get_tile_properties_by_gid(gid)
                    if tile_props and tile_props.get('collides'):
                        # Crée un rectangle aux coordonnées de la tuile
                        rect = pygame.Rect(
                            x * TILE_WIDTH,
                            y * TILE_HEIGHT,
                            TILE_WIDTH,
                            TILE_HEIGHT
                        )
                        colliders.append(rect)
    return colliders

def main():
    pygame.init()
    
    # Chargement de la carte
    tmx_data = load_tmx_map("map.tmx")
    
    # Récupération largeur/hauteur en nombre de tuiles (selon la 1ère couche)
    map_width = tmx_data.width
    map_height = tmx_data.height
    
    # Calcul de la taille de la fenêtre (en pixels)
    screen_width = map_width * TILE_WIDTH
    screen_height = map_height * TILE_HEIGHT
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Petit jeu Tiled + Pygame")
    
    clock = pygame.time.Clock()

    # Chargement sprite perso
    # On suppose un sprite 32x32 pixels
    player_image = pygame.image.load("character.png").convert_alpha()
    player_rect = player_image.get_rect()
    # Position initiale (ex: en haut à gauche)
    player_rect.topleft = (50, 50)
    
    # Récupère la liste des "tuiles bloquantes"
    colliders = get_colliding_tiles(tmx_data)
    
    running = True
    while running:
        dt = clock.tick(60)  # Limite à 60 FPS (dt = temps en ms depuis la dernière frame)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Gestion des touches
        keys = pygame.key.get_pressed()
        
        # Sauvegarde l'ancienne position (pour gérer collisions)
        old_x, old_y = player_rect.x, player_rect.y
        
        # Déplacement horizontal
        if keys[pygame.K_LEFT]:
            player_rect.x -= PLAYER_SPEED
        elif keys[pygame.K_RIGHT]:
            player_rect.x += PLAYER_SPEED
        
        # Déplacement vertical
        if keys[pygame.K_UP]:
            player_rect.y -= PLAYER_SPEED
        elif keys[pygame.K_DOWN]:
            player_rect.y += PLAYER_SPEED
        
        # Vérifie collisions basiques avec les tuiles "collides"
        player_hit = False
        for collider in colliders:
            if player_rect.colliderect(collider):
                player_hit = True
                break
        
        # Si le perso est en collision, on annule le déplacement
        if player_hit:
            player_rect.x, player_rect.y = old_x, old_y
        
        # Dessin
        screen.fill((0, 0, 0))  # Efface l'écran (fond noir)
        
        # Dessine la map
        draw_map(screen, tmx_data)
        
        # Dessine le joueur
        screen.blit(player_image, player_rect)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
