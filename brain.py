"""
sdf_brick_engine.py — Template-Free 3D SDF Sculpting & Greedy Brick Mesher
Replaces brain.py's hardcoded builders with continuous 3D volume sculpting + brick merging.
"""
import math

# --- 1. Continuous 3D SDF Primitives & Booleans ---
def sdf_sphere(p, c, r):
    return math.dist(p, c) - r

def sdf_capsule(p, a, b, r):
    pax, pay, paz = p[0]-a[0], p[1]-a[1], p[2]-a[2]
    bax, bay, baz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    h = max(0.0, min(1.0, (pax*bax + pay*bay + paz*baz) / (bax*bax + bay*bay + baz*baz + 1e-6)))
    return math.hypot(pax - bax*h, pay - bay*h, paz - baz*h) - r

def sdf_torus(p, c, r_major, r_minor):
    px, py, pz = p[0]-c[0], p[1]-c[1], p[2]-c[2]
    q = math.hypot(px, pz) - r_major
    return math.hypot(q, py) - r_minor

def op_smooth_union(d1, d2, k=0.35):
    h = max(k - abs(d1 - d2), 0.0) / k
    return min(d1, d2) - h * h * k * 0.25

def op_subtract(d1, d2):
    return max(d1, -d2)

# --- 2. Greedy Brick Mesher (Converts any 3D SDF into Stepped Bricks + Studs) ---
def voxelize_and_mesh_to_bricks(sdf_fn, bounds=((-3,-3,-3),(3,3,3)), Pitch=(0.4, 0.32, 0.4)):
    """
    Samples any continuous 3D (x,y,z) -> (distance, color_key) function
    and greedy-merges solid voxels into large non-overlapping stepped bricks.
    """
    (xmin, ymin, zmin), (xmax, ymax, zmax) = bounds
    dx, dy, dz = Pitch
    nx = int(round((xmax - xmin) / dx))
    ny = int(round((ymax - ymin) / dy))
    nz = int(round((zmax - zmin) / dz))

    # Sample 3D grid
    grid = {}
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                wx = xmin + (ix + 0.5) * dx
                wy = ymin + (iy + 0.5) * dy
                wz = zmin + (iz + 0.5) * dz
                d, col = sdf_fn((wx, wy, wz))
                if d <= 0.0:
                    grid[(ix, iy, iz)] = col

    # Greedy 3D box merging (merges adjacent voxels of same color into optimal bricks)
    visited = set()
    parts = [{"n": "CoreRoot", "p": None, "s": "box", "sz": [0.2, 0.2, 0.2], "po": [0, 0, 0], "ro": [0, 0, 0], "c": "A"}]
    part_id = 0

    for iy in range(ny):
        for iz in range(nz):
            for ix in range(nx):
                if (ix, iy, iz) not in grid or (ix, iy, iz) in visited:
                    continue
                col = grid[(ix, iy, iz)]
                # Expand X
                wx = 1
                while (ix + wx, iy, iz) in grid and (ix + wx, iy, iz) not in visited and grid[(ix + wx, iy, iz)] == col:
                    wx += 1
                # Expand Z
                wz = 1
                can_z = True
                while can_z:
                    for tx in range(ix, ix + wx):
                        if (tx, iy, iz + wz) not in grid or (tx, iy, iz + wz) in visited or grid[(tx, iy, iz + wz)] != col:
                            can_z = False
                            break
                    if can_z:
                        wz += 1
                # Expand Y
                wy = 1
                can_y = True
                while can_y and wy < 3:  # Cap brick height to keep stepped brick aesthetic
                    for tx in range(ix, ix + wx):
                        for tz in range(iz, iz + wz):
                            if (tx, iy + wy, tz) not in grid or (tx, iy + wy, tz) in visited or grid[(tx, iy + wy, tz)] != col:
                                can_y = False
                                break
                        if not can_y:
                            break
                    if can_y:
                        wy += 1

                for tx in range(ix, ix + wx):
                    for ty in range(iy, iy + wy):
                        for tz in range(iz, iz + wz):
                            visited.add((tx, ty, tz))

                part_id += 1
                b_name = f"Brick_{part_id}"
                sz = [round(wx * dx, 2), round(wy * dy, 2), round(wz * dz, 2)]
                po = [
                    round(xmin + (ix + wx * 0.5) * dx, 2),
                    round(ymin + (iy + wy * 0.5) * dy, 2),
                    round(zmin + (iz + wz * 0.5) * dz, 2),
                ]
                parts.append({"n": b_name, "p": "CoreRoot", "s": "box", "sz": sz, "po": po, "ro": [0, 0, 0], "c": col})

                # Add top studs only where the top surface is exposed to air
                top_iy = iy + wy
                for tx in range(ix, ix + wx, 2):
                    for tz in range(iz, iz + wz, 2):
                        if (tx, top_iy, tz) not in grid:
                            sx = round((tx - (ix + wx * 0.5) + 0.5) * dx, 2)
                            sy = round(sz[1] * 0.5 + 0.05, 2)
                            sz_off = round((tz - (iz + wz * 0.5) + 0.5) * dz, 2)
                            parts.append({
                                "n": f"Stud_{part_id}_{tx}_{tz}",
                                "p": b_name,
                                "s": "cylinder",
                                "sz": [0.26, 0.12, 0.26],
                                "po": [sx, sy, sz_off],
                                "ro": [0, 0, 0],
                                "c": col
                            })
    return parts
