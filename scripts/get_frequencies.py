import io
import requests
import zipfile
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def test_frequencies(airport_id):
    print(f"[-] Fetching NASR data for {airport_id}...")
    zip_url = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-02-19.zip"
    r_nasr = requests.get(zip_url, headers=HEADERS, stream=True)
    
    primary_freq = "None"
    center_freq = "None"
    center_id = "Unknown"

    with zipfile.ZipFile(io.BytesIO(r_nasr.content)) as z:
        
        # 1. Grab the exact Center ID from column 637
        apt_file = next(f for f in z.infolist() if f.filename.endswith('APT.txt'))
        with z.open(apt_file) as f:
            for line_bytes in f:
                line = line_bytes.decode('latin-1', errors='ignore')
                if line.startswith("APT") and line[27:31].strip() == airport_id:
                    center_id = line[637:640].strip()
                    break
                    
        # 2. Extract specific Frequencies from TWR.txt
        twr_file = next(f for f in z.infolist() if f.filename.endswith('TWR.txt'))
        with z.open(twr_file) as f:
            for line_bytes in f:
                line = line_bytes.decode('latin-1', errors='ignore')
                
                # Primary Approach/Departure (Separated Logic)
                if line.startswith("TWR3") and line[4:8].strip() == airport_id:
                    # TWR3 lines are exclusively Approach/Departure. No keyword needed.
                    freq_match = re.search(r'1[1-3]\d\.\d{1,3}', line)
                    if freq_match and primary_freq == "None":
                        primary_freq = freq_match.group()
                        
                elif line.startswith("TWR7") and line[4:8].strip() == airport_id:
                    # TWR7 are remarks. We MUST require keywords to avoid ATIS/Ground.
                    if any(keyword in line for keyword in ["APCH", "DEP", "APP"]):
                        freq_match = re.search(r'1[1-3]\d\.\d{1,3}', line)
                        if freq_match and primary_freq == "None":
                            primary_freq = freq_match.group()
                            
                # Backup Center Frequency from Remarks (TWR6 lines)
                if line.startswith("TWR6") and line[4:8].strip() == airport_id:
                    if "ARTCC" in line or "Z" in line:
                        freq_match = re.search(r'\b(?:ON|FREQS)\s+(\d{3}\.\d{1,3})', line)
                        if freq_match and center_freq == "None":
                            center_freq = freq_match.group(1)

    print(f"\n[+] IIMC Frequencies for {airport_id}:")
    print(f"    Overlying Center: {center_id}")
    print(f"    Primary (Approach): {primary_freq}")
    print(f"    Backup (Center): {center_freq}\n")

if __name__ == "__main__":
    test_frequencies("SLC")
    test_frequencies("RWI")