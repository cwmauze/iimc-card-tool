import json
import math
import os
import time
import rasterio
import numpy as np
from rasterio.windows import from_bounds

def build_terrain_grid():
    print("[-] Initializing Copernicus V2.0 Numpy Terrain Engine...")
    terrain_dir = "TerrainData"
    
    if not os.path.exists(terrain_dir):
        print(f"[!] Directory '{terrain_dir}' not found. Please create it and add .tif files.")
        return
        
    tif_files = [os.path.join(terrain_dir, f) for f in os.listdir(terrain_dir) if f.endswith('.tif')]
    if not tif_files:
        print("[!] No .tif files found in TerrainData folder!")
        return
        
    # Load existing database to allow seamless resuming
    terrain_grid = {}
    if os.path.exists("terrain.json"):
        try:
            with open("terrain.json", 'r') as f:
                terrain_grid = json.load(f)
            print(f"[-] Loaded existing terrain.json with {len(terrain_grid)} sectors.")
        except:
            print("[!] Warning: Could not read existing terrain.json. Starting fresh.")

    # Load tracker to avoid re-scanning completed tiles
    processed_file = "processed_tiles.txt"
    processed_tiles = set()
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_tiles = set(line.strip() for line in f)
        print(f"[-] Loaded tracker: {len(processed_tiles)} tiles already completed.")

    grid_resolution = 0.1
    total_files = len(tif_files)
    completed_files = len(processed_tiles)
    
    # Tracking for ETA calculation
    tiles_to_process = total_files - completed_files
    if tiles_to_process == 0:
        print("\n[-] All tiles have already been processed!")
        return
        
    session_start_time = time.time()
    session_processed_count = 0

    for tif_path in tif_files:
        filename = os.path.basename(tif_path)
        if filename in processed_tiles:
            continue
            
        session_processed_count += 1
        master_percent = (completed_files / total_files) * 100
        
        # Calculate ETA
        elapsed_time = time.time() - session_start_time
        avg_time_per_tile = elapsed_time / session_processed_count if session_processed_count > 0 else 0
        remaining_tiles = total_files - completed_files
        eta_seconds = avg_time_per_tile * remaining_tiles
        eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds)) if session_processed_count > 1 else "Calculating..."
        
        print(f"\n[-] Processing [{completed_files + 1}/{total_files} | {master_percent:.1f}%] - {filename}")
        print(f"    > ETA: {eta_str} | Extracting pure numpy arrays...")
        
        with rasterio.open(tif_path) as dataset:
            bounds = dataset.bounds
            transform = dataset.transform
            nodata = dataset.nodata
            
            # Read the entire 1-degree tile into RAM instantly
            try:
                full_data = dataset.read(1)
            except Exception as e:
                print(f"\n[!] CORRUPTED TILE DETECTED: {filename}. Skipping to prevent crash.")
                continue
                
            # Mask out nodata values (ocean/voids) so they don't corrupt the max search
            if nodata is not None:
                full_data = np.where(full_data == nodata, -9999, full_data)

            # Define the bounding box grid edges
            start_lat = math.floor(bounds.bottom * 10) / 10.0
            end_lat = math.ceil(bounds.top * 10) / 10.0
            start_lon = math.floor(bounds.left * 10) / 10.0
            end_lon = math.ceil(bounds.right * 10) / 10.0

            lat_steps = int(round((end_lat - start_lat) / grid_resolution))
            lon_steps = int(round((end_lon - start_lon) / grid_resolution))

            # Iterate through the 0.1 degree grid cells
            for i in range(lat_steps):
                cell_start_lat = start_lat + (i * grid_resolution)
                cell_end_lat = cell_start_lat + grid_resolution
                
                for j in range(lon_steps):
                    cell_start_lon = start_lon + (j * grid_resolution)
                    cell_end_lon = cell_start_lon + grid_resolution

                    # Get the pixel window that corresponds to this 0.1 degree cell
                    window = from_bounds(
                        cell_start_lon, cell_start_lat,
                        cell_end_lon, cell_end_lat,
                        transform=transform
                    )
                    
                    # Round to exact pixel boundaries
                    window = window.round_lengths().round_offsets()
                    
                    row_start, row_end = int(window.row_off), int(window.row_off + window.height)
                    col_start, col_end = int(window.col_off), int(window.col_off + window.width)

                    # Safety bound check
                    row_start, row_end = max(0, row_start), min(full_data.shape[0], row_end)
                    col_start, col_end = max(0, col_start), min(full_data.shape[1], col_end)

                    # Slice the numpy array
                    cell_data = full_data[row_start:row_end, col_start:col_end]
                    
                    if cell_data.size == 0:
                        continue
                        
                    max_val_meters = np.max(cell_data)
                    
                    if max_val_meters <= -1000:
                        continue # Skip cells that are entirely ocean or nodata

                    # Find the local array index of the highest pixel
                    local_row, local_col = np.unravel_index(np.argmax(cell_data), cell_data.shape)
                    
                    # Translate local index back to global raster index
                    global_row = row_start + local_row
                    global_col = col_start + local_col
                    
                    # Get the exact dead-center coordinate of that specific maximum pixel
                    exact_lon, exact_lat = dataset.xy(global_row, global_col)
                    
                    max_elev_feet = max_val_meters * 3.28084
                    key = f"{round(cell_start_lat, 1)}_{round(cell_start_lon, 1)}"
                    
                    # Check for overlaps (Copernicus tiles often overlap by 1 pixel)
                    if key in terrain_grid:
                        existing_elev = terrain_grid[key][0] if isinstance(terrain_grid[key], list) else terrain_grid[key]
                        if max_elev_feet > existing_elev:
                            # 6 decimal places for extreme coordinate precision
                            terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(exact_lat, 6), round(exact_lon, 6)]
                    else:
                        terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(exact_lat, 6), round(exact_lon, 6)]

        # Save progress securely after every tile
        completed_files += 1
        with open(processed_file, 'a') as f:
            f.write(f"{filename}\n")
            
        with open("terrain.json", 'w') as f:
            json.dump(terrain_grid, f, separators=(',', ':'))

    print(f"\n[-] Processing Complete!")
    print(f"[-] Final Database Size: {len(terrain_grid)} sectors.")
    print(f"[-] File size: {os.path.getsize('terrain.json') / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    try:
        build_terrain_grid()
    except KeyboardInterrupt:
        print("\n\n[!] Process interrupted by user. Progress has been saved. You can resume at any time.")