import pygame
import sys
import os

pygame.init()

# --- Ablak beállítások ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Egyszerű rajzoló PyGame-mel")

# --- Segéd-függvények ---
def draw_shape(surface, shape, color, start_pos, end_pos, filled):
    """
    shape: 'rect' vagy 'ellipse'
    color: (R, G, B) formátumú tuple
    start_pos, end_pos: (x, y) kezdő és végpont
    filled: True => kitöltött, False => körvonal
    """
    x1, y1 = start_pos
    x2, y2 = end_pos
    # Rendezés, hogy negatív méret ne legyen gond:
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x1 - x2)
    height = abs(y1 - y2)

    if shape == 'rect':
        if filled:
            pygame.draw.rect(surface, color, (left, top, width, height))
        else:
            pygame.draw.rect(surface, color, (left, top, width, height), 2)

    elif shape == 'ellipse':
        if filled:
            pygame.draw.ellipse(surface, color, (left, top, width, height))
        else:
            pygame.draw.ellipse(surface, color, (left, top, width, height), 2)

def save_drawing(surface, filename="rajz.png"):
    """
    A teljes felület mentése egy képfájlba.
    """
    pygame.image.save(surface, filename)
    print(f"Kép mentve ide: {filename}")

def load_drawing(filename="rajz.png"):
    """
    Megpróbálja betölteni a korábban elmentett képet.
    Ha sikeres, egy új Surface objektumot ad vissza.
    """
    if os.path.exists(filename):
        loaded_image = pygame.image.load(filename)
        return loaded_image
    else:
        print(f"Nincs ilyen fájl: {filename}")
        return None

# --- Alapbeállítások ---
clock = pygame.time.Clock()
running = True

# Kezdeti állapotok
current_shape = 'rect'      # 'rect' vagy 'ellipse'
colors = {
    1: (255, 0, 0),   # piros
    2: (0, 255, 0),   # zöld
    3: (0, 0, 255)    # kék
}
current_color = colors[1]
filled = True  # kitöltés flag

start_pos = None   # rajzolás kezdőpontja
end_pos = None     # rajzolás végpontja

# Egy látható felület, amin rajzolunk:
drawing_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
drawing_surface.fill((255, 255, 255))  # fehér háttér

while running:
    # Eseménykezelés
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            # Alakzatváltás
            if event.key == pygame.K_r:
                current_shape = 'rect'
                print("Téglalap rajzolás mód")
            elif event.key == pygame.K_e:
                current_shape = 'ellipse'
                print("Ellipszis rajzolás mód")

            # Színváltás
            elif event.key == pygame.K_1:
                current_color = colors[1]
                print("Piros szín")
            elif event.key == pygame.K_2:
                current_color = colors[2]
                print("Zöld szín")
            elif event.key == pygame.K_3:
                current_color = colors[3]
                print("Kék szín")

            # Kitöltés váltása
            elif event.key == pygame.K_f:
                filled = not filled
                if filled:
                    print("Kitöltött mód")
                else:
                    print("Körvonal mód")

            # Mentés
            elif event.key == pygame.K_s:
                save_drawing(drawing_surface, "rajz.png")

            # Betöltés
            elif event.key == pygame.K_l:
                loaded_image = load_drawing("rajz.png")
                if loaded_image:
                    drawing_surface.blit(loaded_image, (0, 0))
                    print("Betöltés sikeres")

            # Képernyő törlése (pl. C gomb)
            elif event.key == pygame.K_c:
                drawing_surface.fill((255, 255, 255))
                print("Vászon törölve (fehér)")

            # Kilépés (Esc)
            elif event.key == pygame.K_ESCAPE:
                running = False

        # Egérkezelés
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Bal gomb lenyomása: kezdőpont rögzítése
            if event.button == 1:
                start_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            # Bal gomb felengedése: végpont rögzítése és rajzolás
            if event.button == 1 and start_pos is not None:
                end_pos = event.pos
                # Rajzolás a drawing_surface-re
                draw_shape(drawing_surface, current_shape, current_color, 
                           start_pos, end_pos, filled)
                # Visszaállítás None-ra, hogy újrajelenítsük a kezdeti állapotot
                start_pos = None
                end_pos = None

    # A főképernyő (screen) mindig a drawing_surface aktuális állapotát mutatja
    screen.blit(drawing_surface, (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
