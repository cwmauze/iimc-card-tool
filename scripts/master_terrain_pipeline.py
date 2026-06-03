import json
import math
import os
import time
import urllib.request
import ssl
import rasterio
import numpy as np
from rasterio.windows import from_bounds

# Bypass macOS Python SSL certificate verification for the public AWS bucket
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION ---
TERRAIN_DIR = "TerrainData"
PROCESSED_FILE = "processed_tiles.txt"
JSON_DB = "terrain.json"

# Set to True if you want to delete the .tif file immediately after extracting the peaks.
# This prevents your hard drive from filling up. (Tiles logged in processed_tiles.txt will not be re-downloaded).
DELETE_AFTER_PROCESSING = False 
# ---------------------

def ensure_valid_tile(filename, filepath):
    """Checks if a tile is corrupt. If it is, deletes it and re-downloads from AWS."""
    if os.path.exists(filepath):
        try:
            with rasterio.open(filepath) as ds:
                ds.read(1) # Deep payload read to verify integrity
            return True
        except Exception:
            print(f"    [!] Corrupt payload detected: {filename}. Trashing and re-downloading...")
            os.remove(filepath)

    # If we reach here, the file either didn't exist or was corrupt and deleted.
    base_name = filename.replace('.tif', '')
    aws_url = f"https://copernicus-dem-30m.s3.amazonaws.com/{base_name}/{filename}"
    
    print(f"    > Fetching fresh tile from AWS Open Data...")
    try:
        urllib.request.urlretrieve(aws_url, filepath)
        # Final validation of the new download
        with rasterio.open(filepath) as ds:
            ds.read(1)
        return True
    except Exception as e:
        print(f"    [!] Failed to acquire valid tile from AWS: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

def master_terrain_pipeline():
    print("[-] Initializing Master Terrain Pipeline (Auto-Healing & V2 Numpy Math)...")
    
    if not os.path.exists(TERRAIN_DIR):
        os.makedirs(TERRAIN_DIR)
        
    # Scan directory for all intended files
    tif_files = [f for f in os.listdir(TERRAIN_DIR) if f.endswith('.tif')]
    if not tif_files:
        print("[!] No .tif files found in TerrainData folder! Add at least one tile to seed the list.")
        return
        
    # Load existing database to allow seamless resuming
    terrain_grid = {}
    if os.path.exists(JSON_DB):
        try:
            with open(JSON_DB, 'r') as f:
                terrain_grid = json.load(f)
            print(f"[-] Loaded existing {JSON_DB} with {len(terrain_grid)} sectors.")
        except:
            print(f"[!] Warning: Could not read {JSON_DB}. Starting fresh.")

    # Load tracker to avoid re-downloading or re-scanning completed tiles
    processed_tiles = set()
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            processed_tiles = set(line.strip() for line in f)
        print(f"[-] Loaded tracker: {len(processed_tiles)} tiles already completed.")

    grid_resolution = 0.1
    total_files = len(tif_files)
    completed_files = len(processed_tiles)
    
    tiles_to_process = total_files - completed_files
    if tiles_to_process <= 0:
        print("\n[-] All tracked tiles have already been processed!")
        return
        
    session_start_time = time.time()
    session_processed_count = 0

    for filename in tif_files:
        if filename in processed_tiles:
            continue # Smart skip: bypasses processing and downloading entirely
            
        filepath = os.path.join(TERRAIN_DIR, filename)
        
        session_processed_count += 1
        master_percent = (completed_files / total_files) * 100
        
        # Calculate ETA
        elapsed_time = time.time() - session_start_time
        avg_time_per_tile = elapsed_time / session_processed_count if session_processed_count > 0 else 0
        remaining_tiles = total_files - completed_files
        eta_seconds = avg_time_per_tile * remaining_tiles
        eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds)) if session_processed_count > 1 else "Calculating..."
        
        print(f"\n[-] Processing [{completed_files + 1}/{total_files} | {master_percent:.1f}%] - {filename}")
        print(f"    > ETA: {eta_str}")
        
        # Phase 1: Auto-Heal & Validate
        if not ensure_valid_tile(filename, filepath):
            print(f"    > Skipping {filename} due to unrecoverable errors.")
            continue
        
        # Phase 2: High-Speed Numpy Extraction
        with rasterio.open(filepath) as dataset:
            bounds = dataset.bounds
            transform = dataset.transform
            nodata = dataset.nodata
            
            full_data = dataset.read(1)
            
            if nodata is not None:
                full_data = np.where(full_data == nodata, -9999, full_data)

            start_lat = math.floor(bounds.bottom * 10) / 10.0
            end_lat = math.ceil(bounds.top * 10) / 10.0
            start_lon = math.floor(bounds.left * 10) / 10.0
            end_lon = math.ceil(bounds.right * 10) / 10.0

            lat_steps = int(round((end_lat - start_lat) / grid_resolution))
            lon_steps = int(round((end_lon - start_lon) / grid_resolution))

            for i in range(lat_steps):
                cell_start_lat = start_lat + (i * grid_resolution)
                cell_end_lat = cell_start_lat + grid_resolution
                
                for j in range(lon_steps):
                    cell_start_lon = start_lon + (j * grid_resolution)
                    cell_end_lon = cell_start_lon + grid_resolution

                    window = from_bounds(
                        cell_start_lon, cell_start_lat,
                        cell_end_lon, cell_end_lat,
                        transform=transform
                    )
                    
                    window = window.round_lengths().round_offsets()
                    
                    row_start, row_end = int(window.row_off), int(window.row_off + window.height)
                    col_start, col_end = int(window.col_off), int(window.col_off + window.width)

                    row_start, row_end = max(0, row_start), min(full_data.shape[0], row_end)
                    col_start, col_end = max(0, col_start), min(full_data.shape[1], col_end)

                    cell_data = full_data[row_start:row_end, col_start:col_end]
                    
                    if cell_data.size == 0:
                        continue
                        
                    max_val_meters = np.max(cell_data)
                    
                    if max_val_meters <= -1000:
                        continue 

                    local_row, local_col = np.unravel_index(np.argmax(cell_data), cell_data.shape)
                    global_row = row_start + local_row
                    global_col = col_start + local_col
                    
                    exact_lon, exact_lat = dataset.xy(global_row, global_col)
                    max_elev_feet = max_val_meters * 3.28084
                    key = f"{round(cell_start_lat, 1)}_{round(cell_start_lon, 1)}"
                    
                    if key in terrain_grid:
                        existing_elev = terrain_grid[key][0] if isinstance(terrain_grid[key], list) else terrain_grid[key]
                        if max_elev_feet > existing_elev:
                            terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(exact_lat, 6), round(exact_lon, 6)]
                    else:
                        terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(exact_lat, 6), round(exact_lon, 6)]

        # Phase 3: Record Keeping & Cleanup
        completed_files += 1
        with open(PROCESSED_FILE, 'a') as f:
            f.write(f"{filename}\n")
            
        with open(JSON_DB, 'w') as f:
            json.dump(terrain_grid, f, separators=(',', ':'))

        if DELETE_AFTER_PROCESSING:
            os.remove(filepath)

    print(f"\n[-] Master Pipeline Complete!")
    print(f"[-] Final Database Size: {len(terrain_grid)} sectors.")
    print(f"[-] File size: {os.path.getsize(JSON_DB) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    try:
        master_terrain_pipeline()
    except KeyboardInterrupt:
        print("\n\n[!] Process interrupted by user. Progress has been securely saved. Run the script again to resume.")