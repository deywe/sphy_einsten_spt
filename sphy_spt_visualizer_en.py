import py5
import pandas as pd
import numpy as np
import hashlib

# --- Simulation Constants ---
GRID_RES = 30
GRID_SIZE = 1200
SPHERE_RADIUS = 150
SPHERE_RES = 15

# --- Global State ---
df = None
total_frames = 0
current_frame_idx = 0
sphere_vertices = []

# --- Camera & Navigation ---
cam_rot_x, cam_rot_z = 0.8, 0.5
cam_zoom = -300
offset_x, offset_y = 0, 0
is_corrupted = False

def generate_sha256(data_string):
    """Generates a SHA-256 signature for data integrity."""
    return hashlib.sha256(data_string.encode()).hexdigest()

def settings():
    py5.size(1000, 800, py5.P3D)

def setup():
    global df, total_frames, sphere_vertices
    py5.window_resizable(True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.text_font(py5.create_font("SansSerif", 14))
    
    # 1. Load the Parquet "Truth" File
    try:
        df = pd.read_parquet("espaco_tempo_dataset.parquet")
        total_frames = len(df)
        print(f"Dataset Loaded: {total_frames} frames found.")
    except Exception as e:
        print(f"Critical Error: Could not find 'espaco_tempo_dataset.parquet'. Run the generator first!")
        py5.exit_sketch()

    # 2. Pre-calculate Wireframe Sphere
    for i in range(SPHERE_RES + 1):
        lat = py5.remap(i, 0, SPHERE_RES, -py5.HALF_PI, py5.HALF_PI)
        for j in range(SPHERE_RES + 1):
            lon = py5.remap(j, 0, SPHERE_RES, -py5.PI, py5.PI)
            vx = SPHERE_RADIUS * py5.cos(lat) * py5.cos(lon)
            vy = SPHERE_RADIUS * py5.sin(lat)
            vz = SPHERE_RADIUS * py5.cos(lat) * py5.sin(lon)
            sphere_vertices.append(np.array([vx, vy, vz]))

def draw():
    global current_frame_idx, cam_rot_x, cam_rot_z, cam_zoom, offset_x, offset_y, is_corrupted
    py5.background(0, 0, 5) # Dark space
    
    if df is None: return

    # --- REAL-TIME VALIDATION ---
    row = df.iloc[current_frame_idx]
    
    # Reconstruct the state exactly as it was hashed in the generator
    current_state = {
        'frame': int(row['frame']),
        'sphere_x': float(row['sphere_x']),
        'sphere_y': float(row['sphere_y']),
        'mass_z': float(row['mass_z']),
        'angle': float(row['angle'])
    }
    
    # Re-calculate hash using the stored 'prev_hash'
    computed_hash = generate_sha256(str(current_state) + row['prev_hash'])
    stored_hash = row['sha256']
    
    # Check for Reality Corruption
    is_corrupted = (computed_hash != stored_hash)

    # --- 3D RENDERING ---
    py5.push_matrix()
    
    # Apply Camera/View Matrix
    py5.translate(py5.width/2 + offset_x, py5.height/2 + offset_y, cam_zoom)
    py5.rotate_x(cam_rot_x)
    py5.rotate_z(cam_rot_z)

    if is_corrupted:
        render_corruption_glitch()
    else:
        render_spacetime_grid(row)
        render_truth_sphere(row)

    py5.pop_matrix()

    # --- HUD & METRICS ---
    render_hud(stored_hash, computed_hash)

    # Loop frames
    current_frame_idx = (current_frame_idx + 1) % total_frames

def render_spacetime_grid(row):
    """Renders the Einsteinian Spacetime Fabric."""
    tx, ty, mz = row['sphere_x'], row['sphere_y'], row['mass_z']
    py5.no_fill()
    py5.stroke_weight(1)
    
    # Grid lines along X
    for i in range(GRID_RES + 1):
        x = py5.remap(i, 0, GRID_RES, -GRID_SIZE/2, GRID_SIZE/2)
        py5.begin_shape()
        for j in range(GRID_RES + 1):
            y = py5.remap(j, 0, GRID_RES, -GRID_SIZE/2, GRID_SIZE/2)
            d = py5.dist(x, y, tx, ty)
            # Apply Curvature Depth (Z)
            z = -py5.remap(d, 0, 400, mz, 0) if d < 400 else 0
            
            # Dynamic Hue: Blue (Normal) -> Cyan (Curved)
            hue = py5.remap(z, -250, 0, 180, 210)
            py5.stroke(hue, 80, 100, 60)
            py5.vertex(x, y, z)
        py5.end_shape()

def render_truth_sphere(row):
    """Renders the Core Sphere (The Being/Truth)."""
    py5.push_matrix()
    py5.translate(row['sphere_x'], row['sphere_y'], -row['mass_z'] + 50)
    py5.rotate_z(row['angle'])
    
    py5.stroke(45, 90, 100, 100) # Golden/Amber Glow
    for i in range(SPHERE_RES):
        py5.begin_shape(py5.LINES)
        for j in range(SPHERE_RES + 1):
            idx = i * (SPHERE_RES + 1) + j
            v = sphere_vertices[idx]
            py5.vertex(v[0], v[1], v[2])
            
            # Connect to next latitudinal point
            if j < SPHERE_RES:
                v_next = sphere_vertices[idx + 1]
                py5.vertex(v_next[0], v_next[1], v_next[2])
        py5.end_shape()
    py5.pop_matrix()

def render_corruption_glitch():
    """Visual feedback for hash mismatch."""
    py5.stroke(0, 100, 100) # Bright Red
    py5.stroke_weight(2)
    for _ in range(20):
        py5.line(py5.random(-500, 500), py5.random(-500, 500), py5.random(-100, 100),
                 py5.random(-500, 500), py5.random(-500, 500), py5.random(-100, 100))

def render_hud(stored, computed):
    """Heads-Up Display for auditing the reality state."""
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.reset_matrix()
    
    # Background bar
    py5.no_stroke()
    py5.fill(0, 0, 0, 180)
    py5.rect(0, 0, py5.width, 100)
    
    # Status Text
    py5.fill(0, 0, 100)
    py5.text(f"FRAME: {current_frame_idx} / {total_frames}", 20, 30)
    py5.text(f"STORED HASH:   {stored}", 20, 55)
    
    if is_corrupted:
        py5.fill(0, 100, 100)
        py5.text(f"COMPUTED HASH: {computed} [INVALID]", 20, 80)
        py5.text("REALITY CORRUPTION DETECTED: UNCERTAINTY INJECTED", py5.width - 400, 30)
    else:
        py5.fill(120, 100, 100)
        py5.text(f"COMPUTED HASH: {computed} [VALID]", 20, 80)
        py5.text("REALITY VERIFIED: NO DATA LEAKAGE", py5.width - 300, 30)
        
    py5.hint(py5.ENABLE_DEPTH_TEST)

# --- Interactive Controls ---

def mouse_dragged():
    global cam_rot_x, cam_rot_z, offset_x, offset_y
    if py5.mouse_button == py5.LEFT:
        cam_rot_z += (py5.mouse_x - py5.pmouse_x) * 0.01
        cam_rot_x += (py5.mouse_y - py5.pmouse_y) * 0.01
    elif py5.mouse_button == py5.RIGHT or py5.mouse_button == py5.CENTER:
        offset_x += (py5.mouse_x - py5.pmouse_x)
        offset_y += (py5.mouse_y - py5.pmouse_y)

def mouse_wheel(event):
    global cam_zoom
    cam_zoom -= event.get_count() * 30

if __name__ == "__main__":
    py5.run_sketch()
