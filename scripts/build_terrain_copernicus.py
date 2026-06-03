import json
import math
import os
import rasterio

def build_terrain_grid():
    print("[-] Initializing Local Rasterio Terrain Engine...")
    terrain_dir = "TerrainData"
    
    if not os.path.exists(terrain_dir):
        print(f"[!] Directory '{terrain_dir}' not found. Please create it and add .tif files.")
        return
        
    tif_files = [os.path.join(terrain_dir, f) for f in os.listdir(terrain_dir) if f.endswith('.tif')]
    if not tif_files:
        print("[!] No .tif files found in TerrainData folder!")
        return
        
    # If a terrain.json already exists, load it so we can seamlessly add new regions to it
    terrain_grid = {}
    if os.path.exists("terrain.json"):
        try:
            with open("terrain.json", 'r') as f:
                terrain_grid = json.load(f)
            print(f"[-] Loaded existing terrain.json with {len(terrain_grid)} sectors.")
        except:
            pass

    # NEW: Load processed tracker to avoid re-scanning completed tiles
    processed_file = "processed_tiles.txt"
    processed_tiles = set()
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_tiles = set(line.strip() for line in f)
        print(f"[-] Loaded tracker: {len(processed_tiles)} tiles already completed.")

    grid_resolution = 0.1
    sub_samples = 120 
    
    # NEW: Calculate totals for the master progress percentage
    total_files = len(tif_files)
    completed_files = len(processed_tiles)
    
    for idx, tif_path in enumerate(tif_files, start=1):
        filename = os.path.basename(tif_path)
        if filename in processed_tiles:
            continue # Instantly skip to the next file
            
        master_percent = (completed_files / total_files) * 100
        print(f"\n[-] Processing [{completed_files + 1}/{total_files} - {master_percent:.1f}% Overall]: {filename}...")
        
        with rasterio.open(tif_path) as dataset:
            bounds = dataset.bounds
            lon_min, lat_min, lon_max, lat_max = bounds.left, bounds.bottom, bounds.right, bounds.top
            
            start_lat = math.floor(lat_min * 10) / 10.0
            end_lat = math.ceil(lat_max * 10) / 10.0
            start_lon = math.floor(lon_min * 10) / 10.0
            end_lon = math.ceil(lon_max * 10) / 10.0
            
            total_lat_steps = int(round((end_lat - start_lat) / grid_resolution)) + 1
            current_step = 0
            
            lat = start_lat
            while lat <= end_lat:
                current_step += 1
                percent = (current_step / total_lat_steps) * 100
                print(f"\r    Scanning row {current_step}/{total_lat_steps} ({percent:.1f}%) complete...", end="", flush=True)
                
                lon = start_lon
                while lon <= end_lon:
                    max_elev_feet = 0
                    max_lat = lat
                    max_lon = lon
                    
                    # Build coordinate list for rapid batch sampling
                    coords = []
                    for i in range(sub_samples):
                        for j in range(sub_samples):
                            sample_lat = lat + (i * (grid_resolution / sub_samples))
                            sample_lon = lon + (j * (grid_resolution / sub_samples))
                            # Only sample if exactly within the bounds of this specific .tif file
                            if lat_min <= sample_lat <= lat_max and lon_min <= sample_lon <= lon_max:
                                coords.append((sample_lon, sample_lat)) # rasterio uses (x, y) = (lon, lat)
                    
                    if coords:
                        try:
                            for i, val in enumerate(dataset.sample(coords)):
                                elev_meters = val[0]
                                # Ignore nodata gaps (often represented as massive negative numbers)
                                if elev_meters > -1000 and elev_meters != dataset.nodata:
                                    elev_feet = elev_meters * 3.28084
                                    if elev_feet > max_elev_feet:
                                        max_elev_feet = elev_feet
                                        max_lat = coords[i][1]
                                        max_lon = coords[i][0]
                        except:
                            pass
                            
                    if max_elev_feet > 0:
                        key = f"{round(lat, 1)}_{round(lon, 1)}"
                        # Store as an array: [Elevation, Exact Latitude, Exact Longitude]
                        # And ensure we never overwrite a higher peak if tiles overlap
                        if key in terrain_grid:
                            if isinstance(terrain_grid[key], list):
                                existing_elev = terrain_grid[key][0]
                            else:
                                existing_elev = terrain_grid[key] # Backwards compatibility for old integer grids
                                
                            if max_elev_feet > existing_elev:
                                terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(max_lat, 4), round(max_lon, 4)]
                        else:
                            terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(max_lat, 4), round(max_lon, 4)]
                        
                    # Rounding prevents infinite while-loop floating point drift
                    lon = round(lon + grid_resolution, 4)
                lat = round(lat + grid_resolution, 4)
            
            # NEW: Mark this specific tile as completed and log it
            completed_files += 1
            with open(processed_file, 'a') as f:
                f.write(f"{filename}\n")
            
            # NEW: Save the JSON database incrementally after every tile
            with open("terrain.json", 'w') as f:
                json.dump(terrain_grid, f, separators=(',', ':'))

    print(f"\n[-] Compiling final outputs...")
    with open("terrain.json", 'w') as f:
        json.dump(terrain_grid, f, separators=(',', ':'))
        
    print(f"[-] Success. Saved {len(terrain_grid)} terrain grid sectors to terrain.json.")
    print(f"[-] File size: {os.path.getsize('terrain.json') / 1024:.1f} KB")

if __name__ == "__main__":
    build_terrain_grid()