import math
import py3dep
import geopandas as gpd
from shapely.geometry import box

def get_bounding_box(lat, lon, radius_nm):
    """Calculates a coordinate bounding box for a given centerpoint and radius."""
    radius_km = radius_nm * 1.852
    lat_change = radius_km / 111.32
    lon_change = radius_km / (111.32 * math.cos(math.radians(lat)))
    
    min_lat = lat - lat_change
    max_lat = lat + lat_change
    min_lon = lon - lon_change
    max_lon = lon + lon_change
    
    return min_lon, min_lat, max_lon, max_lat

def get_highest_terrain(min_lon, min_lat, max_lon, max_lat):
    """Queries the USGS 3DEP API for the highest terrain in the bounding box."""
    geom = box(min_lon, min_lat, max_lon, max_lat)
    geo_df = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326")
    
    # Fetch DEM at 30-meter resolution
    dem = py3dep.get_map("DEM", geo_df.geometry[0], resolution=30, geo_crs="EPSG:4326")
    
    # Convert highest point from meters to feet
    max_meters = float(dem.max())
    return max_meters * 3.28084

def calculate_msa(lat, lon, radius_nm=30, safety_buffer=1000):
    """Calculates final MSA based on terrain and obstacles."""
    min_lon, min_lat, max_lon, max_lat = get_bounding_box(lat, lon, radius_nm)
    
    # 1. Get Terrain
    max_terrain_ft = get_highest_terrain(min_lon, min_lat, max_lon, max_lat)
    
    # 2. Get Obstacles (Placeholder for your DOF logic)
    max_obstacle_ft = 0 
    
    # 3. Determine highest point, add buffer, and round up to nearest 100
    controlling_elevation = max(max_terrain_ft, max_obstacle_ft)
    raw_msa = controlling_elevation + safety_buffer
    final_msa = math.ceil(raw_msa / 100) * 100
    
    return {
        "max_terrain_ft": round(max_terrain_ft, 1),
        "max_obstacle_ft": round(max_obstacle_ft, 1),
        "calculated_msa": final_msa
    }