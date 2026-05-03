import py5
import pandas as pd
import numpy as np
import hashlib
from collections import deque

# --- Simulation Constants ---
GRID_RES = 30
GRID_SIZE = 1200
SPHERE_RADIUS = 140

# --- Global State ---
df = None
total_frames = 0
current_frame_idx = 0
validation_log = deque(maxlen=8)
cam_rot_x, cam_rot_z = 0.8, 0.5
cam_zoom = -500
is_corrupted = False

def generate_sha256(data_string):
    return hashlib.sha256(data_string.encode()).hexdigest()

def settings():
    py5.size(1200, 900, py5.P3D)

def setup():
    global df, total_frames
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    try:
        df = pd.read_parquet("espaco_tempo_dataset.parquet")
        total_frames = len(df)
    except:
        print("Erro: Arquivo Parquet não encontrado.")
        py5.exit_sketch()

def draw():
    global current_frame_idx, cam_rot_x, cam_rot_z, is_corrupted
    py5.background(0, 0, 3) 
    
    if df is None: return

    # --- 1. LOGIC & VALIDATION ---
    row = df.iloc[current_frame_idx]
    current_state = {
        'frame': int(row['frame']),
        'sphere_x': float(row['sphere_x']),
        'sphere_y': float(row['sphere_y']),
        'mass_z': float(row['mass_z']),
        'angle': float(row['angle'])
    }
    computed_hash = generate_sha256(str(current_state) + row['prev_hash'])
    is_corrupted = (computed_hash != row['sha256'])
    
    if py5.frame_count % 3 == 0:
        status = "OK" if not is_corrupted else "FAIL"
        validation_log.append(f"FRM {current_frame_idx:04d}: {computed_hash[:16]}... {status}")

    # --- 2. RENDER 3D WORLD ---
    py5.push_matrix()
    # Centralização absoluta baseada na largura/altura atual
    py5.translate(py5.width/2, py5.height/2 + 50, cam_zoom)
    py5.rotate_x(cam_rot_x)
    py5.rotate_z(cam_rot_z)
    
    render_grid(row)
    render_sphere(row)
    py5.pop_matrix()

    # --- 3. RENDER TECHNICAL FRAME (HUD) ---
    draw_technical_interface(computed_hash)

    current_frame_idx = (current_frame_idx + 1) % total_frames

def draw_technical_interface(current_hash):
    """Cria uma moldura técnica isolada com título centralizado."""
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.reset_matrix()
    
    # --- Frame Superior (HUD) ---
    py5.no_stroke()
    py5.fill(0, 0, 0, 255)
    py5.rect(0, 0, py5.width, 110)
    
    # Linha de separação tecnológica
    py5.stroke(180, 100, 100)
    py5.stroke_weight(2)
    py5.line(0, 110, py5.width, 110)
    
    # --- Título Centralizado ---
    py5.text_align(py5.CENTER) # Alinhamento ao centro
    py5.fill(45, 80, 100)      # Dourado SPHY
    py5.text_size(26)
    py5.text("SPHY - EINSTEIN OKABE SIMBIOTIC FRAMEWORK", py5.width / 2, 45)
    
    # --- Status e Validação (Abaixo do título, também centralizado) ---
    py5.text_size(14)
    if is_corrupted:
        py5.fill(0, 100, 100) # Alerta Vermelho
        status_txt = f"⚠️ INTEGRITY FAILURE AT FRAME {current_frame_idx} ⚠️"
    else:
        py5.fill(130, 100, 100) # Verde Simbiótico
        status_txt = f"FRAME: {current_frame_idx}/{total_frames} | SHA256: VALIDATED"
    
    py5.text(status_txt, py5.width / 2, 75)
    
    # --- Monitor de Hash (Texto menor no rodapé do frame superior) ---
    py5.fill(0, 0, 70)
    py5.text_size(11)
    py5.text(f"CURRENT SIGNATURE: {current_hash}", py5.width / 2, 98)

    # --- Log Lateral (Mantido no canto para não poluir o centro) ---
    py5.text_align(py5.LEFT) # Volta o alinhamento para o log
    py5.fill(0, 0, 0, 150)
    py5.rect(20, py5.height - 180, 350, 160, 5)
    py5.fill(0, 0, 100)
    py5.text("CONTINUOUS AUDIT LOG:", 35, py5.height - 155)
    
    py5.text_size(10)
    for i, log in enumerate(validation_log):
        py5.text(log, 35, py5.height - 135 + (i * 15))
        
    py5.hint(py5.ENABLE_DEPTH_TEST)
def render_grid(row):
    tx, ty, mz = row['sphere_x'], row['sphere_y'], row['mass_z']
    py5.no_fill()
    py5.stroke_weight(1)
    for i in range(GRID_RES + 1):
        x = py5.remap(i, 0, GRID_RES, -GRID_SIZE/2, GRID_SIZE/2)
        py5.begin_shape()
        for j in range(GRID_RES + 1):
            y = py5.remap(j, 0, GRID_RES, -GRID_SIZE/2, GRID_SIZE/2)
            d = py5.dist(x, y, tx, ty)
            z = -py5.remap(d, 0, 400, mz, 0) if d < 400 else 0
            py5.stroke(190, 80, 100, 40)
            py5.vertex(x, y, z)
        py5.end_shape()

def render_sphere(row):
    py5.push_matrix()
    py5.translate(row['sphere_x'], row['sphere_y'], -row['mass_z'] + 50)
    py5.rotate_z(row['angle'])
    py5.stroke(45, 90, 100, 100)
    py5.no_fill()
    py5.sphere_detail(15)
    py5.sphere(SPHERE_RADIUS)
    py5.pop_matrix()

def mouse_dragged():
    global cam_rot_x, cam_rot_z
    cam_rot_z += (py5.mouse_x - py5.pmouse_x) * 0.01
    cam_rot_x += (py5.mouse_y - py5.pmouse_y) * 0.01

if __name__ == "__main__":
    py5.run_sketch()
