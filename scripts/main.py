from fastapi import FastAPI
from msa_calculator import calculate_msa

app = FastAPI()

@app.get("/api/get-msa")
def get_msa_endpoint(lat: float, lon: float, radius: int = 30):
    """
    API Endpoint to calculate the MSA.
    Example usage: http://localhost:8000/api/get-msa?lat=35.8563&lon=-77.8918&radius=30
    """
    try:
        # Run the calculation
        result = calculate_msa(lat, lon, radius_nm=radius)
        
        # Return the data to the frontend
        return {
            "status": "success",
            "centerpoint": {"lat": lat, "lon": lon},
            "radius_nm": radius,
            "data": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}