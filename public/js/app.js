let globalAirports = {};
let globalObstacles = [];

window.onload = async () => {
    try {
        const aptRes = await fetch('airports.json');
        globalAirports = await aptRes.json();
        console.log(`Loaded ${Object.keys(globalAirports).length} airports.`);

        const obsRes = await fetch('obstacles.json');
        globalObstacles = await obsRes.json();
        console.log(`Loaded ${globalObstacles.length} obstacles.`);

        // The button is now correctly plugged in here
        document.getElementById('generate-btn').addEventListener('click', generateIIMCCard);
    } catch (e) {
        console.error("Critical: Database load failed. Make sure you are running a local server.", e);
    }
};

function haversineNM(lat1, lon1, lat2, lon2) {
    const R = 3440.065; 
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

async function getPeakTerrain(lat, lon, radiusNM) {
    const degPerNM = 1 / 60;
    const offset = radiusNM * degPerNM;
    
    const samples = [
        {lat: lat, lon: lon},
        {lat: lat + offset, lon: lon},
        {lat: lat - offset, lon: lon},
        {lat: lat, lon: lon + offset},
        {lat: lat, lon: lon - offset},
        {lat: lat + (offset * 0.7), lon: lon + (offset * 0.7)},
        {lat: lat - (offset * 0.7), lon: lon - (offset * 0.7)},
        {lat: lat + (offset * 0.7), lon: lon - (offset * 0.7)},
        {lat: lat - (offset * 0.7), lon: lon + (offset * 0.7)}
    ];

    try {
        const requests = samples.map(p => 
            fetch(`https://epqs.nationalmap.gov/v1/json?x=${p.lon}&y=${p.lat}&units=Feet&output=json`)
            .then(res => res.json())
        );
        const results = await Promise.all(requests);
        return Math.max(...results.map(r => parseFloat(r.value) || 0));
    } catch (e) {
        console.error("USGS API Failure:", e);
        return 0;
    }
}

async function generateIIMCCard() {
    let id = document.getElementById('centerpoint').value.toUpperCase().trim();
    const radius = parseFloat(document.getElementById('radius').value);
    
    let center = globalAirports[id];
    if (!center && id.startsWith('K') && id.length === 4) {
        center = globalAirports[id.substring(1)];
    }
    
    if (!center) {
        alert(`Identifier "${id}" not found.`);
        return;
    }

    console.log(`--- NEW SEARCH: ${id} ---`);
    console.log(`Center Coordinates: Lat ${center.lat}, Lon ${center.lon}`);

    let maxObsMSL = 0;
    let obsFoundCount = 0;
    
    globalObstacles.forEach(obs => {
        const dist = haversineNM(center.lat, center.lon, obs.lat, obs.lon);
        if (dist <= radius) {
            obsFoundCount++;
            const obsHeight = obs.msl || 0;
            if (obsHeight > maxObsMSL) maxObsMSL = obsHeight;
        }
    });

    console.log(`Obstacles found within ${radius} NM: ${obsFoundCount}`);
    console.log(`Highest Obstacle MSL found: ${maxObsMSL}`);

    const maxTerrMSL = await getPeakTerrain(center.lat, center.lon, radius);
    console.log(`Highest Terrain MSL found: ${maxTerrMSL}`);

    const peak = Math.max(maxObsMSL, maxTerrMSL);
    const rawMSA = peak + 1000;
    const finalMSA = Math.ceil(rawMSA / 100) * 100;

    document.getElementById('prev-location').value = id;
    document.getElementById('prev-msa').value = finalMSA;
    document.getElementById('prev-radius').value = radius;
    
    const d = new Date();
    d.setDate(d.getDate() + 56);
    document.getElementById('prev-expires').value = d.toLocaleDateString('en-GB', {day:'2-digit', month:'short', year:'2-digit'}).toUpperCase();
    
    console.log(`Final Calculated MSA: ${finalMSA}`);
    console.log(`-----------------------`);
}