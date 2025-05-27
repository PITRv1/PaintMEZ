import pygame
import sys
import os

pygame.init()

# ========== ALAP BEÁLLÍTÁSOK ==========

SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 900
UI_HEIGHT = 140  # Megnövelt UI-sáv a gombokhoz (több sor + logó)

LIGHT_GRAY = (220, 220, 220)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
PURPLE = (128, 0, 128)
LOGO_COLOR = (0, 150, 200)

DEFAULT_PALETTE = [RED, GREEN, BLUE, BLACK, YELLOW, ORANGE, PURPLE, WHITE]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PaintMEZ - Többrétegű Rajz, Egyéni Színnel")

clock = pygame.time.Clock()

# ========== RAJZ-FUNKCIÓKHOZ TARTOZÓ ÁLLAPOT ==========

current_tool = 'rect'   # 'rect', 'ellipse', 'line', 'eraser'
current_color = BLACK
fill_shapes = True
brush_thickness = 3

mouse_is_down = False
start_pos = (0, 0)
line_points = []

# ========== TÖBBSZÖRÖS RÉTEG KEZELÉS (vázlat) ==========

class Layer:
    def __init__(self, name="Layer", background_color=None):
        self.name = name
        self.background_color = background_color
        self.shapes = []
        self.redo_stack = []
        self.visible = True

layers = [
    Layer(name="Base Layer", background_color=WHITE)
]
current_layer_index = 0

def get_current_layer():
    return layers[current_layer_index]

def add_layer():
    new_layer = Layer(name=f"Layer {len(layers)}", background_color=None)
    layers.append(new_layer)
    print(f"Új réteg: {new_layer.name}")

def remove_layer():
    global current_layer_index
    if len(layers) > 1:
        removed = layers.pop(current_layer_index)
        print(f"Réteg törölve: {removed.name}")
        current_layer_index = max(0, current_layer_index - 1)
    else:
        print("Nem törölhető az utolsó réteg.")

def next_layer():
    global current_layer_index
    current_layer_index = (current_layer_index + 1) % len(layers)
    print(f"Aktív réteg: {layers[current_layer_index].name}")

def previous_layer():
    global current_layer_index
    current_layer_index = (current_layer_index - 1) % len(layers)
    print(f"Aktív réteg: {layers[current_layer_index].name}")

def set_layer_background_color(color):
    layer = get_current_layer()
    layer.background_color = color
    print(f"Réteg háttérszíne: {color} ({layer.name})")

# ========== UNDO/REDO, TÖRLÉS ==========

def layer_undo():
    layer = get_current_layer()
    if layer.shapes:
        layer.redo_stack.append(layer.shapes.pop())
        print(f"Réteg '{layer.name}' - Undo")
    else:
        print("Nincs mit visszavonni.")

def layer_redo():
    layer = get_current_layer()
    if layer.redo_stack:
        layer.shapes.append(layer.redo_stack.pop())
        print(f"Réteg '{layer.name}' - Redo")

def clear_current_layer():
    layer = get_current_layer()
    layer.shapes.clear()
    layer.redo_stack.clear()
    print(f"Réteg '{layer.name}' törölve.")

# ========== SHAPES KEZELÉS, RAJZOLÁS EGY RÉTEGRE ==========

def create_shape_data(stype, start=None, end=None, points=None):
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

def draw_shape_item(surface, item):
    stype = item['type']
    if stype == 'loaded_image':
        loaded_img = item['surface']
        surface.blit(loaded_img, (0, 0))
        return

    th = item.get('thickness', 1)
    if stype in ('rect', 'ellipse'):
        sx, sy = item['start']
        ex, ey = item['end']
        left = min(sx, ex)
        top = min(sy, ey)
        width = abs(sx - ex)
        height = abs(sy - ey)
        color = item.get('color', BLACK)
        fill = item.get('fill', True)

        if stype == 'rect':
            if fill:
                pygame.draw.rect(surface, color, (left, top, width, height))
            else:
                pygame.draw.rect(surface, color, (left, top, width, height), th)
        else:  # ellipse
            if fill:
                pygame.draw.ellipse(surface, color, (left, top, width, height))
            else:
                pygame.draw.ellipse(surface, color, (left, top, width, height), th)

    elif stype == 'line':
        color = item.get('color', BLACK)
        points = item['points']
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, th)

    elif stype == 'eraser':
        points = item['points']
        if len(points) > 1:
            pygame.draw.lines(surface, WHITE, False, points, th)

def redraw_all():
    final_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT), pygame.SRCALPHA)
    for layer in layers:
        if not layer.visible:
            continue
        layer_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT), pygame.SRCALPHA)
        if layer.background_color is not None:
            layer_surf.fill(layer.background_color)
        for shape in layer.shapes:
            draw_shape_item(layer_surf, shape)
        final_surface.blit(layer_surf, (0, 0))
    return final_surface

# ========== FÁJL MENTÉS / BETÖLTÉS ==========

def save_canvas(filename="multi_layer.png"):
    final_surf = redraw_all()
    pygame.image.save(final_surf, filename)
    print(f"Mentve: {filename}")

def load_canvas(filename="multi_layer.png"):
    if os.path.exists(filename):
        loaded = pygame.image.load(filename)
        base_layer = layers[0]
        base_layer.shapes.clear()
        base_layer.background_color = None
        base_layer.shapes.append({'type': 'loaded_image', 'surface': loaded})
        print(f"Betöltve: {filename}")
    else:
        print("Nincs ilyen fájl.")

# ========== GOMB, CSÚSZKA, SZÍN SWATCH OSZTÁLYOK ==========

class Button:
    def __init__(self, text, callback, tooltip=None, w=100, h=30):
        self.text = text
        self.callback = callback
        self.tooltip = tooltip
        self.w = w
        self.h = h
        self.rect = pygame.Rect(0, 0, w, h)

        self.font = pygame.font.SysFont(None, 18)
        self.bg_color = GRAY
        self.hover_color = DARK_GRAY
        self.text_color = BLACK

    def set_position(self, x, y):
        self.rect.topleft = (x, y)

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        color = self.bg_color
        if self.rect.collidepoint(mouse_pos):
            color = self.hover_color
            if self.tooltip:
                show_tooltip(self.tooltip, mouse_pos)

        pygame.draw.rect(surf, color, self.rect, border_radius=4)
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class ColorSwatch:
    def __init__(self, color, set_bg=False, tooltip=None, size=32):
        self.color = color
        self.set_bg = set_bg
        self.tooltip = tooltip
        self.size = size
        self.rect = pygame.Rect(0, 0, size, size)

    def set_position(self, x, y):
        self.rect.topleft = (x, y)

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.rect(surf, self.color, self.rect)
        pygame.draw.rect(surf, BLACK, self.rect, 2)

        if self.tooltip and self.rect.collidepoint(mouse_pos):
            show_tooltip(self.tooltip, mouse_pos)

    def handle_event(self, event):
        global current_color
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.set_bg:
                    set_layer_background_color(self.color)
                else:
                    current_color = self.color
                    print(f"Szín beállítva: {current_color}")

class Slider:
    def __init__(self, min_val=1, max_val=20, start_val=3, tooltip=None, w=150, h=20):
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.tooltip = tooltip
        self.w = w
        self.h = h
        self.rect = pygame.Rect(0, 0, w, h)
        self.handle_width = 12
        self.dragging = False
        self.update_handle_x()

    def set_position(self, x, y):
        self.rect.topleft = (x, y)
        self.update_handle_x()

    def update_handle_x(self):
        ratio = (self.value - self.min_val) / float(self.max_val - self.min_val)
        self.handle_x = self.rect.x + int(ratio * (self.rect.w - self.handle_width))

    def value_from_x(self, x_pos):
        rel = x_pos - self.rect.x
        ratio = rel / float(self.rect.w - self.handle_width)
        val = self.min_val + ratio * (self.max_val - self.min_val)
        return int(round(max(self.min_val, min(self.max_val, val))))

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.rect(surf, DARK_GRAY, self.rect)
        handle_rect = pygame.Rect(self.handle_x, self.rect.y, self.handle_width, self.h)
        pygame.draw.rect(surf, GRAY, handle_rect)

        font = pygame.font.SysFont(None, 18)
        val_surf = font.render(str(self.value), True, BLACK)
        val_rect = val_surf.get_rect(midbottom=(handle_rect.centerx, self.rect.y - 2))
        surf.blit(val_surf, val_rect)

        if self.tooltip and self.rect.collidepoint(mouse_pos):
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

tooltip_text = None
tooltip_pos = None

def show_tooltip(text, pos):
    global tooltip_text, tooltip_pos
    tooltip_text = text
    tooltip_pos = pos

def draw_tooltip(surf):
    global tooltip_text, tooltip_pos
    if tooltip_text and tooltip_pos:
        font = pygame.font.SysFont(None, 20)
        t_surf = font.render(tooltip_text, True, (50, 50, 50))
        pad = 5
        bg_rect = t_surf.get_rect()
        bg_rect.topleft = (tooltip_pos[0] + 10, tooltip_pos[1] + 10)
        bg_rect.inflate_ip(pad*2, pad*2)

        pygame.draw.rect(surf, (255, 255, 210), bg_rect)
        pygame.draw.rect(surf, BLACK, bg_rect, 1)
        surf.blit(t_surf, (bg_rect.x+pad, bg_rect.y+pad))

    tooltip_text = None
    tooltip_pos = None

# ========== SÚGÓ / HELP ==========

show_help = False

def toggle_help():
    global show_help
    show_help = not show_help

def draw_help_overlay(surf):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    font = pygame.font.SysFont(None, 26)
    lines = [
        "PaintMEZ - Többrétegű Rajzprogram, Egyéni Szín megadás",
        "",
        "Eszközök, több sorba rendezett gombok fent.",
        "Rétegek: Új, Köv/Előző, Törlés, Undo/Redo rétegenként.",
        "Háttérszín: 'Set BG' swatch-okkal vagy egyéni színnel állítható.",
        "Beépített paletta + 'Egyéni szín' gomb, ami HEX vagy RGB bevitelt is elfogad.",
        "",
        "Mentés / Betöltés: pixelképet. A réteges adatok JSON-ban nincsenek mentve.",
        "",
        "Kattints a HELP gombra újra, hogy bezárd."
    ]
    y = 100
    for line in lines:
        s = font.render(line, True, WHITE)
        r = s.get_rect(center=(SCREEN_WIDTH//2, y))
        overlay.blit(s, r)
        y += 40
    surf.blit(overlay, (0, 0))

# ========== EGYÉNI SZÍN BEVITEL (RGB/HEX) ==========

custom_color_overlay = False
color_input_text = ""    # A felhasználó által beírt szöveg
color_error_message = "" # Ha parsing közben hiba adódik

def toggle_custom_color():
    global custom_color_overlay, color_input_text, color_error_message
    custom_color_overlay = not custom_color_overlay
    color_input_text = ""
    color_error_message = ""

def parse_color_string(text):
    """
    Elfogadja pl.:
    - "255, 128, 64"
    - "255 128 64"
    - "#FFAABB"
    - "FFAABB"
    Visszaad egy (R, G, B) tuple-t vagy hibát dob.
    """
    text = text.strip()
    # Hex forma (#123456 vagy 123456)
    if text.startswith("#"):
        text = text[1:].strip()
    # Most, ha 6 hosszú hex maradt, megpróbáljuk parse-olni
    if len(text) == 6 and all(c in "0123456789ABCDEFabcdef" for c in text):
        r = int(text[0:2], 16)
        g = int(text[2:4], 16)
        b = int(text[4:6], 16)
        return (r, g, b)

    # Egyébként RGB formátum, pl. "255,128,64" vagy "255 128 64"
    # Szétbontjuk vessző vagy szóköz alapján.
    import re
    parts = re.split(r'[,\s]+', text)
    if len(parts) == 3:
        try:
            r = int(parts[0])
            g = int(parts[1])
            b = int(parts[2])
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return (r, g, b)
            else:
                raise ValueError("Az RGB értékeknek 0..255 között kell lenniük.")
        except ValueError as e:
            raise ValueError("Hibás számforma az RGB-n belül. (pl. 255,0,128)")

    raise ValueError("Nem sikerült értelmezni a színt (HEX vagy RGB formátum).")

def draw_custom_color_overlay(surface):
    """
    Egy kis ablak, ahol megjelenik:
    - "Egyéni szín beírása (RGB vagy HEX):"
    - A beviteli mező (color_input_text)
    - Ok gomb, Mégse gomb, esetleg hibajelzés
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))

    # Kis téglalap középen
    box_width = 400
    box_height = 200
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = (SCREEN_HEIGHT - box_height) // 2

    pygame.draw.rect(overlay, (230, 230, 230), (box_x, box_y, box_width, box_height), border_radius=8)
    pygame.draw.rect(overlay, BLACK, (box_x, box_y, box_width, box_height), 2, border_radius=8)

    font = pygame.font.SysFont(None, 24)
    title_surf = font.render("Egyéni szín beírása (RGB vagy HEX):", True, BLACK)
    title_rect = title_surf.get_rect(midtop=(box_x + box_width//2, box_y + 10))
    overlay.blit(title_surf, title_rect)

    # Beviteli mező
    input_rect = pygame.Rect(box_x + 30, box_y + 60, box_width - 60, 30)
    pygame.draw.rect(overlay, WHITE, input_rect, border_radius=5)
    pygame.draw.rect(overlay, BLACK, input_rect, 2, border_radius=5)

    text_surf = font.render(color_input_text, True, (0, 0, 128))
    text_rect = text_surf.get_rect(midleft=(input_rect.x + 5, input_rect.y + input_rect.h//2))
    overlay.blit(text_surf, text_rect)

    # OK és Mégse gomb
    ok_rect = pygame.Rect(box_x + 60, box_y + 120, 100, 30)
    cancel_rect = pygame.Rect(box_x + 240, box_y + 120, 100, 30)

    pygame.draw.rect(overlay, (180, 255, 180), ok_rect, border_radius=5)
    pygame.draw.rect(overlay, BLACK, ok_rect, 2, border_radius=5)
    ok_surf = font.render("OK", True, BLACK)
    ok_rect_text = ok_surf.get_rect(center=ok_rect.center)
    overlay.blit(ok_surf, ok_rect_text)

    pygame.draw.rect(overlay, (255, 180, 180), cancel_rect, border_radius=5)
    pygame.draw.rect(overlay, BLACK, cancel_rect, 2, border_radius=5)
    cancel_surf = font.render("Mégse", True, BLACK)
    cancel_rect_text = cancel_surf.get_rect(center=cancel_rect.center)
    overlay.blit(cancel_surf, cancel_rect_text)

    # Hibaüzenet, ha van
    if color_error_message:
        error_surf = font.render(color_error_message, True, (200, 0, 0))
        error_rect = error_surf.get_rect(midtop=(box_x + box_width//2, box_y + 100))
        overlay.blit(error_surf, error_rect)

    surface.blit(overlay, (0, 0))

# ========== FŐ GOMBOK, SWATCHOK, SLIDER LÉTREHOZÁSA ==========

buttons = []
color_swatches = []
bg_color_swatches = []
slider = None

def set_tool_rect():
    global current_tool
    current_tool = 'rect'

def set_tool_ellipse():
    global current_tool
    current_tool = 'ellipse'

def set_tool_line():
    global current_tool
    current_tool = 'line'

def set_tool_eraser():
    global current_tool
    current_tool = 'eraser'

def toggle_fill():
    global fill_shapes
    fill_shapes = not fill_shapes

def undo_cb():
    layer_undo()

def redo_cb():
    layer_redo()

def clear_cb():
    clear_current_layer()

def save_cb():
    save_canvas("multi_layer.png")

def load_cb():
    load_canvas("multi_layer.png")

def exit_program():
    pygame.quit()
    sys.exit()

def create_ui():
    global slider

    # Fő gombok
    button_data = [
        ("Téglalap", set_tool_rect, "Téglalap rajzolás"),
        ("Ellipszis", set_tool_ellipse, "Ellipszis rajzolás"),
        ("Szabadkézi", set_tool_line, "Szabadkézi vonal"),
        ("Radír", set_tool_eraser, "Radírozás"),
        ("Kitöltés", toggle_fill, "Kitöltött/körvonal"),
        ("Undo", undo_cb, "Visszavonás (aktuális réteg)"),
        ("Redo", redo_cb, "Újra (aktuális réteg)"),
        ("Törlés", clear_cb, "Aktuális réteg törlése"),
        ("Mentés", save_cb, "Kép mentése"),
        ("Betöltés", load_cb, "Kép betöltése"),
        ("Help", toggle_help, "Súgó"),
        ("Kilépés", exit_program, "Kilépés"),
        ("Köv. réteg", next_layer, "Következő réteg"),
        ("Előző réteg", previous_layer, "Előző réteg"),
        ("Új réteg", add_layer, "Új réteg"),
        ("Réteg törlés", remove_layer, "Aktuális réteg törlése"),
        # ÚJ: Egyéni szín beállítás gomb
        ("Egyéni szín", toggle_custom_color, "Megadhatsz RGB vagy Hex kódot"),
    ]

    for (txt, cb, tip) in button_data:
        btn = Button(txt, cb, tip)
        buttons.append(btn)

    # Swatchok
    for c in DEFAULT_PALETTE:
        sw = ColorSwatch(c, set_bg=False, tooltip=f"Szín: {c}")
        color_swatches.append(sw)

    for c in DEFAULT_PALETTE:
        sw = ColorSwatch(c, set_bg=True, tooltip=f"Set BG: {c}")
        bg_color_swatches.append(sw)

    slider = Slider(min_val=1, max_val=30, start_val=3, tooltip="Ecset/radír vastagság")
    return slider

slider = create_ui()

def layout_buttons_in_rows():
    x = 200
    y = 10
    spacing = 10
    row_height = 40
    max_width = SCREEN_WIDTH - 10

    # Gombok több sorban
    for btn in buttons:
        w = btn.w
        h = btn.h
        if x + w + spacing > max_width:
            x = 200
            y += row_height + spacing
        btn.set_position(x, y)
        x += w + spacing

    x = 200
    y += row_height + spacing
    # Szín swatch
    for sw in color_swatches:
        size = sw.size
        if x + size + spacing > max_width:
            x = 200
            y += size + spacing
        sw.set_position(x, y)
        x += size + spacing

    x += 30
    for sw in bg_color_swatches:
        size = sw.size
        if x + size + spacing > max_width:
            x = 200
            y += size + spacing
        sw.set_position(x, y)
        x += size + spacing

    x += 20
    slider.set_position(x, y+5)

# ========== LOGÓ ==========

def draw_logo(surface):
    font = pygame.font.SysFont(None, 48, bold=True)
    text = "PaintMEZ"
    text_surf = font.render(text, True, LOGO_COLOR)
    text_rect = text_surf.get_rect(topleft=(10, 10))
    surface.blit(text_surf, text_rect)

# ========== FŐ CIKLUS ==========

running = True
layout_buttons_in_rows()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Ha az egyéni szín overlay aktív, először azt kezeljük
        if custom_color_overlay:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # OK -> próbáljuk parse-olni
                    try:
                        col = parse_color_string(color_input_text)
                        current_color = col
                        print(f"Egyéni szín beállítva: {current_color}")
                        toggle_custom_color()  # Bezárjuk az overlayt
                    except ValueError as e:
                        color_error_message = str(e)
                    # Ha hiba, akkor color_error_message-ben jelezzük
                elif event.key == pygame.K_ESCAPE:
                    toggle_custom_color()  # Mégse
                elif event.key == pygame.K_BACKSPACE:
                    if len(color_input_text) > 0:
                        color_input_text = color_input_text[:-1]
                else:
                    # Szöveges karaktert fűzünk hozzá
                    # Korlátozzuk a max hosszát, pl. 20
                    if len(color_input_text) < 20:
                        color_input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Nézzük, rákattintott-e az OK / Mégse gombra
                # Ehhez a draw_custom_color_overlay-ből emlékszünk a rect-jeikre:
                box_width = 400
                box_height = 200
                box_x = (SCREEN_WIDTH - box_width) // 2
                box_y = (SCREEN_HEIGHT - box_height) // 2
                ok_rect = pygame.Rect(box_x + 60, box_y + 120, 100, 30)
                cancel_rect = pygame.Rect(box_x + 240, box_y + 120, 100, 30)

                if ok_rect.collidepoint(event.pos):
                    # OK gomb
                    try:
                        col = parse_color_string(color_input_text)
                        current_color = col
                        print(f"Egyéni szín beállítva: {current_color}")
                        toggle_custom_color()
                    except ValueError as e:
                        color_error_message = str(e)

                elif cancel_rect.collidepoint(event.pos):
                    # Mégse
                    toggle_custom_color()

            # Ha overlay aktív, nem kezeljük a többi gombot, rajzot, stb.
            continue

        # Normál eseménykezelés (gombok, csúszka, swatchok, rajz)
        for b in buttons:
            b.handle_event(event)
        for sw in color_swatches:
            sw.handle_event(event)
        for sw in bg_color_swatches:
            sw.handle_event(event)
        slider.handle_event(event)

        # Rajzterület
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[1] > UI_HEIGHT:
                mouse_is_down = True
                layer = get_current_layer()
                layer.redo_stack.clear()

                if current_tool in ('rect', 'ellipse'):
                    start_pos = (event.pos[0], event.pos[1] - UI_HEIGHT)
                elif current_tool in ('line', 'eraser'):
                    line_points = [(event.pos[0], event.pos[1] - UI_HEIGHT)]

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if mouse_is_down:
                mouse_is_down = False
                layer = get_current_layer()
                if current_tool in ('rect', 'ellipse'):
                    end_pos = (event.pos[0], event.pos[1] - UI_HEIGHT)
                    shape_data = create_shape_data(current_tool, start=start_pos, end=end_pos)
                    layer.shapes.append(shape_data)
                elif current_tool in ('line', 'eraser'):
                    if len(line_points) > 1:
                        shape_data = create_shape_data(current_tool, points=line_points)
                        layer.shapes.append(shape_data)
                line_points = []

        elif event.type == pygame.MOUSEMOTION:
            if mouse_is_down and event.pos[1] > UI_HEIGHT:
                if current_tool in ('line', 'eraser'):
                    line_points.append((event.pos[0], event.pos[1] - UI_HEIGHT))
                    final_surf = redraw_all()
                    if len(line_points) > 1:
                        if current_tool == 'line':
                            pygame.draw.line(final_surf, current_color,
                                             line_points[-2], line_points[-1], brush_thickness)
                        else:
                            pygame.draw.line(final_surf, WHITE,
                                             line_points[-2], line_points[-1], brush_thickness)
                    # Képernyő frissítés
                    screen.fill(LIGHT_GRAY, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
                    draw_logo(screen)
                    for b in buttons:
                        b.draw(screen)
                    for sw in color_swatches:
                        sw.draw(screen)
                    for sw in bg_color_swatches:
                        sw.draw(screen)
                    slider.draw(screen)

                    screen.blit(final_surf, (0, UI_HEIGHT))
                    if show_help:
                        draw_help_overlay(screen)
                    draw_tooltip(screen)
                    pygame.display.flip()

    # ========== Minden frame kirajzolása ==========

    final_surf = redraw_all()

    # Felső UI sáv
    screen.fill(LIGHT_GRAY, (0, 0, SCREEN_WIDTH, UI_HEIGHT))

    # Logó
    draw_logo(screen)

    # Gombok, swatchok, slider
    for b in buttons:
        b.draw(screen)
    for sw in color_swatches:
        sw.draw(screen)
    for sw in bg_color_swatches:
        sw.draw(screen)
    slider.draw(screen)

    # Rétegek
    screen.blit(final_surf, (0, UI_HEIGHT))

    # Előnézet téglalap / ellipszis
    if mouse_is_down and current_tool in ('rect', 'ellipse'):
        mx, my = pygame.mouse.get_pos()
        if my > UI_HEIGHT:
            preview_surf = final_surf.copy()
            end_pos = (mx, my - UI_HEIGHT)
            shape_data = create_shape_data(current_tool, start=start_pos, end=end_pos)
            draw_shape_item(preview_surf, shape_data)
            screen.blit(preview_surf, (0, UI_HEIGHT))

    # Help overlay
    if show_help:
        draw_help_overlay(screen)

    # Ha custom_color_overlay aktív, rárajzoljuk azt is
    if custom_color_overlay:
        draw_custom_color_overlay(screen)

    # Tooltip
    draw_tooltip(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
