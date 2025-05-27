import pygame
import sys
import os

pygame.init()

# ========== ABLAK MÉRETEK, ALAPÉRTELMEZÉSEK ==========

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

UI_HEIGHT = 80           # A felső UI sáv magassága
COLOR_PALETTE_SIZE = 30  # Egy színnégyzet mérete a palettán
SLIDER_WIDTH = 120       # Ecsetvastagság csúszka szélessége
SLIDER_HEIGHT = 20

# Színek
WHITE = (255, 255, 255)
GRAY = (220, 220, 220)
DARK_GRAY = (140, 140, 140)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
PURPLE = (128, 0, 128)

# Előre definiált színpaletta (bővíthető)
COLOR_PALETTE = [
    RED, GREEN, BLUE, BLACK, YELLOW, ORANGE, PURPLE, WHITE
]

# ========== KÉPERNYŐ BEÁLLÍTÁSOK ==========

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Legjobb Pygame Rajzoló - GUI-val")

# A rajzfelület (ahová ténylegesen rajzolunk) a képernyő UI alatti részében foglal helyet
drawing_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT))
drawing_surface.fill(WHITE)

clock = pygame.time.Clock()

# ========== ÁLLAPOTVÁLTOZÓK ==========

current_tool = 'rect'      # Lehetséges: rect, ellipse, line (szabadkézi), eraser
current_color = BLACK
fill_shapes = True         # True => kitöltött, False => körvonal
brush_thickness = 3        # Alapértelmezett ecsetvastagság

# Visszavonáshoz (undo) és újra (redo) listák
# A "shapes" listában eltárolunk minden rajzolt elemet (alakzatokat, vonalakat).
# Egy elem pl. ilyen lehet:
# {
#   "type": "rect"/"ellipse"/"line"/"eraser",
#   "start": (x, y),
#   "end": (x, y),        # vonalnál pl. sok pont
#   "points": [...],      # szabadkézi rajz esetén
#   "color": (R, G, B),
#   "fill": True/False,
#   "thickness": int
# }
shapes = []
redo_stack = []

# Az épp rajzolt (de még be nem fejezett) objektum átmeneti tárolására
current_drawing = None

# ========== OSZTÁLYOK ==========

class Button:
    """
    Egyszerű gomb-osztály, ami téglalapot rajzol, benne szöveggel.
    Ha rákattintanak, meghívja a callback függvényt.
    """
    def __init__(self, x, y, w, h, text, callback, font_size=18,
                 bg_color=GRAY, hover_color=DARK_GRAY, text_color=BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont(None, font_size)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            color = self.hover_color
        else:
            color = self.bg_color

        pygame.draw.rect(surface, color, self.rect, border_radius=5)

        # Szöveg megjelenítése középen
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class ColorSwatch:
    """
    Kis négyzet a színpalettán. Ha rákattintanak, beállítja a kiválasztott színt.
    """
    def __init__(self, x, y, color, size=COLOR_PALETTE_SIZE):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 1)  # keret

    def handle_event(self, event):
        global current_color
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                current_color = self.color

class Slider:
    """
    Egyszerű 'csúszka' a brush_thickness beállítására.
    """
    def __init__(self, x, y, w, h, min_val=1, max_val=20, start_val=3):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.dragging = False

        # Belső mozgó "fogantyú"
        self.handle_width = 10
        self.handle_height = h
        self.handle_x = self.value_to_x(start_val)

    def value_to_x(self, val):
        """Lineáris leképezés: (min_val..max_val) -> a slider szélességére."""
        ratio = (val - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * (self.rect.w - self.handle_width))

    def x_to_value(self, x_pos):
        """Az x koordinátából visszaadja a slider értékét."""
        relative_x = x_pos - self.rect.x
        ratio = relative_x / float(self.rect.w - self.handle_width)
        val = self.min_val + ratio * (self.max_val - self.min_val)
        return int(round(max(self.min_val, min(self.max_val, val))))

    def draw(self, surface):
        # Csúszka sín
        pygame.draw.rect(surface, DARK_GRAY, self.rect)
        # Fogantyú
        handle_rect = pygame.Rect(self.handle_x, self.rect.y, 
                                  self.handle_width, self.handle_height)
        pygame.draw.rect(surface, GRAY, handle_rect)

        # Kiírjuk az aktuális értéket is (felette)
        font = pygame.font.SysFont(None, 18)
        text_surf = font.render(str(self.value), True, BLACK)
        text_rect = text_surf.get_rect(midbottom=(handle_rect.centerx, self.rect.y - 2))
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        global brush_thickness
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.handle_x = event.pos[0] - (self.handle_width // 2)
                self.handle_x = max(self.rect.x, min(self.rect.x + self.rect.w - self.handle_width, self.handle_x))
                self.value = self.x_to_value(self.handle_x)
                brush_thickness = self.value

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = event.pos[0] - (self.handle_width // 2)
            self.handle_x = max(self.rect.x, min(self.rect.x + self.rect.w - self.handle_width, self.handle_x))
            self.value = self.x_to_value(self.handle_x)
            brush_thickness = self.value

# ========== CALLBACK FÜGGVÉNYEK A GOMBOKHOZ ==========

def set_tool_rect():
    global current_tool
    current_tool = 'rect'
    print("Eszköz: Téglalap.")

def set_tool_ellipse():
    global current_tool
    current_tool = 'ellipse'
    print("Eszköz: Ellipszis.")

def set_tool_line():
    global current_tool
    current_tool = 'line'
    print("Eszköz: Szabadkézi rajz.")

def set_tool_eraser():
    global current_tool
    current_tool = 'eraser'
    print("Eszköz: Radír.")

def toggle_fill():
    global fill_shapes
    fill_shapes = not fill_shapes
    if fill_shapes:
        print("Alakzatok: kitöltve.")
    else:
        print("Alakzatok: körvonal.")

def undo_action():
    if shapes:
        # A shapes utolsó elemét áttesszük a redo_stack-be
        redo_stack.append(shapes.pop())
        redraw_all()
        print("Visszavonás (Undo) megtörtént.")

def redo_action():
    if redo_stack:
        shapes.append(redo_stack.pop())
        redraw_all()
        print("Újra (Redo) megtörtént.")

def clear_canvas():
    shapes.clear()
    redo_stack.clear()
    drawing_surface.fill(WHITE)
    print("Vászon törölve (fehér).")

def save_drawing():
    filename = "best_drawing.png"
    pygame.image.save(drawing_surface, filename)
    print(f"Rajz mentve: {filename}")

def load_drawing():
    filename = "best_drawing.png"
    if os.path.exists(filename):
        loaded = pygame.image.load(filename)
        drawing_surface.blit(loaded, (0, 0))
        # Mentett rajzot nem konvertáljuk vissza "shapes" listába, 
        # de ha szeretnénk, bonyolultabb formátumot (pl. JSON) kellene használni.
        print("Kép betöltve.")
    else:
        print("Nincs elmentett rajz.")

def exit_program():
    pygame.quit()
    sys.exit()

# ========== GOMBOK, UI ELEMEK LÉTREHOZÁSA ==========

buttons = []
color_swatches = []
slider = None

def create_ui():
    global slider

    # Gombméretek, elhelyezés
    button_x = 10
    button_y = 10
    button_w = 80
    button_h = 30
    spacing = 10

    def add_button(text, callback):
        nonlocal button_x
        btn = Button(button_x, button_y, button_w, button_h, text, callback)
        buttons.append(btn)
        button_x += (button_w + spacing)

    # Eszközgombok
    add_button("Téglalap", set_tool_rect)
    add_button("Ellipszis", set_tool_ellipse)
    add_button("Szabadkézi", set_tool_line)
    add_button("Radír", set_tool_eraser)
    add_button("Kitöltés", toggle_fill)

    # Undo/Redo gombok
    add_button("Undo", undo_action)
    add_button("Redo", redo_action)

    # Törlés / Mentés / Betöltés / Kilépés
    add_button("Törlés", clear_canvas)
    add_button("Mentés", save_drawing)
    add_button("Betöltés", load_drawing)
    add_button("Kilépés", exit_program)

    # Színpaletta elhelyezése
    # Induljon a jobb oldalon, vagy legalábbis kicsit arrébb:
    palette_x = button_x
    palette_y = 10
    for col in COLOR_PALETTE:
        sw = ColorSwatch(palette_x, palette_y, col)
        color_swatches.append(sw)
        palette_x += (COLOR_PALETTE_SIZE + 5)

    # Ecsetvastagság csúszka
    slider_x = palette_x + 20
    slider_y = 20
    slider = Slider(slider_x, slider_y, SLIDER_WIDTH, SLIDER_HEIGHT, min_val=1, max_val=20, start_val=3)

def redraw_all():
    """
    A shapes listában tárolt összes objektumot újrarajzolja a drawing_surface-re.
    """
    drawing_surface.fill(WHITE)
    for shape_data in shapes:
        draw_shape_from_data(shape_data)

def draw_shape_from_data(data):
    """
    A shape_data alapján kirajzol egy objektumot (téglalap, ellipszis, vonal, radír) a drawing_surface-re.
    """
    st = data.get("type")
    col = data.get("color")
    th = data.get("thickness", 1)
    fill = data.get("fill", True)
    if st in ("rect", "ellipse"):
        start_x, start_y = data["start"]
        end_x, end_y = data["end"]
        left = min(start_x, end_x)
        top = min(start_y, end_y)
        width = abs(start_x - end_x)
        height = abs(start_y - end_y)

        if st == "rect":
            if fill:
                pygame.draw.rect(drawing_surface, col, (left, top, width, height))
            else:
                pygame.draw.rect(drawing_surface, col, (left, top, width, height), th)
        else:  # ellipse
            if fill:
                pygame.draw.ellipse(drawing_surface, col, (left, top, width, height))
            else:
                pygame.draw.ellipse(drawing_surface, col, (left, top, width, height), th)

    elif st == "line":
        # "points" lista
        points = data["points"]
        if len(points) > 1:
            pygame.draw.lines(drawing_surface, col, False, points, th)

    elif st == "eraser":
        # "points" lista, fehér színnel rajzol (radíroz)
        points = data["points"]
        if len(points) > 1:
            pygame.draw.lines(drawing_surface, WHITE, False, points, th)

def create_shape_data(tool, start_pos, end_pos=None, points=None):
    """
    Létrehoz egy dict-et, amely a shapes listába kerül majd.
    """
    if tool in ("rect", "ellipse"):
        return {
            "type": tool,
            "start": start_pos,
            "end": end_pos,
            "color": current_color,
            "fill": fill_shapes,
            "thickness": brush_thickness
        }
    elif tool == "line":
        return {
            "type": "line",
            "points": points,  # Szabadkézi rajz pontjai
            "color": current_color,
            "thickness": brush_thickness
        }
    elif tool == "eraser":
        return {
            "type": "eraser",
            "points": points,  # Radírozó pontjai
            "thickness": brush_thickness
        }

# ========== FŐ PROGRAM ==========

create_ui()
running = True

mouse_is_down = False
start_pos = (0, 0)
line_points = []

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Gombok, színválasztók, csúszka kezelése
        for btn in buttons:
            btn.handle_event(event)
        for sw in color_swatches:
            sw.handle_event(event)
        slider.handle_event(event)

        # Egéresemények a rajzfelületen
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            # Csak akkor rajzolunk, ha a UI alatti területre kattint
            if mouse_y > UI_HEIGHT:
                mouse_is_down = True
                redo_stack.clear()  # Ha új dologba kezdünk, a redo stacket töröljük

                if current_tool in ("rect", "ellipse"):
                    start_pos = (mouse_x, mouse_y - UI_HEIGHT)
                    # Ideiglenesen még nem rakjuk be a shapes-be,
                    # csak akkor, ha felengedik az egeret.

                elif current_tool in ("line", "eraser"):
                    line_points = [(mouse_x, mouse_y - UI_HEIGHT)]

        elif event.type == pygame.MOUSEMOTION:
            if mouse_is_down:
                mouse_x, mouse_y = event.pos
                if mouse_y > UI_HEIGHT:
                    if current_tool in ("line", "eraser"):
                        # Folyamatosan gyűjtjük a pontokat
                        line_points.append((mouse_x, mouse_y - UI_HEIGHT))
                        # Rajzolunk is real-time
                        if current_tool == "line":
                            pygame.draw.line(drawing_surface, current_color,
                                             line_points[-2], line_points[-1], brush_thickness)
                        else:  # eraser
                            pygame.draw.line(drawing_surface, WHITE,
                                             line_points[-2], line_points[-1], brush_thickness)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if mouse_is_down:
                mouse_x, mouse_y = event.pos
                mouse_is_down = False

                if mouse_y > UI_HEIGHT:
                    if current_tool in ("rect", "ellipse"):
                        end_pos = (mouse_x, mouse_y - UI_HEIGHT)
                        shape_data = create_shape_data(current_tool, start_pos, end_pos=end_pos)
                        shapes.append(shape_data)
                        draw_shape_from_data(shape_data)

                    elif current_tool in ("line", "eraser"):
                        if len(line_points) > 1:
                            shape_data = create_shape_data(current_tool, None, None, line_points)
                            shapes.append(shape_data)
                        line_points = []

    # Előnézet rajzolása (pl. téglalapnál, ellipszisnél) - "rubber band" effect
    # Ehhez frissítjük a főképernyőt minden ciklusban
    screen.fill(GRAY)  # UI háttér
    # Gombok
    for btn in buttons:
        btn.draw(screen)
    # Színpaletta
    for sw in color_swatches:
        sw.draw(screen)
    # Csúszka
    slider.draw(screen)

    # Felhasználó éppen húzza az egeret? Mutassuk az alakuló alakzatot
    # (Csak rect/ellipse esetén)
    preview_surface = drawing_surface.copy()
    if mouse_is_down and current_tool in ("rect", "ellipse"):
        mx, my = pygame.mouse.get_pos()
        if my > UI_HEIGHT:
            temp_end = (mx, my - UI_HEIGHT)
            shape_data = create_shape_data(current_tool, start_pos, end_pos=temp_end)
            draw_shape_from_data(shape_data)

            # Kirajzoljuk a preview-t a "drawing_surface" helyett a "screen"-re,
            # hogy ne rögzüljön, csak vizuális előnézet legyen.
            screen.blit(drawing_surface, (0, UI_HEIGHT))
            screen.blit(preview_surface, (0, UI_HEIGHT))
        else:
            # Ha UI-n mozog, akkor egyszerűen csak a drawing_surface rajza
            screen.blit(drawing_surface, (0, UI_HEIGHT))
    else:
        # Ha nincs preview, csak simán rajzoljuk a kész rajzot
        screen.blit(drawing_surface, (0, UI_HEIGHT))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
