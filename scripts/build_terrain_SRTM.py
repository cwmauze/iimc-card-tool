import json
import srtm
import math
import os

def build_terrain_grid():
    print("[-] Initializing SRTM Terrain Engine...")
    print("    (This will download NASA SRTM tiles locally on the first run. Please be patient.)")
    
    # Initialize the SRTM elevation data manager
    elevation_data = srtm.get_data()
    
    # Bounding boxes: [Min Lat, Max Lat, Min Lon, Max Lon]
    regions = {
        "CONUS": [24.0, 50.0, -125.0, -66.0],
        "ALASKA": [51.0, 72.0, -180.0, -129.0],
        "HAWAII": [18.0, 23.0, -161.0, -154.0]
    }
    
    terrain_grid = {}
    grid_resolution = 0.1 # 0.1 degrees is ~6 NM 
    
    # [SUGGESTED UPDATE]: Increased sub_samples from 3 to 120 for ~90m SRTM3 resolution
    sub_samples = 120 
    
    for region_name, bounds in regions.items():
        print(f"[-] Processing {region_name}...")
        lat_min, lat_max, lon_min, lon_max = bounds
        
        # Calculate total rows for the progress tracker
        total_lat_steps = int(round((lat_max - lat_min) / grid_resolution)) + 1
        current_step = 0
        
        lat = lat_min
        while lat <= lat_max:
            # Update the console with a rolling percentage
            current_step += 1
            percent = (current_step / total_lat_steps) * 100
            print(f"\r    Scanning row {current_step}/{total_lat_steps} ({percent:.1f}%) complete...", end="", flush=True)
            
            lon = lon_min
            while lon <= lon_max:
                max_elev_feet = 0
                max_lat = lat
                max_lon = lon
                
                # Sample the 0.1 degree cell to find the highest rock
                for i in range(sub_samples):
                    for j in range(sub_samples):
                        sample_lat = lat + (i * (grid_resolution / sub_samples))
                        sample_lon = lon + (j * (grid_resolution / sub_samples))
                        
                        try:
                            elev_meters = elevation_data.get_elevation(sample_lat, sample_lon)
                            if elev_meters:
                                elev_feet = elev_meters * 3.28084
                                if elev_feet > max_elev_feet:
                                    max_elev_feet = elev_feet
                                    max_lat = sample_lat
                                    max_lon = sample_lon
                        except:
                            pass
                
                # Only store the cell if there is actually terrain above sea level to save file size
                if max_elev_feet > 0:
                    # Key format: "Lat_Lon" rounded to 1 decimal
                    key = f"{round(lat, 1)}_{round(lon, 1)}"
                    # Store as an array: [Elevation, Exact Latitude, Exact Longitude]
                    terrain_grid[key] = [int(math.ceil(max_elev_feet)), round(max_lat, 4), round(max_lon, 4)]
                
                lon += grid_resolution
            lat += grid_resolution
            
        # Print a newline when the region finishes so the next region doesn't overwrite it
        print()

    print(f"[-] Compiling outputs...")
    with open("terrain.json", 'w') as f:
        json.dump(terrain_grid, f, separators=(',', ':'))
        
    print(f"[-] Success. Saved {len(terrain_grid)} terrain grid sectors to terrain.json.")
    print(f"[-] File size: {os.path.getsize('terrain.json') / 1024:.1f} KB")

if __name__ == "__main__":
    build_terrain_grid()