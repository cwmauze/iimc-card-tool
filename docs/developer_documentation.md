# IIMC Card Tool - Developer Documentation

## 1. System Architecture
The IIMC (Inadvertent Instrument Meteorological Conditions) Card Tool is a **100% client-side, static web application**. It is designed to function offline once loaded, ensuring pilots can use it in areas with degraded cellular reception.

- **Frontend:** HTML, CSS, Vanilla JavaScript.
- **Backend / Database:** None at runtime. All data is pre-compiled into static JSON files (`airports.json`, `obstacles.json`, `terrain.json`, `metadata.json`).
- **Hosting:** GitHub Pages.
- **Data Maintenance:** Python scripts running via GitHub Actions on a cron schedule.

## 2. Directory Structure
- `index.html`: The main entry point containing the UI, Kneeboard generation logic, and map integration.
- `js/app.js`: Contains data fetching logic and core calculation functions (Haversine distance, USGS API fallback).
- `css/style.css`: Contains additional styling.
- `data/`: The static JSON databases used by the application.
- `scripts/`: Python scripts used for offline data processing and database updates.
- `.github/workflows/`: GitHub Actions workflows for CI/CD automation.

## 3. Data Pipeline & Maintenance

### FAA Database Updates (NASR & DOF)
The application relies on accurate FAA data for obstacles and airports. This is automated via `.github/workflows/update-database.yml`, which runs `scripts/update_database.py` every Sunday.

1. **DOF (Digital Obstacle File):** The script parses the FAA's 56-day DOF `.dat` file, extracts obstacles >200ft AGL, and saves them to `obstacles.json`.
2. **NASR (National Airspace System Resource):** The script downloads the current 28-day AIRAC cycle ZIP, extracts `APT.txt` (airports) and `TWR.txt` (frequencies), and saves them to `airports.json`.

### Terrain Processing (Copernicus DEM)
Terrain data (Copernicus GLO-30) is processed offline to create a highly optimized grid for the frontend.
- Scripts like `master_terrain_pipeline.py` and `build_terrain_copernicus.py` take raw 30-meter GeoTIFFs, extract the absolute highest peak in every 0.1° x 0.1° coordinate grid, and compile this into `terrain.json`.
- This pre-processing is crucial for instant, offline performance in the browser.

## 4. Frontend Engine & Mathematical Model
The frontend engine is primarily contained within `index.html` (with some helpers in `js/app.js`).

### Core Calculation Logic (MSA)
When a user requests a Minimum Safe Altitude (MSA) calculation:
1. **Distance Checking:** The Haversine formula calculates the distance between the centerpoint and all obstacles/terrain grid points.
2. **Sector Checking:** If custom sectors are used, the True Bearing is calculated and adjusted for Magnetic Variation (using the integrated WMM 2025-2030 Epoch model) to determine which sector the point falls into.
3. **Controlling Factor:** The highest obstacle or terrain peak (MSL) within the sector/radius is identified.
4. **Padding:** A 100-foot TERPS pad + 1,000-foot IFR buffer is added.
5. **Rounding:** The final value is rounded up to the next 100-foot increment.

### UI & Kneeboard Generation
- **Map Preview:** Uses Leaflet.js to render a map preview with street, satellite, or VFR sectional layers.
- **Print Spooler:** The application uses custom CSS `@media print` queries and dynamic DOM manipulation to build a printable PDF kneeboard card directly in the browser. Layouts can be saved as JSON templates.
