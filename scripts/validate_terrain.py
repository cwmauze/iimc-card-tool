import os
import rasterio

def validate_tifs():
    directory = "TerrainData"
    if not os.path.exists(directory):
        print(f"[!] Directory '{directory}' not found.")
        return

    tif_files = [f for f in os.listdir(directory) if f.endswith('.tif')]
    print(f"[-] Found {len(tif_files)} tiles. Starting integrity sweep...")
    
    bad_files = []
    
    for i, file in enumerate(tif_files):
        filepath = os.path.join(directory, file)
        
        # Check 1: File size (A pure ocean tile might be small, but under 1KB is definitely a corrupted drop)
        if os.path.getsize(filepath) < 1024:
            bad_files.append((file, "Too small (Under 1KB)"))
            continue
            
        # Check 2: Can rasterio actually open and read the geospatial header?
        try:
            with rasterio.open(filepath) as dataset:
                bounds = dataset.bounds # Forces rasterio to parse the internal metadata
        except Exception as e:
            bad_files.append((file, "Corrupted or unreadable GeoTIFF"))

        # Simple progress tracker
        if i % 100 == 0 and i > 0:
            print(f"    ...checked {i}/{len(tif_files)} tiles")

    print("\n[-] Validation Complete.")
    if not bad_files:
        print("[+] SUCCESS: All downloaded tiles passed the integrity check!")
    else:
        print(f"[!] WARNING: Found {len(bad_files)} bad tiles. You should delete these and re-run the downloader:")
        for bad in bad_files:
            print(f"    - {bad[0]} : {bad[1]}")

if __name__ == "__main__":
    validate_tifs()