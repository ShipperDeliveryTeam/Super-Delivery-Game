import sys

with open('src/core/game_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if 'self.ui_background = self._load_ui_image("phongnen.png", (SCREEN_WIDTH, SCREEN_HEIGHT))' in line and i > 580:
        continue
    if 'self.ui_logo = self._load_ui_image("logo.png", (560, 230))' in line:
        continue
    if 'self.ui_shipper = self._load_ui_image("shipper.png", (210, 150))' in line:
        continue
    
    # logo replace
    if 'logo_rect.y = 55' in line:
        line = line.replace('55', '15')
    
    # shipper replace
    if 'shipper_w = 620' in line:
        line = line.replace('shipper_w = 620', 'img_w, img_h = self.ui_shipper.get_size()')
    elif 'shipper_h = 430' in line:
        line = line.replace('shipper_h = 430', 'target_h = 430\n            target_w = int(img_w * (target_h / img_h)) if img_h > 0 else 620')
    elif 'shipper = pygame.transform.smoothscale(self.ui_shipper, (shipper_w, shipper_h))' in line:
        line = line.replace('shipper_w, shipper_h', 'target_w, target_h')

    new_lines.append(line)

with open('src/core/game_manager.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
