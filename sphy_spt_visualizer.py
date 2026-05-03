import py5
import pandas as pd
import numpy as np
import hashlib

# Configurações de exibição
grid_res = 30
grid_size = 1200
sphere_radius = 150
sphere_res = 15

# Globais de controle
df = None
current_f = 0
cam_rot_x, cam_rot_z = 0.8, 0.5
cam_zoom, offset_x, offset_y = -200, 0, 0
sphere_vertices = []

def generate_sha256(data_string):
    return hashlib.sha256(data_string.encode()).hexdigest()

def settings():
    py5.size(1000, 800, py5.P3D)

def setup():
    global df, sphere_vertices
    py5.window_resizable(True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Carregar Dados
    try:
        df = pd.read_parquet("espaco_tempo_dataset.parquet")
    except:
        print("Erro: Execute o gerador primeiro!")
        py5.exit_sketch()

    # Pré-gerar esfera wireframe
    for i in range(sphere_res + 1):
        lat = py5.remap(i, 0, sphere_res, -py5.HALF_PI, py5.HALF_PI)
        for j in range(sphere_res + 1):
            lon = py5.remap(j, 0, sphere_res, -py5.PI, py5.PI)
            vx = sphere_radius * py5.cos(lat) * py5.cos(lon)
            vy = sphere_radius * py5.sin(lat)
            vz = sphere_radius * py5.cos(lat) * py5.sin(lon)
            sphere_vertices.append(np.array([vx, vy, vz]))

def draw():
    global current_f, cam_rot_x, cam_rot_z, cam_zoom, offset_x, offset_y
    py5.background(0, 0, 3)
    
    # Validação de Hash
    row = df.iloc[current_f]
    state_to_check = {
        'frame': row['frame'],
        'sphere_x': row['sphere_x'],
        'sphere_y': row['sphere_y'],
        'mass_z': row['mass_z'],
        'angle': row['angle']
    }
    check_hash = generate_sha256(str(state_to_check) + row['prev_hash'])
    
    # Interface de Câmera
    py5.translate(py5.width/2 + offset_x, py5.height/2 + offset_y, cam_zoom)
    py5.rotate_x(cam_rot_x)
    py5.rotate_z(cam_rot_z)

    if check_hash != row['sha256']:
        render_corruption_alert()
    else:
        render_spacetime(row)

    current_f = (current_f + 1) % len(df)
    render_hud(row['sha256'], current_f)

def render_spacetime(row):
    tx, ty, mz = row['sphere_x'], row['sphere_y'], row['mass_z']
    
    # Desenhar Grid Curvado
    py5.no_fill()
    py5.stroke_weight(1)
    
    for i in range(grid_res + 1):
        x = py5.remap(i, 0, grid_res, -grid_size/2, grid_size/2)
        py5.begin_shape()
        for j in range(grid_res + 1):
            y = py5.remap(j, 0, grid_res, -grid_size/2, grid_size/2)
            d = py5.dist(x, y, tx, ty)
            z = -py5.remap(d, 0, 400, mz, 0) if d < 400 else 0
            
            py5.stroke(200, 70, 100, 50)
            py5.vertex(x, y, z)
        py5.end_shape()

    # Desenhar Esfera de Einstein
    py5.push_matrix()
    py5.translate(tx, ty, -mz + 50)
    py5.rotate_z(row['angle'])
    py5.stroke(45, 90, 100, 90) # Dourado Deterministico
    for i in range(sphere_res):
        py5.begin_shape(py5.LINES)
        for j in range(sphere_res):
            v = sphere_vertices[i * (sphere_res+1) + j]
            py5.vertex(v[0], v[1], v[2])
            v_n = sphere_vertices[i * (sphere_res+1) + j + 1]
            py5.vertex(v_n[0], v_n[1], v_n[2])
        py5.end_shape()
    py5.pop_matrix()

def render_hud(h, f):
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.reset_matrix()
    py5.fill(0, 0, 100)
    py5.text(f"FRAME: {f} | SPT-HASH: {h[:24]}...", 20, 30)
    py5.hint(py5.ENABLE_DEPTH_TEST)

def render_corruption_alert():
    py5.fill(0, 100, 100)
    py5.text("REALITY CORRUPTION: SHA-256 MISMATCH", 0, 0)

def mouse_dragged():
    global cam_rot_x, cam_rot_z, offset_x, offset_y
    if py5.mouse_button == py5.LEFT:
        cam_rot_z += (py5.mouse_x - py5.pmouse_x) * 0.01
        cam_rot_x += (py5.mouse_y - py5.pmouse_y) * 0.01
    else:
        offset_x += (py5.mouse_x - py5.pmouse_x)
        offset_y += (py5.mouse_y - py5.pmouse_y)

def mouse_wheel(event):
    global cam_zoom
    cam_zoom -= event.get_count() * 30

if __name__ == "__main__":
    py5.run_sketch()
