# IIMC Card Tool

## Overview
The Inadvertent Instrument Meteorological Conditions (IIMC) Card Tool is a pre-flight planning web application designed for pilots. Its primary purpose is to generate localized Minimum Safe Altitude (MSA) diagrams and dynamic emergency action plans based on user-defined parameters, including centerpoint, action radius, and custom directional sectors.

This application is strictly intended for pre-flight use on the ground. It is designed to produce a highly accurate, printable kneeboard reference card that can be physically stored in the cockpit for immediate, offline access during an IIMC event or other emergency requiring rapid situational awareness.

---

## Data Provenance & Integrity
The core function of this tool is calculating safe altitudes. Therefore, the integrity of the MSA calculations relies entirely on the accuracy and currency of the underlying databases. This tool utilizes authoritative, highly vetted data for all terrain, obstacle, and airspace calculations.

### 1. Topographical Terrain Grid (Copernicus DEM GLO-30)
* **Source:** Copernicus Digital Elevation Model (GLO-30).
* **Resolution:** 1 arc-second (approximately 30 meters at the equator).
* **Processing Model:** To optimize for instantaneous performance without sacrificing life-safety margins, the raw 30-meter GeoTIFF tiles are pre-processed into an indexed search grid (`terrain.json`) using a custom build pipeline. 
* **Data Guarantee:** The airspace is divided into a 0.1° x 0.1° coordinate grid. Within every single grid square, the processing script evaluates thousands of individual 30-meter pixels and extracts **only the absolute maximum elevation**. This peak elevation, along with its exact latitude and longitude, is recorded. This strict extraction methodology guarantees that the absolute highest point of terrain in any sector is retained for MSA calculations. There is zero data smoothing, averaging, or interpolation that could artificially lower peak elevations.

### 2. Obstacle Database (FAA DOF)
* **Source:** Federal Aviation Administration (FAA) Digital Obstacle File (DOF).
* **Update Cycle:** The obstacle database is updated automatically every Sunday at 0000Z via a backend automated script (`update_database.py`) that fetches and parses the latest DOF `.dat` file directly from the FAA.
* **Data Handling:** The tool parses the FAA DOF, filtering out obstacles below 200 feet AGL to optimize processing. This is a standard aviation charting practice, as the underlying 30-meter terrain model and the applied 100-foot TERPS pad natively dictate baseline safety margins below this threshold. 

### 3. Airspace & Frequency Data (FAA NASR)
* **Source:** FAA National Airspace System Resource (NASR) 28-Day Subscription.
* **Update Cycle:** Strictly aligned with the FAA's 28-day AIRAC cycle. A backend automation fetches the current cycle's ZIP file directly from the FAA NFDC portal to ensure communication frequencies are current.
* **Data Handling:** The tool extracts precise airport coordinates, overlying ARTCC center identifiers, and primary approach/departure frequencies (`APT.txt` and `TWR.txt`).

### 4. Magnetic Variation (WMM)
* **Source:** World Magnetic Model (WMM) 2025-2030 Epoch.
* **Data Handling:** True North coordinates are converted to Magnetic North dynamically using an integrated client-side WMM calculation module. This ensures that the sector boundaries and headings printed on the card are magnetically accurate for the specific geographic location and current epoch.

---

## Mathematical Model: How the MSA is Calculated
The tool utilizes a strict, conservative mathematical engine to determine the Minimum Safe Altitude for any defined sector. When a user requests a calculation, the following sequence occurs:

1. **Geospatial Bounding:** The tool establishes a search bounding box based on the defined centerpoint and nautical mile radius, explicitly accounting for spherical Earth convergence to ensure no edge-case terrain is missed.
2. **Radial Distance Verification:** Every terrain peak and obstacle within the bounding box is subjected to the Haversine formula to verify it physically falls within the requested nautical mile radius.
3. **Sector Bearing Verification:** The tool calculates the True Bearing from the centerpoint to each valid peak. It then checks if that bearing falls within the bounds of the user's specific magnetic sector slices (accounting for local magnetic declination).
4. **Controlling Factor Identification:** Within each sector, the tool competes the highest verified terrain peak (MSL) against the highest verified obstacle (MSL). The absolute highest value becomes the "Controlling Factor."
5. **Safety Padding:** * A **100-foot pad** is added to the Controlling Factor to account for undocumented vegetation and minor unmapped structural variances (TERPS standard).
    * A **1,000-foot IFR buffer** is added to the padded elevation to guarantee standard instrument clearance.
6. **Altitude Rounding:** The final sum is mathematically rounded up to the next highest 100-foot increment to generate the final MSA.

*Formula: `Final MSA = RoundUp100( Max(Obstacle_MSL, Terrain_MSL) + 100' + 1000' )`*

---

## Usage Instructions

### 1. Define Location & Radius
* Input an FAA Facility Identifier (e.g., `KRWI`) or precise Latitude/Longitude coordinates (Decimal or DMS formats accepted).
* Set the desired action radius (in Nautical Miles).

### 2. Configure Sectors
* **Single Sector:** Generates a standard 360° MSA ring.
* **Custom Sectors:** Toggle the EFB switch to enable custom sector boundaries. Drag the radial handles on the visual wheel to define up to 4 specific headings. The tool will independently calculate the MSA, controlling obstacle/terrain, and closest ATC frequency for each distinct slice.

### 3. Audit & Preview
* Review the "Calculation Audit" section to verify the exact coordinates and elevation of the controlling factor for each sector.
* Click **Preview on Map** to view the magnetic sector boundaries and controlling obstacle/terrain markers overlaid on VFR Sectional, Satellite, or Street maps to visually confirm clearance prior to printing.

### 4. Customization & Export
* Click **Export .PDF** to enter the Kneeboard layout mode.
* Text boxes and MSA labels can be dragged into ideal positions to prevent visual overlapping.
* Company logos, scale sliders, and emergency instructions can be customized via the left sidebar.
* Click **Print Card** to generate the final physical kneeboard printout to be placed in the aircraft, or **Save Template** to download a `.json` file of your custom layout for future use.

---

*Disclaimer: This tool is strictly designed to assist pilots in pre-flight planning and the development of local IIMC procedures. The pilot in command remains solely responsible for verifying all altitudes, frequencies, and headings against current, official flight information publications prior to flight.*
