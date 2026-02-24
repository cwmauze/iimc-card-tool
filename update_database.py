import os
import json
import zipfile
import io
import requests
import datetime
import re
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DOF_URL = "https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/dof/"

# Exact FAA APT.txt Column Slices (0-indexed)
APT_COLS = {
    'id': (27, 31),
    'name': (133, 183),
    'lat': (523, 538), 
    'lon': (550, 565)  
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_current_airac_cycle():
    base_date = datetime.date(2026, 1, 22) 
    today = datetime.date.today()
    delta = (today - base_date).days
    cycles_passed = delta // 28
    return base_date + datetime.timedelta(days=cycles_passed*28)

def get_dof_zip_url():
    response = requests.get(DOF_URL, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    for link in soup.find_all('a', href=True):
        if 'dof' in link['href'].lower() and link['href'].lower().endswith('.zip'):
            return link['href'] if link['href'].startswith('http') else f"https://www.faa.gov{link['href']}"
            
    match = re.search(r'["\']([^"\']*dof[^"\']*\.zip)["\']', response.text, re.IGNORECASE)
    if match:
        url = match.group(1)
        return url if url.startswith('http') else f"https://www.faa.gov{url}"
        
    raise Exception("Could not find a valid DOF ZIP link.")

def faa_to_decimal(s):
    if not s or s.strip() == "": return 0.0
    s = s.strip().upper()
    mult = -1 if ('S' in s or 'W' in s) else 1
    clean = s.replace('N','').replace('S','').replace('E','').replace('W','')
    parts = clean.split('-')
    try:
        if len(parts) >= 3:
            dd = float(parts[0]) + float(parts[1])/60 + float(parts[2])/3600
        else:
            dd = float(clean)
        return round(dd * mult, 6)
    except: 
        return 0.0

def parse_dof_dms(dms_str):
    dms_str = dms_str.strip()
    if not dms_str: return 0.0
    direction = dms_str[-1]
    parts = dms_str[:-1].split()
    if len(parts) != 3: return 0.0
    decimal = float(parts[0]) + (float(parts[1]) / 60.0) + (float(parts[2]) / 3600.0)
    if direction in ['S', 'W']: decimal = -decimal
    return decimal
        
def process_data():
    obstacles = []
    airports = {}
    metadata = {"dof_date": "Unknown", "apt_count": 0, "obs_count": 0}

    print("[-] Fetching latest DOF ZIP...")
    try:
        dof_zip_url = get_dof_zip_url()
        print(f"[-] Downloading: {dof_zip_url}")
        
        r_dof = requests.get(dof_zip_url, headers=HEADERS)
        with zipfile.ZipFile(io.BytesIO(r_dof.content)) as z:
            dat_filename = next(name for name in z.namelist() if name.upper().endswith('DOF.DAT'))
            with z.open(dat_filename) as f:
                for line_bytes in f:
                    line = line_bytes.decode('utf-8', errors='ignore')
                    
                    if line.startswith("  CURRENCY DATE ="):
                        metadata["dof_date"] = line.split("=")[1].strip()
                        
                    if len(line) < 100 or line.startswith("CUR") or line.startswith("-") or line.startswith("OAS") or line.startswith(" "):
                        continue
                    
                    try:
                        msl_str = line[89:94].strip() 
                        agl_str = line[83:88].strip() 

                        if not msl_str.isdigit() or not agl_str.isdigit(): continue
                        
                        msl = int(msl_str)
                        agl = int(agl_str)

                        if agl < 200: continue
                        
                        # Smart pattern search to ignore FAA column shifts
                        lat = parse_dof_dms(re.search(r'\d{2}\s+\d{2}\s+[\d\.]+[NS]', line).group())
                        lon = parse_dof_dms(re.search(r'\d{2,3}\s+\d{2}\s+[\d\.]+[EW]', line).group())
                        city = line[18:34].strip()
                        state = line[15:17].strip().upper()
                        oas = line[0:9].strip()
                        
                        obstacles.append({
                            "id": oas, 
                            "state": state, 
                            "city": city, 
                            "lat": lat, 
                            "lon": lon, 
                            "agl": agl, 
                            "msl": msl
                        })
                    except:
                        continue
        print(f"    > Parsed {len(obstacles)} Obstacles.")
    except Exception as e:
        print(f"[!] DOF Process failed: {e}")

    print("\n[-] Fetching latest NASR APT ZIP...")
    cycle_date = get_current_airac_cycle()
    date_str = cycle_date.strftime("%Y-%m-%d")
    
    metadata["apt_date"] = cycle_date.strftime("%m/%d/%y")
    
    try:
        # Bypass the FAA landing page directly to the ZIP
        zip_url = f"https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_{date_str}.zip"
        print(f"[-] Downloading: {zip_url}")
        r_nasr = requests.get(zip_url, headers=HEADERS, stream=True, timeout=45)
        
        with zipfile.ZipFile(io.BytesIO(r_nasr.content)) as z:
            # 1. Parse Airports and Overlying Centers
            apt_file_info = next(f for f in z.infolist() if f.filename.endswith('APT.txt'))
            with z.open(apt_file_info) as f:
                for line_bytes in f:
                    line = line_bytes.decode('latin-1', errors='ignore')
                    if line.startswith("APT"):
                        loc_id = line[APT_COLS['id'][0]:APT_COLS['id'][1]].strip()
                        name_str = line[APT_COLS['name'][0]:APT_COLS['name'][1]].strip()
                        lat_str = line[APT_COLS['lat'][0]:APT_COLS['lat'][1]].strip()
                        lon_str = line[APT_COLS['lon'][0]:APT_COLS['lon'][1]].strip()
                        if loc_id and lat_str and lon_str:
                            lat = faa_to_decimal(lat_str)
                            lon = faa_to_decimal(lon_str)
                            center_id = line[637:640].strip()
                            if lat != 0.0 and lon != 0.0:
                                airports[loc_id] = {
                                    "name": name_str, 
                                    "lat": lat, 
                                    "lon": lon,
                                    "center_id": center_id,
                                    "primary_freq": "None",
                                    "center_freq": "None"
                                }
                                
            # 2. Parse Frequencies from TWR.txt
            twr_file_info = next(f for f in z.infolist() if f.filename.endswith('TWR.txt'))
            with z.open(twr_file_info) as f:
                for line_bytes in f:
                    line = line_bytes.decode('latin-1', errors='ignore')
                    
                    # Primary Approach/Departure
                    if line.startswith("TWR7"):
                        loc_id = line[4:8].strip()
                        if loc_id in airports and ("APCH" in line or "DEP" in line):
                            freq_match = re.search(r'\d{3}\.\d{1,3}', line)
                            if freq_match and airports[loc_id]["primary_freq"] == "None":
                                airports[loc_id]["primary_freq"] = freq_match.group()
                                
                    # Backup Center Frequency
                    elif line.startswith("TWR6"):
                        loc_id = line[4:8].strip()
                        if loc_id in airports and ("ARTCC" in line or "Z" in line):
                            freq_match = re.search(r'\b(?:ON|FREQS)\s+(\d{3}\.\d{1,3})', line)
                            if freq_match and airports[loc_id]["center_freq"] == "None":
                                airports[loc_id]["center_freq"] = freq_match.group(1)

        print(f"    > Parsed {len(airports)} Airports/Heliports with frequencies.")
    except Exception as e:
        print(f"[!] NASR Process failed: {e}")

    print("\n[-] Compiling outputs...")
    
    if len(obstacles) > 0:
        with open("obstacles.json", 'w') as f:
            json.dump(obstacles, f, separators=(',', ':'))
        metadata["obs_count"] = len(obstacles)
        print(f"[-] Saved {len(obstacles)} obstacles.")
    else:
        print("[!] WARNING: No obstacles parsed. Skipping overwrite to protect existing data.")
        if os.path.exists("obstacles.json"):
            try:
                with open("obstacles.json", 'r') as f:
                    metadata["obs_count"] = len(json.load(f))
            except: pass
            
    if len(airports) > 0:
        with open("airports.json", 'w') as f:
            json.dump(airports, f, separators=(',', ':'))
        metadata["apt_count"] = len(airports)
        print(f"[-] Saved {len(airports)} airports.")
        
    with open("metadata.json", 'w') as f:
        json.dump(metadata, f)
        
    print("[-] Success. Database update complete.")

if __name__ == "__main__":
    process_data()