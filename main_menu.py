import pygame
import sys
import os

pygame.init()

# --- Ablak beállítások ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
UI_HEIGHT = 50  # A felső UI sáv magassága

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rajzolóprogram - Egyszerű GUI-val")

# --- Színek ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Gombokhoz használhatunk többféle színt (alap, hovered, stb.):
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER = (160, 160, 160)
BUTTON_TEXT_COLOR = BLACK

# Előre definiált színváltozatok egy dict-ben
colors = {
    "Piros": RED,
    "Zöld": GREEN,
    "Kék": BLUE
}

# --- Globális rajz-állapotok ---
current_shape = 'rect'  # 'rect' vagy 'ellipse'
current_color = RED
filled = True  # kitöltés flag

# Rajzfelület (külön Surface)
drawing_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT))
drawing_surface.fill(WHITE)

# Gomb definiálása segédfüggvénnyel:
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.base_color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER
        self.text_color = BUTTON_TEXT_COLOR
        self.font = pygame.font.SysFont(None, 20)

    def draw(self, surface):
        # Egér fölé van-e húzva?
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            color = self.hover_color
        else:
            color = self.base_color

        pygame.draw.rect(surface, color, self.rect)

        # Szöveg kiírása
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        """Ha egérkattintás történt a gomb területén, akkor hívja a callback-et."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

# --- Callback függvények a gombokhoz ---
def set_shape_rect():
    global current_shape
    current_shape = 'rect'
    print("Téglalap mód.")

def set_shape_ellipse():
    global current_shape
    current_shape = 'ellipse'
    print("Ellipszis mód.")

def toggle_fill():
    global filled
    filled = not filled
    if filled:
        print("Kitöltött alakzat.")
    else:
        print("Körvonalas alakzat.")

def set_color_red():
    global current_color
    current_color = RED
    print("Szín: piros.")

def set_color_green():
    global current_color
    current_color = GREEN
    print("Szín: zöld.")

def set_color_blue():
    global current_color
    current_color = BLUE
    print("Szín: kék.")

def save_drawing():
    filename = "rajz_gui.png"
    # Képet úgy mentjük, hogy a drawing_surface-en lévő rajzot elmentjük.
    pygame.image.save(drawing_surface, filename)
    print(f"Rajz mentve: {filename}")

def load_drawing():
    filename = "rajz_gui.png"
    if os.path.exists(filename):
        loaded = pygame.image.load(filename)
        drawing_surface.blit(loaded, (0, 0))
        print("Kép betöltve.")
    else:
        print("Nincs mentett kép a fájlban.")

def clear_drawing():
    drawing_surface.fill(WHITE)
    print("Vászon törölve (fehér).")

def exit_program():
    pygame.quit()
    sys.exit()

# --- Gombok létrehozása és elhelyezése ---
buttons = []
# Bal oldalra formázott gombok, mindegyik 80px széles, 30px magas, kis hézagokkal
button_x = 10
button_y = 10
button_width = 80
button_height = 30
button_spacing = 10

def add_button(label, callback):
    global button_x
    new_button = Button(button_x, button_y, button_width, button_height, label, callback)
    buttons.append(new_button)
    button_x += (button_width + button_spacing)

# Alakzat gombok
add_button("Téglalap", set_shape_rect)
add_button("Ellipszis", set_shape_ellipse)

# Kitöltés gomb
add_button("Kitöltés", toggle_fill)

# Szín gombok
add_button("Piros", set_color_red)
add_button("Zöld", set_color_green)
add_button("Kék", set_color_blue)

# Egyéb funkció gombok
add_button("Mentés", save_drawing)
add_button("Betöltés", load_drawing)
add_button("Törlés", clear_drawing)
add_button("Kilépés", exit_program)

# --- Segédfüggvény rajzoláshoz ---
def draw_shape(surface, shape, color, start_pos, end_pos, filled):
    """
    shape: 'rect' vagy 'ellipse'
    color: (R, G, B) tuple
    start_pos, end_pos: (x, y) koordináták
    filled: True => kitöltött, False => körvonal
    """
    x1, y1 = start_pos
    x2, y2 = end_pos
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

# --- Főprogram ciklus ---
clock = pygame.time.Clock()
running = True

start_pos = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Gombok eseménykezelése
        for btn in buttons:
            btn.handle_event(event)

        # Egérkezelés a rajzfelületen
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            # Ellenőrizzük, hogy a rajzfelületre kattintott-e a felhasználó (a UI alatt)
            if mouse_y > UI_HEIGHT:  # a UI HEIGHT felett helyezkedik el a rajz
                # Ekkor indul a rajzolás
                # A rajzfelület koordinátáihoz igazítjuk (levonjuk a UI_HEIGHT-et)
                start_pos = (mouse_x, mouse_y - UI_HEIGHT)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if start_pos is not None:
                mouse_x, mouse_y = event.pos
                if mouse_y > UI_HEIGHT:
                    end_pos = (mouse_x, mouse_y - UI_HEIGHT)
                    draw_shape(drawing_surface, current_shape, current_color, start_pos, end_pos, filled)
                start_pos = None

    # --- UI kirajzolás ---
    screen.fill(GRAY)  # háttérszín a felső sávnak
    # Gombok
    for btn in buttons:
        btn.draw(screen)

    # Rajzfelület kirajzolása a gombok alá
    screen.blit(drawing_surface, (0, UI_HEIGHT))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
