import os
import requests
import time

def download_copernicus():
    # Define our bounding boxes (min_lat, max_lat, min_lon, max_lon)
    regions = {
        "HAWAII": (18, 23, -161, -154),
        "CONUS": (24, 50, -125, -66),
        "ALASKA": (51, 72, -180, -129)
    }

    # AWS Open Data public bucket for Copernicus GLO-30
    base_url = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
    output_dir = "TerrainData"
    os.makedirs(output_dir, exist_ok=True)

    session = requests.Session()

    for region_name, bounds in regions.items():
        min_lat, max_lat, min_lon, max_lon = bounds
        print(f"\n[-] Starting AWS pipeline for {region_name}...")
        
        # Copernicus tiles are identified by their bottom-left corner coordinate
        for lat in range(min_lat, max_lat + 1):
            for lon in range(min_lon, max_lon + 1):
                # Format the hemisphere and coordinates (e.g., N40_00_W105_00)
                ns = "N" if lat >= 0 else "S"
                ew = "E" if lon >= 0 else "W"
                
                abs_lat = abs(lat)
                abs_lon = abs(lon)
                
                tile_id = f"{ns}{abs_lat:02d}_00_{ew}{abs_lon:03d}_00"
                folder_name = f"Copernicus_DSM_COG_10_{tile_id}_DEM"
                file_name = f"{folder_name}.tif"
                
                url = f"{base_url}/{folder_name}/{file_name}"
                out_path = os.path.join(output_dir, file_name)
                
                # Skip if we already successfully downloaded it
                if os.path.exists(out_path):
                    continue

                try:
                    # Stream the download so we don't blow up system RAM
                    response = session.get(url, stream=True, timeout=10)
                    
                    # A 200 means the tile exists (land). 403/404 means it's pure ocean.
                    if response.status_code == 200:
                        print(f"    [+] Downloading: {file_name}")
                        with open(out_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        # Brief pause to respect the AWS server rate limits
                        time.sleep(0.1)
                except Exception as e:
                    print(f"    [!] Error downloading {file_name}: {e}")

    print("\n[-] All regions downloaded successfully. You are ready to run build_terrain.py!")

if __name__ == "__main__":
    download_copernicus()