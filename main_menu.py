import pygame
import sys
import os
import math

pygame.init()

# ========== KONSTANSOK ==========

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

UI_HEIGHT = 100                   # Felső UI sáv magassága
TOOLTIP_BG_COLOR = (250, 250, 210)  # Tooltip háttér (világos sárga)
TOOLTIP_TEXT_COLOR = (50, 50, 50)
TOOLTIP_FONT_SIZE = 16

# Színek
WHITE = (255, 255, 255)
LIGHT_GRAY = (220, 220, 220)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
PURPLE = (128, 0, 128)

# Egy egyszerű, előre definiált paletta
DEFAULT_PALETTE = [
    RED, GREEN, BLUE, BLACK, YELLOW, ORANGE, PURPLE, WHITE
]

# ========== ABLAK/RAJZFELÜLET ==========

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Professzionális Rajzolóprogram - PyGame")

# A tényleges rajzfelület (vászon) a felső UI alatt kezdődik
drawing_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT))
drawing_surface.fill(WHITE)

clock = pygame.time.Clock()

# ========== ÁLLAPOT VÁLTOZÓK ==========

current_tool = 'rect'  # 'rect', 'ellipse', 'line', 'eraser'
current_color = BLACK
fill_shapes = True    # True => kitöltött, False => csak körvonal
brush_thickness = 3

shapes = []           # A rajzolt elemek listája (visszavonáshoz, újrarajzoláshoz)
redo_stack = []       # Az Undo műveletek elemei kerülnek ide

mouse_is_down = False
start_pos = (0, 0)
line_points = []

# Tooltip kezelés
tooltip_text = None
tooltip_rect = None

# Súgó (help) overlay mutatása
show_help_overlay = False

# ========== HASZNOS FÜGGVÉNYEK ==========

def redraw_canvas():
    """
    shapes listát végigjárva újrarajzol mindent a drawing_surface-re.
    """
    drawing_surface.fill(WHITE)
    for item in shapes:
        draw_shape_item(item)

def draw_shape_item(item):
    stype = item['type']
    col = item.get('color', BLACK)
    th = item.get('thickness', 1)
    fill = item.get('fill', True)

    if stype in ('rect', 'ellipse'):
        (sx, sy) = item['start']
        (ex, ey) = item['end']
        left = min(sx, ex)
        top = min(sy, ey)
        width = abs(sx - ex)
        height = abs(sy - ey)
        if stype == 'rect':
            if fill:
                pygame.draw.rect(drawing_surface, col, (left, top, width, height))
            else:
                pygame.draw.rect(drawing_surface, col, (left, top, width, height), th)
        else:  # ellipse
            if fill:
                pygame.draw.ellipse(drawing_surface, col, (left, top, width, height))
            else:
                pygame.draw.ellipse(drawing_surface, col, (left, top, width, height), th)

    elif stype == 'line':
        points = item['points']
        if len(points) > 1:
            pygame.draw.lines(drawing_surface, col, False, points, th)

    elif stype == 'eraser':
        points = item['points']
        # Radír => fehér rajzolás
        if len(points) > 1:
            pygame.draw.lines(drawing_surface, WHITE, False, points, th)

def create_shape_data(stype, start=None, end=None, points=None):
    """
    Létrehoz egy rajzolási objektumot. Ez megy a shapes listába.
    """
    if stype in ('rect', 'ellipse'):
        return {
            'type': stype,
            'start': start,
            'end': end,
            'color': current_color,
            'fill': fill_shapes,
            'thickness': brush_thickness
        }
    elif stype == 'line':
        return {
            'type': 'line',
            'points': points,
            'color': current_color,
            'thickness': brush_thickness
        }
    elif stype == 'eraser':
        return {
            'type': 'eraser',
            'points': points,
            'thickness': brush_thickness
        }

def undo():
    if shapes:
        redo_stack.append(shapes.pop())
        redraw_canvas()

def redo():
    if redo_stack:
        shapes.append(redo_stack.pop())
        redraw_canvas()

def save_drawing(filename="drawing.png"):
    pygame.image.save(drawing_surface, filename)
    print(f"Mentve: {filename}")

def load_drawing(filename="drawing.png"):
    if os.path.exists(filename):
        loaded = pygame.image.load(filename)
        drawing_surface.blit(loaded, (0, 0))
        print(f"{filename} betöltve!")
    else:
        print("Nincs mentett fájl a megadott néven.")

def clear_canvas():
    shapes.clear()
    redo_stack.clear()
    drawing_surface.fill(WHITE)
    print("Vászon törölve (fehér).")

# ========== GUI ELEMEK OSZTÁLYAI ==========

class Button:
    """
    Egyszerű gomb, kattintáskor callback.
    Támogatja a tooltipet is.
    """
    def __init__(self, x, y, w, h, text, callback,
                 tooltip=None,
                 font_size=18,
                 bg_color=GRAY,
                 hover_color=DARK_GRAY,
                 text_color=BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.tooltip = tooltip

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont(None, font_size)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            color = self.hover_color
            if self.tooltip:
                show_tooltip(self.tooltip, mouse_pos)
        else:
            color = self.bg_color

        pygame.draw.rect(surface, color, self.rect, border_radius=5)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class ColorSwatch:
    """
    Színválasztó négyzet. Ha rákattintanak, beállítja a global current_color-t.
    Tooltip is lehetséges.
    """
    def __init__(self, x, y, color, size=32, tooltip=None):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = color
        self.tooltip = tooltip

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.rect(surface, self.color, self.rect)
        # Keret
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        if self.rect.collidepoint(mouse_pos) and self.tooltip:
            show_tooltip(self.tooltip, mouse_pos)

    def handle_event(self, event):
        global current_color
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                current_color = self.color
                print(f"Szín beállítva: {current_color}")

class Slider:
    """
    Ecsetvastagság állítása.
    """
    def __init__(self, x, y, w, h, min_val=1, max_val=20, start_val=3, tooltip=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.handle_width = 12
        self.dragging = False
        self.tooltip = tooltip

        self.update_handle_x()

    def update_handle_x(self):
        ratio = (self.value - self.min_val) / float(self.max_val - self.min_val)
        self.handle_x = self.rect.x + int(ratio * (self.rect.w - self.handle_width))

    def value_from_x(self, x_pos):
        rel = x_pos - self.rect.x
        ratio = rel / float(self.rect.w - self.handle_width)
        val = self.min_val + ratio * (self.max_val - self.min_val)
        return int(round(max(self.min_val, min(self.max_val, val))))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        # Sáv
        pygame.draw.rect(surface, DARK_GRAY, self.rect)
        # Fogantyú
        handle_rect = pygame.Rect(self.handle_x, self.rect.y, self.handle_width, self.rect.h)
        pygame.draw.rect(surface, GRAY, handle_rect)

        # Érték kijelzése
        font = pygame.font.SysFont(None, 20)
        text_surf = font.render(str(self.value), True, BLACK)
        text_rect = text_surf.get_rect(midbottom=(handle_rect.centerx, self.rect.y - 2))
        surface.blit(text_surf, text_rect)

        if self.rect.collidepoint(mouse_pos) and self.tooltip:
            show_tooltip(self.tooltip, mouse_pos)

    def handle_event(self, event):
        global brush_thickness

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.handle_x = event.pos[0] - self.handle_width // 2
                self.handle_x = max(self.rect.x, min(self.rect.x + self.rect.w - self.handle_width, self.handle_x))
                self.value = self.value_from_x(self.handle_x)
                brush_thickness = self.value

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = event.pos[0] - self.handle_width // 2
            self.handle_x = max(self.rect.x, min(self.rect.x + self.rect.w - self.handle_width, self.handle_x))
            self.value = self.value_from_x(self.handle_x)
            brush_thickness = self.value

# ========== TOOLTIP MEGOLDÁS ==========

def show_tooltip(text, mouse_pos):
    """
    Ezt meghívja a gomb/slider, ha az egér fölé viszik.
    """
    global tooltip_text, tooltip_rect
    tooltip_text = text
    tooltip_rect = mouse_pos

def draw_tooltip(surface):
    """
    Kirajzolja az épp aktív tooltipet, ha van.
    """
    global tooltip_text, tooltip_rect
    if tooltip_text and tooltip_rect:
        font = pygame.font.SysFont(None, TOOLTIP_FONT_SIZE)
        text_surf = font.render(tooltip_text, True, TOOLTIP_TEXT_COLOR)
        # Köré húzunk egy kis hátteret
        padding = 5
        bg_rect = text_surf.get_rect()
        bg_rect.topleft = (tooltip_rect[0] + 10, tooltip_rect[1] + 10)
        bg_rect.inflate_ip(padding * 2, padding * 2)

        pygame.draw.rect(surface, TOOLTIP_BG_COLOR, bg_rect)
        pygame.draw.rect(surface, BLACK, bg_rect, 1)

        surface.blit(text_surf, (bg_rect.x + padding, bg_rect.y + padding))

    # Minden frame végén töröljük, hogy ne maradjon a következő ciklusokra
    tooltip_text = None
    tooltip_rect = None

# ========== SÚGÓ (HELP) OVERLAY ==========

def draw_help_overlay(surface):
    """
    Egy félig átlátszó fekete rétegre írjunk fehér szöveget, 
    ami elmagyarázza a használatot.
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # fekete, 180-as alfa

    font = pygame.font.SysFont(None, 28)
    lines = [
        "SÚGÓ (HELP)",
        "",
        "Eszközök a felső sávban:",
        "- Téglalap, Ellipszis: kattints és húzd az egérrel.",
        "- Szabadkézi (line), Radír (eraser): lenyomva folyamatos rajzolás.",
        "",
        "Kitöltés / körvonal gomb a kitöltést váltja.",
        "Undo/Redo: visszavonás / újra.",
        "Színpaletta: kattintással színt vált.",
        "Csúszka: ecset/radír vastagság beállítása.",
        "Törlés: teljes rajz törlése.",
        "Mentés / Betöltés: a rajz.png fájlba/fájlból.",
        "",
        "Kilépés: bezárja a programot.",
        "",
        "(Kattints a Help gombra ismét, hogy eltűnjön ez az ablak.)"
    ]

    y_offset = 100
    for line in lines:
        text_surf = font.render(line, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        overlay.blit(text_surf, text_rect)
        y_offset += 40

    surface.blit(overlay, (0, 0))

# ========== CALLBACK FÜGGVÉNYEK A GOMBOKHOZ ==========

def set_tool_rect():
    global current_tool
    current_tool = 'rect'
    print("Eszköz: Téglalap")

def set_tool_ellipse():
    global current_tool
    current_tool = 'ellipse'
    print("Eszköz: Ellipszis")

def set_tool_line():
    global current_tool
    current_tool = 'line'
    print("Eszköz: Szabadkézi")

def set_tool_eraser():
    global current_tool
    current_tool = 'eraser'
    print("Eszköz: Radír")

def toggle_fill():
    global fill_shapes
    fill_shapes = not fill_shapes
    if fill_shapes:
        print("Alakzatok: kitöltött")
    else:
        print("Alakzatok: körvonalas")

def undo_cb():
    undo()
    print("Visszavonás (Undo)")

def redo_cb():
    redo()
    print("Újra (Redo)")

def clear_cb():
    clear_canvas()

def save_cb():
    save_drawing("rajz.png")

def load_cb():
    load_drawing("rajz.png")

def toggle_help():
    global show_help_overlay
    show_help_overlay = not show_help_overlay

def exit_program():
    pygame.quit()
    sys.exit()

# ========== GUI ELEMEK LÉTREHOZÁSA ==========

buttons = []
color_swatches = []
slider = None

def create_ui():
    global slider
    button_x = 10
    button_y = 10
    button_w = 80
    button_h = 30
    spacing = 10

    def add_button(text, callback, tip=None):
        nonlocal button_x
        btn = Button(
            button_x,
            button_y,
            button_w,
            button_h,
            text,
            callback,
            tooltip=tip
        )
        buttons.append(btn)
        button_x += button_w + spacing

    # Eszközgombok
    add_button("Téglalap", set_tool_rect, "Téglalap rajzolása")
    add_button("Ellipszis", set_tool_ellipse, "Ellipszis rajzolása")
    add_button("Szabadkézi", set_tool_line, "Szabadkézi rajzolás")
    add_button("Radír", set_tool_eraser, "Radírozás")

    # Kitöltés
    add_button("Kitöltés", toggle_fill, "Váltás: kitöltés / körvonal")

    # Undo / Redo
    add_button("Undo", undo_cb, "Visszavonás")
    add_button("Redo", redo_cb, "Újra")

    # Törlés / Mentés / Betöltés
    add_button("Törlés", clear_cb, "Teljes vászon törlése")
    add_button("Mentés", save_cb, "Kép mentése rajz.png-be")
    add_button("Betöltés", load_cb, "Kép betöltése rajz.png-ből")

    # Súgó + Kilépés
    add_button("Help", toggle_help, "Súgó megjelenítése")
    add_button("Kilépés", exit_program, "Program bezárása")

    # Színpaletta
    pal_x = button_x + 20
    pal_y = 10
    for col in DEFAULT_PALETTE:
        cw = ColorSwatch(pal_x, pal_y, col, size=30, tooltip=f"Szín: {col}")
        color_swatches.append(cw)
        pal_x += 35

    # Csúszka (ecsetvastagság)
    slider_x = pal_x + 20
    slider_y = 15
    slider_w = 150
    slider_h = 20
    slider = Slider(slider_x, slider_y, slider_w, slider_h,
                    min_val=1, max_val=30, start_val=3,
                    tooltip="Ecset-/radírvastagság")
    return slider

slider = create_ui()

# ========== FŐ CIKLUS ==========

running = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Gombok, színválasztó, slider kezelése
        for b in buttons:
            b.handle_event(event)
        for c in color_swatches:
            c.handle_event(event)
        slider.handle_event(event)

        # Egér a rajzfelületen
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[1] > UI_HEIGHT:  # A UI alatti területre kattint
                mouse_is_down = True
                redo_stack.clear()  # új alakzat => redo törlődik

                # Rögzítjük a kezdőpontot
                if current_tool in ('rect', 'ellipse'):
                    start_pos = (event.pos[0], event.pos[1] - UI_HEIGHT)
                elif current_tool in ('line', 'eraser'):
                    line_points = [(event.pos[0], event.pos[1] - UI_HEIGHT)]

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if mouse_is_down:
                mouse_is_down = False
                # Befejezzük az alakzatot / vonalat
                if current_tool in ('rect', 'ellipse'):
                    end_pos = (event.pos[0], event.pos[1] - UI_HEIGHT)
                    shape_data = create_shape_data(current_tool, start=start_pos, end=end_pos)
                    shapes.append(shape_data)
                    draw_shape_item(shape_data)

                elif current_tool in ('line', 'eraser'):
                    if len(line_points) > 1:
                        shape_data = create_shape_data(current_tool, points=line_points)
                        shapes.append(shape_data)
                line_points = []

        elif event.type == pygame.MOUSEMOTION:
            if mouse_is_down and event.pos[1] > UI_HEIGHT:
                if current_tool in ('line', 'eraser'):
                    line_points.append((event.pos[0], event.pos[1] - UI_HEIGHT))
                    if len(line_points) > 1:
                        # Rajzolás valós időben
                        if current_tool == 'line':
                            pygame.draw.line(drawing_surface, current_color,
                                             line_points[-2], line_points[-1],
                                             brush_thickness)
                        else:
                            pygame.draw.line(drawing_surface, WHITE,
                                             line_points[-2], line_points[-1],
                                             brush_thickness)

    # ========== KÉPERNYŐ KIRAJZOLÁS ==========

    # 1. Felső sáv
    screen.fill(LIGHT_GRAY, (0, 0, SCREEN_WIDTH, UI_HEIGHT))

    # 2. Gombok, csúszka, színnégyzetek
    for b in buttons:
        b.draw(screen)
    for c in color_swatches:
        c.draw(screen)
    slider.draw(screen)

    # 3. Rajzfelület
    screen.blit(drawing_surface, (0, UI_HEIGHT))

    # 4. Előnézet (téglalap, ellipszis húzásnál)
    if mouse_is_down and current_tool in ('rect', 'ellipse'):
        preview_surf = drawing_surface.copy()
        mx, my = pygame.mouse.get_pos()
        if my > UI_HEIGHT:
            end_pos = (mx, my - UI_HEIGHT)
            temp_data = create_shape_data(current_tool, start=start_pos, end=end_pos)
            draw_shape_item(temp_data)
            screen.blit(preview_surf, (0, UI_HEIGHT))

    # 5. Súgó overlay
    if show_help_overlay:
        draw_help_overlay(screen)

    # 6. Tooltip (ha van)
    draw_tooltip(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
