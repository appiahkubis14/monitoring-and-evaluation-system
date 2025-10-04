// Global variables initialization
// Global variables initialization
let map;
let farmLayers = L.featureGroup();
let farmsData = [];
let currentFarmId = null;
let drawControl;
let editingLayer = null;
let currentPolygon = null;
let isFullScreen = false;
let originalMapPosition = null;

let searchTimeout;
let currentSearchQuery = '';
let highlightedFarm = null;

// Tile layers
let satelliteLayer, streetLayer, hybridLayer, terrainLayer;

// New layers for additional features
let treeDensityLayer = L.featureGroup();
let cropHealthLayer = L.featureGroup();
let irrigationLayer = L.featureGroup();
let soilTypeLayer = L.featureGroup();
let climateZoneLayer = L.featureGroup();
let roadsLayer = L.featureGroup();
let bufferLayer = L.featureGroup();

// Measurement variables
let currentMode = null;
let measuring = false;
let measurePoints = [];
let tempLine = null;
let tempPolygon = null;
let finishedMeasurements = null;


// Make sure to call this when initializing the map - FIXED VERSION
function initializeTreeLayer() {
    if (!window.treeIconsLayer) {
        window.treeIconsLayer = L.layerGroup();
        // Make sure to add it to the map immediately
        window.treeIconsLayer.addTo(map);
    }
    return window.treeIconsLayer;
}

// Function to clear tree icons - FIXED VERSION
function clearTreeIcons() {
    if (window.treeIconsLayer) {
        window.treeIconsLayer.clearLayers();
    } else {
        // If it doesn't exist, initialize it
        initializeTreeLayer();
    }
}

// Add beautiful tree icon - FIXED VERSION
function addTreeIcon(coords, farm) {
    // Ensure tree layer exists
    if (!window.treeIconsLayer) {
        initializeTreeLayer();
    }
    
    // Create custom tree icon with nice tree-like appearance
    const treeSize = 16 + Math.random() * 8; // Random size between 16-24px
    const treeColor = getTreeColor(farm);
    
    const treeIcon = L.divIcon({
        html: `
            <div style="
                width: ${treeSize}px;
                height: ${treeSize}px;
                position: relative;
                transform: translate(-50%, -50%);
            ">
                <!-- Tree trunk -->
                <div style="
                    position: absolute;
                    bottom: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: ${treeSize * 0.2}px;
                    height: ${treeSize * 0.4}px;
                    background: #8B4513;
                    border-radius: 1px;
                    z-index: 1;
                "></div>
                <!-- Tree crown -->
                <div style="
                    position: absolute;
                    top: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: ${treeSize * 0.8}px;
                    height: ${treeSize * 0.6}px;
                    background: ${treeColor};
                    border-radius: 50% 50% 40% 40%;
                    box-shadow: 0 0 2px rgba(0,0,0,0.3);
                    z-index: 2;
                "></div>
            </div>
        `,
        className: 'tree-icon',
        iconSize: [treeSize, treeSize],
        iconAnchor: [treeSize / 2, treeSize]
    });
    
    const treeMarker = L.marker(coords, {
        icon: treeIcon,
        zIndexOffset: 1000,
        farmId: farm.id,
        interactive: false // Make trees non-clickable
    });
    
    // Safely add to tree icons layer
    try {
        window.treeIconsLayer.addLayer(treeMarker);
    } catch (error) {
        console.error('Error adding tree icon:', error);
        // If there's still an issue, create the layer and try again
        initializeTreeLayer();
        window.treeIconsLayer.addLayer(treeMarker);
    }
}

// Update the map initialization to ensure tree layer is created
function initializeMap() {
    // Create map centered on Ghana
    map = L.map('map').setView([7.9465, -1.0232], 7);

    // Initialize tile layers
    streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    });

    satelliteLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; Google Satellite'
    });

    hybridLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; Google Satellite'
    });

    terrainLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        maxZoom: 17,
        attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> contributors'
    });

    // Add default layers
    hybridLayer.addTo(map);

    // Initialize all layer groups - MAKE SURE TREE LAYER IS INITIALIZED HERE
    farmLayers.addTo(map);
    
    // Initialize tree icons layer before other layers
    initializeTreeLayer();
    
    treeDensityLayer.addTo(map);
    cropHealthLayer.addTo(map);
    irrigationLayer.addTo(map);
    soilTypeLayer.addTo(map);
    climateZoneLayer.addTo(map);
    roadsLayer.addTo(map);
    bufferLayer.addTo(map);

    // Hide additional layers by default
    treeDensityLayer.removeFrom(map);
    cropHealthLayer.removeFrom(map);
    irrigationLayer.removeFrom(map);
    soilTypeLayer.removeFrom(map);
    climateZoneLayer.removeFrom(map);
    roadsLayer.removeFrom(map);

    // Initialize measurement layers
    if (!finishedMeasurements) {
        finishedMeasurements = L.featureGroup().addTo(map);
    }

    // Add scale control
    L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);

    // Initialize measurement tools
    initMeasurement();

    // Load farm data
    loadFarmData();

    initializeAllDataLayers();

    // Load additional layers data
    loadTreeDensityData();
    
    // Load crop health data
    loadCropHealthData();
    
    // Load irrigation data
    loadIrrigationData();
    
    // Load environmental data
    loadEnvironmentalData();

    // Setup event listeners
    setupEventListeners();

    // Initialize panel sections
    initializePanelSections();

    initializeOpacityControls();
}

// Tree Density Data
// Base API URL
const API_BASE_URL = '/api';

// Updated load functions using AJAX
async function loadTreeDensityData() {
    try {
        const response = await fetch(`${API_BASE_URL}/tree-density/`);
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(point => {
                const color = point.density === 'high' ? '#006400' : 
                             point.density === 'medium' ? '#32CD32' : '#90EE90';
                
                const marker = L.circleMarker([point.lat, point.lng], {
                    radius: 6,
                    fillColor: color,
                    color: '#fff',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindPopup(`
                    <div class="tree-density-popup">
                        <strong>Tree Density:</strong> ${point.density}<br>
                        <strong>Trees/Hectare:</strong> ${point.trees_per_hectare}<br>
                        <strong>Region:</strong> ${point.region}
                    </div>
                `);

                treeDensityLayer.addLayer(marker);
            });
            console.log(`Loaded ${data.data.length} tree density points from database`);
        }
    } catch (error) {
        console.error('Error loading tree density data:', error);
    }
}

async function loadCropHealthData() {
    try {
        const response = await fetch(`${API_BASE_URL}/crop-health/`);
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(point => {
                const color = point.ndvi > 0.7 ? '#006400' : 
                             point.ndvi > 0.5 ? '#32CD32' : 
                             point.ndvi > 0.3 ? '#FFD700' : '#FF4500';
                
                const marker = L.circleMarker([point.lat, point.lng], {
                    radius: 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                }).bindPopup(`
                    <div class="crop-health-popup">
                        <strong>NDVI:</strong> ${point.ndvi}<br>
                        <strong>Health:</strong> ${point.health}<br>
                        <strong>Region:</strong> ${point.region}
                    </div>
                `);

                cropHealthLayer.addLayer(marker);
            });
            console.log(`Loaded ${data.data.length} crop health points from database`);
        }
    } catch (error) {
        console.error('Error loading crop health data:', error);
    }
}

async function loadIrrigationData() {
    try {
        const response = await fetch(`${API_BASE_URL}/irrigation-sources/`);
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(source => {
                const icon = L.divIcon({
                    className: 'irrigation-icon',
                    html: `<div style="background-color: #1E90FF; width: 18px; height: 18px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center;">
                              <i class="fas fa-tint" style="color: white; font-size: 9px;"></i>
                           </div>`,
                    iconSize: [18, 18]
                });

                const marker = L.marker([source.lat, source.lng], { icon: icon })
                    .bindPopup(`
                        <div class="irrigation-popup">
                            <strong>Type:</strong> ${source.type}<br>
                            <strong>Capacity:</strong> ${source.capacity}<br>
                            <strong>Region:</strong> ${source.region}
                        </div>
                    `);

                irrigationLayer.addLayer(marker);
            });
            console.log(`Loaded ${data.data.length} irrigation sources from database`);
        }
    } catch (error) {
        console.error('Error loading irrigation data:', error);
    }
}

async function loadEnvironmentalData() {
    await loadSoilData();
    await loadClimateData();
    await loadRoadData();
}

async function loadSoilData() {
    try {
        const response = await fetch(`${API_BASE_URL}/soil-types/`);
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(soil => {
                const color = soil.type.includes('Loamy') ? '#8B4513' : 
                             soil.type.includes('Clay') ? '#654321' :
                             soil.type.includes('Sandy Loam') ? '#F4A460' : '#DEB887';
                
                const polygon = L.polygon(soil.coords, {
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.25,
                    weight: 1,
                    opacity: 0.7
                }).bindPopup(`
                    <div class="soil-popup">
                        <strong>Soil Type:</strong> ${soil.type}<br>
                        <strong>Fertility:</strong> ${soil.fertility}<br>
                        <strong>Region:</strong> ${soil.region}
                    </div>
                `);

                soilTypeLayer.addLayer(polygon);
            });
            console.log(`Loaded ${data.data.length} soil type areas from database`);
        }
    } catch (error) {
        console.error('Error loading soil data:', error);
    }
}

async function loadClimateData() {
    try {
        const response = await fetch(`${API_BASE_URL}/climate-zones/`);
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(zone => {
                const color = zone.zone.includes('Tropical Wet') ? '#006400' :
                             zone.zone.includes('Tropical Dry') ? '#FFD700' :
                             zone.zone.includes('Coastal Savannah') ? '#90EE90' : '#32CD32';
                
                const polygon = L.polygon(zone.coords, {
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.15,
                    weight: 2,
                    dashArray: '5, 5',
                    opacity: 0.6
                }).bindPopup(`
                    <div class="climate-popup">
                        <strong>Climate Zone:</strong> ${zone.zone}<br>
                        <strong>Rainfall:</strong> ${zone.rainfall}<br>
                        <strong>Region:</strong> ${zone.region}
                    </div>
                `);

                climateZoneLayer.addLayer(polygon);
            });
            console.log(`Loaded ${data.data.length} climate zones from database`);
        }
    } catch (error) {
        console.error('Error loading climate data:', error);
    }
}

async function loadRoadData() {
    try {
        const response = await fetch(`${API_BASE_URL}/road-network/`);
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(road => {
                const color = road.type === 'primary_highway' ? '#FF0000' : 
                             road.type === 'secondary_road' ? '#FFA500' : '#FFFF00';
                const weight = road.type === 'primary_highway' ? 4 : 
                              road.type === 'secondary_road' ? 3 : 2;
                
                const polyline = L.polyline(road.coords, {
                    color: color,
                    weight: weight,
                    opacity: 0.8
                }).bindPopup(`
                    <div class="road-popup">
                        <strong>Road Type:</strong> ${road.type}<br>
                        <strong>Condition:</strong> ${road.condition}<br>
                        <strong>Name:</strong> ${road.name || 'Unnamed Road'}
                    </div>
                `);

                roadsLayer.addLayer(polyline);
            });
            console.log(`Loaded ${data.data.length} road segments from database`);
        }
    } catch (error) {
        console.error('Error loading road data:', error);
    }
}

// Initialize all data layers from database
async function initializeAllDataLayers() {
    console.log('Loading agricultural data from database...');
    
    await loadTreeDensityData();
    await loadCropHealthData();
    await loadIrrigationData();
    await loadEnvironmentalData();
    
    console.log('All agricultural data loaded from database');
}





// Buffer Analysis Functions
// Buffer Analysis Functions - Enhanced for multiple independent buffers
let activeBuffers = new Map(); // Track active buffers by type

function createBufferAroundIrrigation() {
    const bufferDistance = parseInt(document.getElementById('bufferDistance').value) || 1000;
    
    // Remove existing irrigation buffer if it exists
    if (activeBuffers.has('irrigation')) {
        removeBuffer('irrigation');
    }
    
    const irrigationBuffers = L.featureGroup();
    let bufferCount = 0;
    
    // Create buffer around each irrigation source
    irrigationLayer.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            const center = layer.getLatLng();
            const buffer = L.circle(center, {
                radius: bufferDistance,
                color: '#1E90FF',
                fillColor: '#1E90FF',
                fillOpacity: 0.25,
                weight: 3,
                className: 'buffer-layer irrigation-buffer'
            }).bindPopup(`
                <div class="buffer-popup">
                    <strong>🚰 Irrigation Buffer</strong><br>
                    <strong>Distance:</strong> ${bufferDistance}m<br>
                    <strong>Farms within buffer:</strong> ${countFarmsInBuffer(center, bufferDistance)}<br>
                    <strong>Source Type:</strong> ${layer.getPopup() ? layer.getPopup().getContent().match(/Type:.*?(?=<br>)/)?.[0]?.replace('Type:', '').trim() : 'Unknown'}
                </div>
            `);
            
            irrigationBuffers.addLayer(buffer);
            bufferCount++;
        }
    });
    
    if (bufferCount > 0) {
        activeBuffers.set('irrigation', {
            layer: irrigationBuffers,
            distance: bufferDistance,
            count: bufferCount
        });
        
        map.addLayer(irrigationBuffers);
        showToast(`Created ${bufferCount} irrigation buffers (${bufferDistance}m)`, 'success');
        updateBufferLegend();
    } else {
        showToast('No irrigation sources found to create buffers', 'warning');
    }
}


// Using Turf.js for proper buffer calculations (recommended)
function createBufferAroundRoads() {
    const bufferDistance = parseInt(document.getElementById('bufferDistance').value) || 1000;
    
    // Remove existing roads buffer if it exists
    if (activeBuffers.has('roads')) {
        removeBuffer('roads');
    }
    
    const roadBuffers = L.featureGroup();
    let bufferCount = 0;
    
    // Check if Turf.js is available
    if (typeof turf === 'undefined') {
        showToast('Turf.js library required for advanced buffer analysis', 'error');
        return;
    }
    
    roadsLayer.eachLayer(layer => {
        if (layer instanceof L.Polyline) {
            const latlngs = layer.getLatLngs();
            
            // Convert to GeoJSON LineString
            const coordinates = latlngs.map(latlng => [latlng.lng, latlng.lat]);
            const lineString = turf.lineString(coordinates);
            
            // Create buffer using Turf
            const buffer = turf.buffer(lineString, bufferDistance / 1000, { units: 'kilometers' });
            
            // Convert back to Leaflet polygon
            const bufferPolygon = L.geoJSON(buffer, {
                style: {
                    color: '#FF6B35',
                    fillColor: '#FF6B35',
                    fillOpacity: 0.25,
                    weight: 2,
                    className: 'buffer-layer road-buffer'
                }
            }).bindPopup(`
                <div class="buffer-popup">
                    <strong>🛣️ Road Buffer</strong><br>
                    <strong>Distance:</strong> ${bufferDistance}m<br>
                    <strong>Road Type:</strong> ${layer.getPopup() ? layer.getPopup().getContent().match(/Road Type:.*?(?=<br>)/)?.[0]?.replace('Road Type:', '').trim() : 'Unknown'}<br>
                    <strong>Buffer Area:</strong> ${turf.area(buffer).toFixed(2)} m²
                </div>
            `);
            
            roadBuffers.addLayer(bufferPolygon);
            bufferCount++;
        }
    });
    
    if (bufferCount > 0) {
        activeBuffers.set('roads', {
            layer: roadBuffers,
            distance: bufferDistance,
            count: bufferCount
        });
        
        map.addLayer(roadBuffers);
        showToast(`Created ${bufferCount} road buffers (${bufferDistance}m)`, 'success');
        updateBufferLegend();
    } else {
        showToast('No roads found to create buffers', 'warning');
    }
}




// New function to create buffer around farms based on status
function createBufferAroundFarms() {
    const bufferDistance = parseInt(document.getElementById('bufferDistance').value) || 1000;
    
    // Remove existing farm buffer if it exists
    if (activeBuffers.has('farms')) {
        removeBuffer('farms');
    }
    
    const farmBuffers = L.featureGroup();
    let bufferCount = 0;
    
    // Create buffers around farms with status-based colors
    farmLayers.eachLayer(layer => {
        if (layer.options && layer.options.farmData) {
            const farm = layer.options.farmData;
            const center = layer.getBounds ? layer.getBounds().getCenter() : layer.getLatLng();
            
            const statusColors = {
                'active': '#28a745',
                'delayed': '#ffc107', 
                'critical': '#dc3545',
                'completed': '#17a2b8',
                'abandoned': '#6c757d'
            };
            
            const bufferColor = statusColors[farm.status] || '#6c757d';
            
            const buffer = L.circle(center, {
                radius: bufferDistance,
                color: bufferColor,
                fillColor: bufferColor,
                fillOpacity: 0.15,
                weight: 2,
                className: 'buffer-layer farm-buffer'
            }).bindPopup(`
                <div class="buffer-popup">
                    <strong>🏠 Farm Buffer</strong><br>
                    <strong>Farm:</strong> ${farm.name}<br>
                    <strong>Status:</strong> ${farm.status}<br>
                    <strong>Buffer Distance:</strong> ${bufferDistance}m<br>
                    <strong>Nearby Farms:</strong> ${countNearbyFarms(center, bufferDistance, farm.id)}
                </div>
            `);
            
            farmBuffers.addLayer(buffer);
            bufferCount++;
        }
    });
    
    if (bufferCount > 0) {
        activeBuffers.set('farms', {
            layer: farmBuffers,
            distance: bufferDistance,
            count: bufferCount
        });
        
        map.addLayer(farmBuffers);
        showToast(`Created ${bufferCount} farm buffers (${bufferDistance}m)`, 'success');
        updateBufferLegend();
    }
}

// New function to create gradient buffer (multiple distances)
function createGradientBuffer() {
    const baseDistance = parseInt(document.getElementById('bufferDistance').value) || 1000;
    
    // Remove existing gradient buffer if it exists
    if (activeBuffers.has('gradient')) {
        removeBuffer('gradient');
    }
    
    const gradientBuffers = L.featureGroup();
    const gradients = [500, 1000, 2000, 5000]; // Multiple buffer distances
    const gradientColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']; // Different colors for each distance
    
    irrigationLayer.eachLayer((layer, index) => {
        if (layer instanceof L.Marker && index < 5) { // Limit to first 5 for performance
            const center = layer.getLatLng();
            
            gradients.forEach((distance, i) => {
                const buffer = L.circle(center, {
                    radius: distance,
                    color: gradientColors[i],
                    fillColor: gradientColors[i],
                    fillOpacity: 0.1 + (i * 0.05), // Increasing opacity
                    weight: 1,
                    className: 'buffer-layer gradient-buffer'
                }).bindPopup(`
                    <div class="buffer-popup">
                        <strong>🌈 Gradient Buffer</strong><br>
                        <strong>Distance:</strong> ${distance}m<br>
                        <strong>Opacity:</strong> ${Math.round((0.1 + (i * 0.05)) * 100)}%<br>
                        <strong>Farms in zone:</strong> ${countFarmsInBuffer(center, distance)}
                    </div>
                `);
                
                gradientBuffers.addLayer(buffer);
            });
        }
    });
    
    if (gradientBuffers.getLayers().length > 0) {
        activeBuffers.set('gradient', {
            layer: gradientBuffers,
            distance: baseDistance,
            count: gradients.length
        });
        
        map.addLayer(gradientBuffers);
        showToast(`Created gradient buffers around irrigation sources`, 'info');
        updateBufferLegend();
    }
}

// Helper function to count nearby farms (excluding current farm)
function countNearbyFarms(center, distance, excludeFarmId) {
    let count = 0;
    farmLayers.eachLayer(layer => {
        if (layer.options && layer.options.farmData && layer.options.farmData.id !== excludeFarmId) {
            const farmCenter = layer.getBounds ? layer.getBounds().getCenter() : layer.getLatLng();
            if (center.distanceTo(farmCenter) <= distance) {
                count++;
            }
        }
    });
    return count;
}

function countFarmsInBuffer(center, distance) {
    let count = 0;
    farmLayers.eachLayer(layer => {
        if (layer.getLatLng && center.distanceTo(layer.getLatLng()) <= distance) {
            count++;
        } else if (layer.getBounds && layer.getBounds().getCenter().distanceTo(center) <= distance) {
            count++;
        }
    });
    return count;
}

// Remove specific buffer type
function removeBuffer(bufferType) {
    if (activeBuffers.has(bufferType)) {
        const buffer = activeBuffers.get(bufferType);
        map.removeLayer(buffer.layer);
        activeBuffers.delete(bufferType);
        showToast(`Removed ${bufferType} buffers`, 'info');
        updateBufferLegend();
    }
}

// Clear all buffers
function clearBufferAnalysis() {
    activeBuffers.forEach((buffer, type) => {
        map.removeLayer(buffer.layer);
    });
    activeBuffers.clear();
    showToast('All buffers cleared', 'info');
    updateBufferLegend();
}

// Update buffer legend in the UI
function updateBufferLegend() {
    const legendSection = document.getElementById('legend-section');
    let bufferLegendHtml = '';
    
    if (activeBuffers.size > 0) {
        bufferLegendHtml += '<div class="legend-divider mt-2 mb-2"></div>';
        bufferLegendHtml += '<h6 class="legend-subtitle">Active Buffers</h6>';
        
        activeBuffers.forEach((buffer, type) => {
            const colors = {
                'irrigation': '#1E90FF',
                'roads': '#FF6B35', 
                'farms': '#28a745',
                'gradient': 'linear-gradient(45deg, #FF6B6B, #96CEB4)'
            };
            
            const icons = {
                'irrigation': '🚰',
                'roads': '🛣️',
                'farms': '🏠',
                'gradient': '🌈'
            };
            
            const names = {
                'irrigation': 'Irrigation Buffers',
                'roads': 'Road Buffers',
                'farms': 'Farm Buffers',
                'gradient': 'Gradient Buffers'
            };
            
            bufferLegendHtml += `
                <div class="legend-item d-flex align-items-center mb-1 buffer-legend-item" data-buffer-type="${type}">
                    <div class="legend-color" style="background: ${colors[type]}; ${type === 'gradient' ? 'background: linear-gradient(45deg, #FF6B6B, #96CEB4);' : ''}"></div>
                    <small>${icons[type]} ${names[type]}</small>
                    <button class="btn-close btn-close-sm ms-auto" onclick="removeBuffer('${type}')" style="font-size: 0.6rem;"></button>
                </div>
                <div class="legend-detail ms-3">
                    <small class="text-muted">${buffer.count} zones • ${buffer.distance}m</small>
                </div>
            `;
        });
    }
    
    // Add or update buffer legend
    const existingBufferLegend = document.getElementById('buffer-legend');
    if (existingBufferLegend) {
        existingBufferLegend.innerHTML = bufferLegendHtml;
    } else {
        const bufferLegend = document.createElement('div');
        bufferLegend.id = 'buffer-legend';
        bufferLegend.innerHTML = bufferLegendHtml;
        legendSection.appendChild(bufferLegend);
    }
}

// Measurement variables
let measureControl;
let isMeasuring = false;
let currentMeasureType = null;

// Initialize measurement tools
function initializeMeasurementTools() {
    // Create custom measurement control
    measureControl = L.control({ position: 'topright' });
    
    measureControl.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'measure-control');
        div.innerHTML = `
            <div class="btn-group-vertical" role="group">
                <button type="button" class="btn btn-success btn-sm" id="measureDistanceBtn" title="Measure Distance">
                    <i class="fas fa-ruler"></i>
                </button>
                <button type="button" class="btn btn-info btn-sm" id="measureAreaBtn" title="Measure Area">
                    <i class="fas fa-draw-polygon"></i>
                </button>
                <button type="button" class="btn btn-secondary btn-sm" id="clearMeasurementsBtn" title="Clear Measurements" style="display: none;">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        return div;
    };
    
    measureControl.addTo(map);

    // Add measurement results display
    const measureResults = L.control({ position: 'topright' });
    measureResults.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'measure-results');
        div.innerHTML = `
            <div class="measurement-info" id="measurementInfo" style="display: none;">
                <div class="card">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1">Measurement</h6>
                        <div id="distanceResult" class="measure-result"></div>
                        <div id="areaResult" class="measure-result"></div>
                        <small class="text-muted">Click to start, double-click to end</small>
                    </div>
                </div>
            </div>
        `;
        return div;
    };
    measureResults.addTo(map);

    // Setup measurement event listeners
    setupMeasurementEvents();
}




// Initialize measurement functionality with DOM ready check
function initMeasurement() {
    // Ensure finishedMeasurements is initialized
    if (!finishedMeasurements) {
        finishedMeasurements = L.featureGroup().addTo(map);
    }
    
    // Wait a bit for DOM to be fully ready
    setTimeout(() => {
        setupMeasurementEventListeners();
    }, 100);
}

 // Calculate area using the shoelace formula
    // Calculate area using the shoelace formula
    function calculateArea(latLngs) {
        if (!latLngs || latLngs.length < 3) return 0;

        let area = 0;
        const n = latLngs.length;

        for (let i = 0; i < n; i++) {
            const j = (i + 1) % n;
            area += latLngs[i].lng * latLngs[j].lat;
            area -= latLngs[j].lng * latLngs[i].lat;
        }

        area = Math.abs(area) / 2;

        // Calculate center point from latLngs
        let sumLat = 0;
        let sumLng = 0;

        for (let i = 0; i < n; i++) {
            sumLat += latLngs[i].lat;
            sumLng += latLngs[i].lng;
        }

        const centerLat = sumLat / n;
        const centerLng = sumLng / n;

        // Convert to square meters (approximate)
        // This is a simplified conversion that works reasonably well for small areas
        const metersPerDegree = 111319.9 * Math.cos(centerLat * Math.PI / 180);
        return area * metersPerDegree * metersPerDegree;
    }


// Separate function for setting up event listeners
function setupMeasurementEventListeners() {
    const distanceBtn = document.getElementById('measureDistanceTool');
    const areaBtn = document.getElementById('measureAreaTool');
    const clearBtn = document.getElementById('clearMeasurementsTool');

    if (!distanceBtn || !areaBtn) {
        console.error('Measurement buttons not found in DOM');
        return;
    }
    
    distanceBtn.addEventListener('click', function (e) {
        e.preventDefault();
        if (currentMode === 'distance' && measuring) {
            finishMeasurement();
        } else {
            startDistanceMeasurement();
        }
    });

    areaBtn.addEventListener('click', function (e) {
        e.preventDefault();
        if (currentMode === 'area' && measuring) {
            finishMeasurement();
        } else {
            startAreaMeasurement();
        }
    });

    // Only add clear listener if button exists
    if (clearBtn) {
        clearBtn.addEventListener('click', clearAllMeasurements);
    }
    
    console.log('Measurement event listeners set up successfully');
}



// Safe layer management functions
function safeAddToMap(layer) {
    if (map && layer && typeof layer.addTo === 'function') {
        return layer.addTo(map);
    }
    return null;
}

function safeRemoveFromMap(layer) {
    if (map && layer && typeof map.removeLayer === 'function') {
        return map.removeLayer(layer);
    }
    return null;
}

// Updated clearAllMeasurements with safety check
function clearAllMeasurements() {
    if (finishedMeasurements && typeof finishedMeasurements.clearLayers === 'function') {
        finishedMeasurements.clearLayers();
        showToast('All measurements cleared', 'info');
    } else {
        console.warn('finishedMeasurements not available for clearing');
    }
}

// Create a custom clear icon
function createClearIcon(layer) {
    const bounds = layer.getBounds();
    const icon = L.divIcon({
        className: 'clear-measurement',
        html: '<div class="clear-icon" title="Click to remove measurement">×</div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    const marker = L.marker(bounds.getCenter(), {
        icon: icon,
        interactive: true,
        bubblingMouseEvents: false
    }).addTo(finishedMeasurements);

    marker.on('click', function () {
        finishedMeasurements.removeLayer(layer);
        finishedMeasurements.removeLayer(marker);
        showToast('Measurement removed', 'info');
    });

    return marker;
}

// Start distance measurement
function startDistanceMeasurement() {
    resetMeasurement(); // Clear any temporary measurement

    currentMode = 'distance';
    measuring = true;
    updateButtonStates();

    // Set cursor style
    map.getContainer().style.cursor = 'crosshair';

    // Add event listeners
    map.on('click', addDistancePoint);
    map.on('mousemove', updateTempDistanceLine);
    map.on('dblclick', finishMeasurement);

    showToast('Distance measurement started. Click to add points, double-click to finish.', 'info');
}

// Start area measurement
function startAreaMeasurement() {
    resetMeasurement(); // Clear any temporary measurement

    currentMode = 'area';
    measuring = true;
    updateButtonStates();

    // Set cursor style
    map.getContainer().style.cursor = 'crosshair';

    // Add event listeners
    map.on('click', addAreaPoint);
    map.on('mousemove', updateTempAreaPolygon);
    map.on('dblclick', finishMeasurement);

    showToast('Area measurement started. Click to add points, double-click to finish.', 'info');
}

// Add point for distance measurement
function addDistancePoint(e) {
    measurePoints.push(e.latlng);

    // Create the permanent line after second point
    if (measurePoints.length >= 2) {
        // Remove any existing temporary line
        if (tempLine) {
            map.removeLayer(tempLine);
            tempLine = null;
        }

        const permanentLine = L.polyline(measurePoints, {
            color: '#3388ff',
            weight: 4,
            opacity: 0.8,
            dashArray: '5, 5'
        }).addTo(finishedMeasurements);

        // Add clear icon
        createClearIcon(permanentLine);

        // Update distance display
        updateDistanceDisplay(permanentLine);

        // Show measurement summary
        showMeasurementSummary();
    }
}

// Update temporary distance line during measurement
function updateTempDistanceLine(e) {
    if (measurePoints.length > 0) {
        const tempPoints = [...measurePoints, e.latlng];
        if (!tempLine) {
            tempLine = L.polyline(tempPoints, {
                color: '#3388ff',
                weight: 2,
                dashArray: '3, 6',
                opacity: 0.5
            }).addTo(map);
        } else {
            tempLine.setLatLngs(tempPoints);
        }

        // Update temporary distance display
        if (measurePoints.length >= 1) {
            const tempDistance = measurePoints[measurePoints.length - 1].distanceTo(e.latlng);
            updateTemporaryDisplay(tempDistance, null);
        }
    }
}

// Add point for area measurement
function addAreaPoint(e) {
    measurePoints.push(e.latlng);

    // Create the permanent polygon after third point
    if (measurePoints.length >= 3) {
        // Remove any existing temporary polygon
        if (tempPolygon) {
            map.removeLayer(tempPolygon);
            tempPolygon = null;
        }

        const permanentPolygon = L.polygon([measurePoints], {
            color: '#28a745',
            weight: 3,
            fillColor: '#28a745',
            fillOpacity: 0.2
        }).addTo(finishedMeasurements);

        // Add clear icon
        createClearIcon(permanentPolygon);

        // Update area display
        updateAreaDisplay(permanentPolygon);

        // Show measurement summary
        showMeasurementSummary();
    }
}

// Update temporary area polygon during measurement
function updateTempAreaPolygon(e) {
    if (measurePoints.length > 0) {
        const tempPoints = [...measurePoints, e.latlng];
        if (!tempPolygon) {
            tempPolygon = L.polygon([tempPoints], {
                color: '#28a745',
                weight: 2,
                fillColor: '#28a745',
                fillOpacity: 0.1,
                opacity: 0.5
            }).addTo(map);
        } else {
            tempPolygon.setLatLngs([tempPoints]);
        }

        // Update temporary area display
        if (measurePoints.length >= 2) {
            const tempArea = calculateArea([...measurePoints, e.latlng]);
            updateTemporaryDisplay(null, tempArea);
        }
    }
}

// Finish the current measurement
function finishMeasurement() {
    if (measurePoints.length < (currentMode === 'distance' ? 2 : 3)) {
        // Not enough points for a valid measurement
        showToast('Not enough points for measurement. Add more points.', 'warning');
        return;
    }

    const layers = finishedMeasurements.getLayers();
    const lastLayer = layers[layers.length - 2]; // Get the actual measurement layer (not the clear icon)
    
    if (lastLayer) {
        if (currentMode === 'distance') {
            const distance = calculateTotalDistance(lastLayer.getLatLngs());
            showToast(`Distance measurement completed: ${formatDistance(distance)}`, 'success');
        } else {
            const area = calculateArea(lastLayer.getLatLngs()[0]);
            showToast(`Area measurement completed: ${formatArea(area)}`, 'success');
        }
    }

    resetMeasurement();
}

// Remove last point
function removeLastPoint() {
    if (measurePoints.length > 0) {
        measurePoints.pop();

        if (currentMode === 'distance') {
            if (tempLine) {
                if (measurePoints.length === 0) {
                    map.removeLayer(tempLine);
                    tempLine = null;
                } else {
                    const tempPoints = [...measurePoints];
                    if (tempLine) tempLine.setLatLngs(tempPoints);
                }
            }

            // Update the last permanent line if it exists
            const layers = finishedMeasurements.getLayers();
            const lastLine = layers.find(layer => layer instanceof L.Polyline);
            if (lastLine && measurePoints.length >= 2) {
                lastLine.setLatLngs(measurePoints);
                updateDistanceDisplay(lastLine);
            } else if (lastLine && measurePoints.length < 2) {
                finishedMeasurements.removeLayer(lastLine);
                // Also remove the clear icon
                const clearIcon = layers.find(layer => layer instanceof L.Marker);
                if (clearIcon) finishedMeasurements.removeLayer(clearIcon);
            }
        }
        else if (currentMode === 'area') {
            if (tempPolygon) {
                if (measurePoints.length < 2) {
                    map.removeLayer(tempPolygon);
                    tempPolygon = null;
                } else {
                    const tempPoints = [...measurePoints];
                    if (tempPolygon) tempPolygon.setLatLngs([tempPoints]);
                }
            }

            // Update the last permanent polygon if it exists
            const layers = finishedMeasurements.getLayers();
            const lastPolygon = layers.find(layer => layer instanceof L.Polygon);
            if (lastPolygon && measurePoints.length >= 3) {
                lastPolygon.setLatLngs([measurePoints]);
                updateAreaDisplay(lastPolygon);
            } else if (lastPolygon && measurePoints.length < 3) {
                finishedMeasurements.removeLayer(lastPolygon);
                // Also remove the clear icon
                const clearIcon = layers.find(layer => layer instanceof L.Marker);
                if (clearIcon) finishedMeasurements.removeLayer(clearIcon);
            }
        }

        showToast('Last point removed', 'info');
    }
}

// Reset temporary measurement state
function resetMeasurement() {
    measuring = false;
    currentMode = null;
    measurePoints = [];

    // Clear temporary layers
    if (tempLine) {
        map.removeLayer(tempLine);
        tempLine = null;
    }
    if (tempPolygon) {
        map.removeLayer(tempPolygon);
        tempPolygon = null;
    }

    // Reset cursor
    map.getContainer().style.cursor = '';

    // Remove event listeners
    map.off('click');
    map.off('mousemove');
    map.off('dblclick');

    // Hide temporary display
    hideTemporaryDisplay();

    updateButtonStates();
}

// Update distance display for a line
function updateDistanceDisplay(line) {
    const distance = calculateTotalDistance(line.getLatLngs());
    const displayText = formatDistance(distance);

    if (!line.getTooltip()) {
        line.bindTooltip(displayText, {
            permanent: true,
            direction: 'top',
            className: 'measure-tooltip distance-tooltip'
        }).openTooltip();
    } else {
        line.setTooltipContent(displayText);
    }
}

// Update area display for a polygon
function updateAreaDisplay(polygon) {
    const area = calculateArea(polygon.getLatLngs()[0]);
    const displayText = formatArea(area);

    if (!polygon.getTooltip()) {
        polygon.bindTooltip(displayText, {
            permanent: true,
            direction: 'center',
            className: 'measure-tooltip area-tooltip'
        }).openTooltip();
    } else {
        polygon.setTooltipContent(displayText);
    }
}

// Calculate total distance for a polyline
function calculateTotalDistance(latLngs) {
    let totalDistance = 0;
    for (let i = 1; i < latLngs.length; i++) {
        totalDistance += latLngs[i - 1].distanceTo(latLngs[i]);
    }
    return totalDistance;
}

// Format distance for display
function formatDistance(meters) {
    if (meters < 1000) {
        return `${meters.toFixed(1)} m`;
    } else {
        return `${(meters / 1000).toFixed(2)} km`;
    }
}

// Format area for display
function formatArea(squareMeters) {
    if (squareMeters < 10000) {
        return `${squareMeters.toFixed(0)} m²`;
    } else {
        return `${(squareMeters / 10000).toFixed(2)} ha`;
    }
}

// Update button states
// Update button states - FIXED VERSION
function updateButtonStates() {
    // Get the actual button elements from your HTML
    const distanceBtn = document.getElementById('measureDistanceTool');
    const areaBtn = document.getElementById('measureAreaTool');
    
    // Check if buttons exist before trying to modify them
    if (!distanceBtn || !areaBtn) {
        console.warn('Measurement buttons not found in DOM');
        return;
    }

    // Reset all measure buttons
    [distanceBtn, areaBtn].forEach(btn => {
        btn.classList.remove('active', 'btn-warning');
        btn.classList.add('btn-outline-success', 'btn-outline-info');
    });

    // Activate current mode button if measuring
    if (measuring && currentMode) {
        const activeBtn = currentMode === 'distance' ? distanceBtn : areaBtn;
        activeBtn.classList.remove('btn-outline-success', 'btn-outline-info');
        activeBtn.classList.add('btn-warning');
        
        // Update button text
        if (currentMode === 'distance') {
            distanceBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        } else {
            areaBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        }
    } else {
        // Reset button text
        distanceBtn.innerHTML = '<i class="fas fa-ruler"></i> Distance';
        areaBtn.innerHTML = '<i class="fas fa-draw-polygon"></i> Area';
    }
}

// Clear all measurements
function clearAllMeasurements() {
    finishedMeasurements.clearLayers();
    showToast('All measurements cleared', 'info');
}

// Show measurement summary
function showMeasurementSummary() {
    const totalMeasurements = finishedMeasurements.getLayers().filter(layer => 
        layer instanceof L.Polyline || layer instanceof L.Polygon
    ).length;
    
    if (totalMeasurements > 0) {
        console.log(`Total measurements on map: ${totalMeasurements}`);
    }
}

// Update temporary display during measurement
function updateTemporaryDisplay(distance, area) {
    // You can implement a temporary display here if needed
    // This could show the current measurement value near the cursor
}

function hideTemporaryDisplay() {
    // Hide any temporary displays
}


// Initialize opacity controls
function initializeOpacityControls() {
    // Base Map Opacity
    document.getElementById('baseOpacitySlider').addEventListener('input', function(e) {
        const opacity = e.target.value / 100;
        document.getElementById('baseOpacityValue').textContent = `${e.target.value}%`;
        setBaseMapOpacity(opacity);
    });

    // Farm Layers Opacity
    document.getElementById('farmOpacitySlider').addEventListener('input', function(e) {
        const opacity = e.target.value / 100;
        document.getElementById('farmOpacityValue').textContent = `${e.target.value}%`;
        setFarmLayersOpacity(opacity);
    });

    // Environmental Layers Opacity
    document.getElementById('envOpacitySlider').addEventListener('input', function(e) {
        const opacity = e.target.value / 100;
        document.getElementById('envOpacityValue').textContent = `${e.target.value}%`;
        setEnvironmentalLayersOpacity(opacity);
    });

    // Buffer Layers Opacity
    document.getElementById('bufferOpacitySlider').addEventListener('input', function(e) {
        const opacity = e.target.value / 100;
        document.getElementById('bufferOpacityValue').textContent = `${e.target.value}%`;
        setBufferLayersOpacity(opacity);
    });
}

// Opacity control functions
function setBaseMapOpacity(opacity) {
    // Set opacity for all base map layers
    if (hybridLayer) hybridLayer.setOpacity(opacity);
    if (streetLayer) streetLayer.setOpacity(opacity);
    if (satelliteLayer) satelliteLayer.setOpacity(opacity);
    if (terrainLayer) terrainLayer.setOpacity(opacity);
}

function setFarmLayersOpacity(opacity) {
    // Set opacity for farm-related layers
    farmLayers.eachLayer(layer => {
        if (layer instanceof L.Polygon) {
            layer.setStyle({ fillOpacity: opacity * 0.6 });
        } else if (layer instanceof L.CircleMarker) {
            layer.setStyle({ fillOpacity: opacity * 0.8 });
        }
    });
    
    treeDensityLayer.eachLayer(layer => {
        if (layer instanceof L.CircleMarker) {
            layer.setStyle({ fillOpacity: opacity * 0.8 });
        }
    });
    
    cropHealthLayer.eachLayer(layer => {
        if (layer instanceof L.CircleMarker) {
            layer.setStyle({ fillOpacity: opacity * 0.7 });
        }
    });
    
    irrigationLayer.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            // For markers, we might want to adjust icon opacity or leave as is
            const icon = layer.getIcon();
            if (icon && icon.options) {
                // You can implement marker opacity if needed
            }
        }
    });
}

function setEnvironmentalLayersOpacity(opacity) {
    // Set opacity for environmental layers
    soilTypeLayer.eachLayer(layer => {
        if (layer instanceof L.Polygon) {
            layer.setStyle({ fillOpacity: opacity * 0.3 });
        }
    });
    
    climateZoneLayer.eachLayer(layer => {
        if (layer instanceof L.Polygon) {
            layer.setStyle({ fillOpacity: opacity * 0.2 });
        }
    });
    
    roadsLayer.eachLayer(layer => {
        if (layer instanceof L.Polyline) {
            layer.setStyle({ opacity: opacity * 0.8 });
        }
    });
}

function setBufferLayersOpacity(opacity) {
    // Set opacity for all buffer layers
    activeBuffers.forEach((buffer, type) => {
        buffer.layer.eachLayer(layer => {
            if (layer instanceof L.Polygon || layer instanceof L.Circle) {
                layer.setStyle({ fillOpacity: opacity * 0.25 });
            }
        });
    });
}


// Function to switch base maps
function switchBaseMap(selectedMapId) {
    // Remove all base maps first
    [hybridLayer, streetLayer, satelliteLayer, terrainLayer].forEach(layer => {
        if (layer && map.hasLayer(layer)) {
            map.removeLayer(layer);
        }
    });
    
    // Add the selected base map
    switch(selectedMapId) {
        case 'hybridLayer':
            hybridLayer.addTo(map);
            break;
        case 'streetLayer':
            streetLayer.addTo(map);
            break;
        case 'satelliteLayer':
            satelliteLayer.addTo(map);
            break;
        case 'terrainLayer':
            terrainLayer.addTo(map);
            break;
    }
    
    // Apply current opacity
    const opacity = document.getElementById('baseOpacitySlider').value / 100;
    setBaseMapOpacity(opacity);
}


function initializePanelSections() {
    // Set initial active sections
    const layersSection = document.getElementById('layers-section');
    const analysisSection = document.getElementById('analysis-section');
    // const opacitySection = document.getElementById('opacity-section');

    if (layersSection) layersSection.classList.add('active');
    if (analysisSection) analysisSection.classList.add('active');
    // if (opacitySection) opacitySection.classList.add('active');

    // Add click handlers to section headers
    document.querySelectorAll('.section-header').forEach(header => {
        const targetId = header.getAttribute('data-toggle');
        const sectionContent = document.getElementById(targetId);

        if (sectionContent) {
            header.addEventListener('click', function () {
                const isActive = sectionContent.classList.contains('active');
                this.classList.toggle('active');
                sectionContent.classList.toggle('active');
            });
        }
    });

    // Panel toggle functionality
    const togglePanelBtn = document.getElementById('togglePanel');
    if (togglePanelBtn) {
        togglePanelBtn.addEventListener('click', function () {
            const panel = document.querySelector('.map-controls-panel');
            if (panel) {
                panel.classList.toggle('collapsed');
                const icon = this.querySelector('i');
                if (panel.classList.contains('collapsed')) {
                    icon.classList.remove('fa-chevron-left');
                    icon.classList.add('fa-chevron-right');
                } else {
                    icon.classList.remove('fa-chevron-right');
                    icon.classList.add('fa-chevron-left');
                }
            }
        });
    }
}



// Enhanced setupEventListeners function
function setupEventListeners() {
    // Existing event listeners...
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);
    document.getElementById('searchInput').addEventListener('input', handleSearchInput);
    document.getElementById('searchInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') performSearch();
        if (e.key === 'Escape') clearSearch();
    });

    // Base map layers
    document.getElementById('satelliteLayer').addEventListener('change', toggleSatelliteLayer);
    document.getElementById('streetLayer').addEventListener('change', toggleStreetLayer);
    document.getElementById('hybridLayer').addEventListener('change', toggleHybridLayer);
    document.getElementById('terrainLayer').addEventListener('change', toggleTerrainLayer);

    // Farm data layers
    document.getElementById('farmLayer').addEventListener('change', toggleFarmLayer);
    document.getElementById('treeDensityLayer').addEventListener('change', toggleTreeDensityLayer);
    document.getElementById('cropHealthLayer').addEventListener('change', toggleCropHealthLayer);
    document.getElementById('irrigationLayer').addEventListener('change', toggleIrrigationLayer);

    // Environmental layers
    document.getElementById('soilTypeLayer').addEventListener('change', toggleSoilTypeLayer);
    document.getElementById('climateZoneLayer').addEventListener('change', toggleClimateZoneLayer);
    document.getElementById('roadsLayer').addEventListener('change', toggleRoadsLayer);

    // Buffer analysis
    document.getElementById('bufferIrrigationBtn').addEventListener('click', createBufferAroundIrrigation);
    document.getElementById('bufferRoadsBtn').addEventListener('click', createBufferAroundRoads);
    document.getElementById('bufferFarmsBtn').addEventListener('click', createBufferAroundFarms);
    document.getElementById('bufferGradientBtn').addEventListener('click', createGradientBuffer);
    document.getElementById('clearBufferBtn').addEventListener('click', clearBufferAnalysis);

    // Opacity control
    // document.getElementById('opacitySlider').addEventListener('input', function (e) {
    //     const opacity = e.target.value / 100;
    //     document.getElementById('opacityValue').textContent = `${e.target.value}%`;
    //     setFarmLayerOpacity(opacity);
    // });

    // Map tools
    document.getElementById('refreshMap').addEventListener('click', loadFarmData);
    document.getElementById('fitToBounds').addEventListener('click', fitToBounds);
    document.getElementById('clearSelection').addEventListener('click', clearSelection);
    document.getElementById('fullScreenBtn').addEventListener('click', toggleFullScreen);

    // Edit boundary buttons
    document.getElementById('editBoundaryBtn').addEventListener('click', startEditingBoundary);
    document.getElementById('validateBoundaryBtn').addEventListener('click', validateBoundary);
    document.getElementById('saveBoundaryBtn').addEventListener('click', saveBoundaryChanges);
    document.getElementById('cancelEditBtn').addEventListener('click', cancelEditing);

    // Measurement tools
    document.getElementById('measureDistanceTool').addEventListener('click', startDistanceMeasurement);
    document.getElementById('measureAreaTool').addEventListener('click', startAreaMeasurement);
    document.getElementById('clearMeasureTool').addEventListener('click', clearAllMeasurements);

    window.addEventListener('resize', function () {
        if (isFullScreen) {
            setTimeout(() => {
                map.invalidateSize(true);
            }, 100);
        }
    });

    // Base map radio buttons (mutually exclusive)
    document.querySelectorAll('input[name="baseMap"]').forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                switchBaseMap(this.id);
            }
        });
    });

}


// New layer toggle functions
function toggleTerrainLayer() {
    const checked = document.getElementById('terrainLayer').checked;
    if (checked) {
        map.addLayer(terrainLayer);
    } else {
        map.removeLayer(terrainLayer);
    }
}

function toggleTreeDensityLayer() {
    const checked = document.getElementById('treeDensityLayer').checked;
    if (checked) {
        map.addLayer(treeDensityLayer);
    } else {
        map.removeLayer(treeDensityLayer);
    }
}

function toggleCropHealthLayer() {
    const checked = document.getElementById('cropHealthLayer').checked;
    if (checked) {
        map.addLayer(cropHealthLayer);
    } else {
        map.removeLayer(cropHealthLayer);
    }
}

function toggleIrrigationLayer() {
    const checked = document.getElementById('irrigationLayer').checked;
    if (checked) {
        map.addLayer(irrigationLayer);
    } else {
        map.removeLayer(irrigationLayer);
    }
}

function toggleSoilTypeLayer() {
    const checked = document.getElementById('soilTypeLayer').checked;
    if (checked) {
        map.addLayer(soilTypeLayer);
    } else {
        map.removeLayer(soilTypeLayer);
    }
}

function toggleClimateZoneLayer() {
    const checked = document.getElementById('climateZoneLayer').checked;
    if (checked) {
        map.addLayer(climateZoneLayer);
    } else {
        map.removeLayer(climateZoneLayer);
    }
}

function toggleRoadsLayer() {
    const checked = document.getElementById('roadsLayer').checked;
    if (checked) {
        map.addLayer(roadsLayer);
    } else {
        map.removeLayer(roadsLayer);
    }
}


//validate boundary before saving

function handleSearchInput(e) {
    const query = e.target.value.trim();
    currentSearchQuery = query;

    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    // Hide results if query is empty
    if (!query) {
        clearSearch();
        return;
    }

    // Show loading state
    showLoadingResults();

    // Debounce search to avoid too many requests
    searchTimeout = setTimeout(() => {
        performSearch(query);
    }, 300);
}

// Enhanced search function
function performSearch(query = null) {
    const searchQuery = query || document.getElementById('searchInput').value.trim();
    const resultsContainer = document.getElementById('searchResults');
    const statsContainer = document.getElementById('searchStats');

    if (!searchQuery) {
        clearSearch();
        return;
    }

    // Perform client-side search on existing farm data
    const results = searchFarms(searchQuery);

    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search me-2"></i>
                No farms found for "${escapeHtml(searchQuery)}"
            </div>
        `;
    } else {
        resultsContainer.innerHTML = results.map((farm, index) => `
            <div class="search-result-item ${index === 0 ? 'active' : ''}" 
                 onclick="selectSearchResult(${farm.id})"
                 onmouseover="highlightSearchResult(${farm.id})"
                 onmouseout="unhighlightSearchResult(${farm.id})">
                <div class="flex-grow-1">
                    <div class="farm-code">${highlightMatch(farm.farm_code, searchQuery)}</div>
                    <div class="farm-name">${highlightMatch(farm.name, searchQuery)}</div>
                    <div class="farm-farmer">${highlightMatch(farm.farmer_name, searchQuery)}</div>
                </div>
                <div>
                    <span class="farm-status-badge" style="background-color: ${statusColors[farm.status] || '#6c757d'}">
                        ${farm.status.charAt(0).toUpperCase() + farm.status.slice(1)}
                    </span>
                </div>
            </div>
        `).join('');

        // Auto-select first result
        if (results.length > 0) {
            highlightSearchResult(results[0].id);
        }
    }

    // Update stats
    document.getElementById('matchesCount').textContent = `${results.length} match${results.length !== 1 ? 'es' : ''} found`;
    statsContainer.style.display = 'block';

    // Show results
    resultsContainer.style.display = 'block';
}

// Client-side search function
function searchFarms(query) {
    if (!query) return [];

    const lowerQuery = query.toLowerCase();
    const results = [];

    farmsData.forEach(farm => {
        let score = 0;
        let matchedFields = [];

        // Check farm code (exact match gets highest score)
        if (farm.farm_code && farm.farm_code.toLowerCase().includes(lowerQuery)) {
            score += farm.farm_code.toLowerCase() === lowerQuery ? 100 : 50;
            matchedFields.push('code');
        }

        // Check farm name
        if (farm.name && farm.name.toLowerCase().includes(lowerQuery)) {
            score += 30;
            matchedFields.push('name');
        }

        // Check farmer name
        if (farm.farmer_name && farm.farmer_name.toLowerCase().includes(lowerQuery)) {
            score += 20;
            matchedFields.push('farmer');
        }

        // Check farmer national ID
        if (farm.farmer_national_id && farm.farmer_national_id.toLowerCase().includes(lowerQuery)) {
            score += 10;
            matchedFields.push('national_id');
        }

        // Check primary crop
        if (farm.primary_crop && farm.primary_crop.toLowerCase().includes(lowerQuery)) {
            score += 5;
            matchedFields.push('crop');
        }

        if (score > 0) {
            results.push({
                ...farm,
                score,
                matchedFields
            });
        }
    });

    // Sort by score (highest first)
    return results.sort((a, b) => b.score - a.score);
}

// Highlight text matches
function highlightMatch(text, query) {
    if (!text || !query) return escapeHtml(text || '');

    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();
    const index = lowerText.indexOf(lowerQuery);

    if (index === -1) return escapeHtml(text);

    const before = text.substring(0, index);
    const match = text.substring(index, index + query.length);
    const after = text.substring(index + query.length);

    return `${escapeHtml(before)}<span class="search-highlight">${escapeHtml(match)}</span>${escapeHtml(after)}`;
}

// Select search result
function selectSearchResult(farmId) {
    const farm = farmsData.find(f => f.id === farmId);
    if (!farm) return;

    // Hide search results
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('searchInput').value = farm.farm_code;

    // Zoom to farm
    zoomToFarm(farmId);

    // Show farm details
    showFarmDetails(farmId);
}

// Highlight farm on map when hovering over search result
function highlightSearchResult(farmId) {
    // Remove previous highlight
    if (highlightedFarm) {
        unhighlightSearchResult(highlightedFarm);
    }

    const farm = farmsData.find(f => f.id === farmId);
    if (!farm) return;

    // Find the layer for this farm
    const layer = farmLayers.getLayers().find(l => l.options.farmId === farmId);

    if (layer) {
        // Store original style
        layer._originalStyle = { ...layer.options };

        // Apply highlight style
        if (layer instanceof L.Polygon) {
            layer.setStyle({
                color: '#ff6b35',
                fillColor: '#ff6b35',
                fillOpacity: 0.8,
                weight: 4
            });
        } else if (layer instanceof L.CircleMarker) {
            layer.setStyle({
                fillColor: '#ff6b35',
                color: '#fff',
                fillOpacity: 1,
                weight: 3,
                radius: 12
            });
        }

        // Bring to front
        layer.bringToFront();

        // Open popup briefly
        layer.openPopup();

        highlightedFarm = farmId;

        // Update search results active state
        updateSearchResultsActiveState(farmId);
    }
}

// Remove highlight
function unhighlightSearchResult(farmId) {
    const layer = farmLayers.getLayers().find(l => l.options.farmId === farmId);

    if (layer && layer._originalStyle) {
        // Restore original style
        if (layer instanceof L.Polygon) {
            layer.setStyle({
                color: layer._originalStyle.color,
                fillColor: layer._originalStyle.fillColor,
                fillOpacity: layer._originalStyle.fillOpacity,
                weight: layer._originalStyle.weight
            });
        } else if (layer instanceof L.CircleMarker) {
            layer.setStyle({
                fillColor: layer._originalStyle.fillColor,
                color: layer._originalStyle.color,
                fillOpacity: layer._originalStyle.fillOpacity,
                weight: layer._originalStyle.weight,
                radius: layer._originalStyle.radius
            });
        }

        // Close popup
        layer.closePopup();
    }

    if (highlightedFarm === farmId) {
        highlightedFarm = null;
    }
}

// Update active state in search results
function updateSearchResultsActiveState(activeFarmId) {
    const resultItems = document.querySelectorAll('.search-result-item');
    resultItems.forEach(item => {
        const farmId = parseInt(item.getAttribute('onclick').match(/\d+/)[0]);
        if (farmId === activeFarmId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Clear search
function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('searchStats').style.display = 'none';

    // Remove any highlights
    if (highlightedFarm) {
        unhighlightSearchResult(highlightedFarm);
    }

    // Clear search timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
        searchTimeout = null;
    }

    currentSearchQuery = '';
}

// Show loading state in search results
function showLoadingResults() {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="loading-results">
            <i class="fas fa-spinner me-2"></i>
            Searching...
        </div>
    `;
    resultsContainer.style.display = 'block';
}

// Enhanced zoom to farm function
function zoomToFarm(farmId) {
    const farm = farmsData.find(f => f.id === farmId);
    if (!farm) return;

    // Find the layer for this farm
    const layer = farmLayers.getLayers().find(l => l.options.farmId === farmId);

    if (layer) {
        if (layer instanceof L.Polygon) {
            map.fitBounds(layer.getBounds(), {
                padding: [50, 50],
                maxZoom: 16
            });
        } else {
            map.setView(layer.getLatLng(), 15);
        }

        // Highlight the farm
        highlightSearchResult(farmId);

        // Auto-remove highlight after 5 seconds
        setTimeout(() => {
            if (highlightedFarm === farmId) {
                unhighlightSearchResult(farmId);
            }
        }, 5000);
    }
}

// Add keyboard navigation for search results
document.addEventListener('keydown', function (e) {
    const resultsContainer = document.getElementById('searchResults');
    if (resultsContainer.style.display === 'none') return;

    const resultItems = document.querySelectorAll('.search-result-item');
    if (resultItems.length === 0) return;

    let currentIndex = -1;
    resultItems.forEach((item, index) => {
        if (item.classList.contains('active')) {
            currentIndex = index;
        }
    });

    switch (e.key) {
        case 'ArrowDown':
            e.preventDefault();
            const nextIndex = (currentIndex + 1) % resultItems.length;
            highlightSearchResult(parseInt(resultItems[nextIndex].getAttribute('onclick').match(/\d+/)[0]));
            break;

        case 'ArrowUp':
            e.preventDefault();
            const prevIndex = currentIndex <= 0 ? resultItems.length - 1 : currentIndex - 1;
            highlightSearchResult(parseInt(resultItems[prevIndex].getAttribute('onclick').match(/\d+/)[0]));
            break;

        case 'Enter':
            if (currentIndex >= 0) {
                e.preventDefault();
                selectSearchResult(parseInt(resultItems[currentIndex].getAttribute('onclick').match(/\d+/)[0]));
            }
            break;

        case 'Escape':
            clearSearch();
            break;
    }
});


// Close search results when clicking outside
document.addEventListener('click', function (e) {
    const searchContainer = document.querySelector('.search-top-container');
    const searchResults = document.getElementById('searchResults');

    // Check if search elements exist and if click is outside
    if (searchContainer && searchResults && searchResults.style.display !== 'none') {
        if (!searchContainer.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    }
});/*  */


// Load farm data from server
function loadFarmData() {
    showLoading('Loading farm data...');

    fetch('/map/data/')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            console.log('Farm data response:', data);
            if (data.success) {
                farmsData = data.farms;
                console.log('Loaded farm data:', farmsData);
                renderFarmsOnMap();
                showToast('Farm data loaded successfully', 'success');
            } else {
                showToast('Error loading farm data: ' + data.error, 'error');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            showToast('Error loading farm data', 'error');
        });
}

// Get farm color based on validation status and farm status
// Farm status colors
const statusColors = {
    'active': '#28a745',      // Green
    'delayed': '#ffc107',     // Yellow
    'critical': '#dc3545',    // Red
    'completed': '#17a2b8',   // Blue
    'abandoned': '#6c757d'    // Gray
};

// Get farm color based on status and validation status
function getFarmColor(farm) {
    // Base color from status
    const statusColor = statusColors[farm.status] || '#6c757d';
    
    // If farm is validated, use the status color with full opacity
    // If not validated, use a muted/desaturated version of the status color
    if (farm.validation_status) {
        return statusColor;
    } else {
        // Return a muted/darker version for non-validated farms
        return getMutedColor(statusColor);
    }
}

// Get muted color for non-validated farms
function getMutedColor(color) {
    // Convert hex to RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    // Reduce saturation and brightness
    const mutedR = Math.floor(r * 0.7);
    const mutedG = Math.floor(g * 0.7);
    const mutedB = Math.floor(b * 0.7);
    
    // Convert back to hex
    return `#${mutedR.toString(16).padStart(2, '0')}${mutedG.toString(16).padStart(2, '0')}${mutedB.toString(16).padStart(2, '0')}`;
}

// Get farm style based on status and validation status
function getFarmStyle(farm) {
    const baseColor = getFarmColor(farm);
    const isActive = farm.status === 'active';
    const isValidated = farm.validation_status;
    
    return {
        color: baseColor,
        fillColor: baseColor,
        fillOpacity: isValidated ? 0.4 : 0.2,        // More opaque for validated
        weight: isValidated ? 3 : 2,                 // Thicker border for validated
        opacity: isValidated ? 1 : 0.8,              // More transparent for non-validated
        dashArray: isValidated ? null : '5, 5'       // Dashed for non-validated
    };
}

// Get marker style for point locations
function getMarkerStyle(farm) {
    const baseColor = getFarmColor(farm);
    const isValidated = farm.validation_status;
    
    return {
        radius: isValidated ? 10 : 8,                // Larger for validated
        fillColor: baseColor,
        color: '#fff',
        weight: isValidated ? 3 : 2,                 // Thicker border for validated
        opacity: 1,
        fillOpacity: isValidated ? 0.9 : 0.7         // More opaque for validated
    };
}

// Render farms on map





// Render farms on map
function renderFarmsOnMap() {
    // Clear existing layers
    farmLayers.clearLayers();

    let validatedCount = 0;
    let nonValidatedCount = 0;
    let statusCounts = {
        'active': 0,
        'delayed': 0,
        'critical': 0,
        'completed': 0,
        'abandoned': 0
    };

    farmsData.forEach(farm => {
        let layer = null;

        // Create boundary polygon if available
        if (farm.boundary && farm.boundary.coordinates) {
            try {
                // Fix the coordinate format - handle both formats
                let coordinates = farm.boundary.coordinates[0];

                console.log('Farm', farm.id, 'boundary coordinates:', coordinates);

                // Check if coordinates are in the problematic format [[lng], [lat], [lng], [lat]]
                if (Array.isArray(coordinates[0]) && coordinates[0].length === 1) {
                    // Convert from [[lng], [lat], [lng], [lat]] to [[lng, lat], [lng, lat]]
                    const fixedCoords = [];
                    for (let i = 0; i < coordinates.length; i += 2) {
                        if (i + 1 < coordinates.length) {
                            const lng = coordinates[i][0];
                            const lat = coordinates[i + 1][0];
                            fixedCoords.push([lng, lat]);
                        }
                    }
                    coordinates = fixedCoords;
                    console.log('Fixed coordinates for farm', farm.id, ':', coordinates);
                }

                // Convert to Leaflet format [lat, lng] and ensure polygon is closed
                const leafletCoords = coordinates.map(coord => {
                    if (Array.isArray(coord) && coord.length >= 2) {
                        return [coord[1], coord[0]]; // Convert [lng, lat] to [lat, lng]
                    }
                    return null;
                }).filter(coord => coord !== null);

                // Close the polygon if not already closed
                if (leafletCoords.length >= 3) {
                    const firstCoord = leafletCoords[0];
                    const lastCoord = leafletCoords[leafletCoords.length - 1];
                    if (firstCoord[0] !== lastCoord[0] || firstCoord[1] !== lastCoord[1]) {
                        leafletCoords.push([firstCoord[0], firstCoord[1]]);
                    }
                }

                console.log('Leaflet coordinates for farm', farm.id, ':', leafletCoords);

                // Only create polygon if we have at least 3 points
                if (leafletCoords.length >= 3) {
                    const farmStyle = getFarmStyle(farm);
                    
                    layer = L.polygon(leafletCoords, {
                        ...farmStyle,
                        farmId: farm.id,
                        farmData: farm // Store farm data for easy access
                    });

                    // Add popup with status and validation info
                    layer.bindPopup(createFarmPopup(farm));
                    // distributeTreesInPolygon(leafletCoords, farm);
                    safeDistributeTrees(leafletCoords, farm);

                    // Add click event
                    // layer.on('click', function (e) {
                    //     L.DomEvent.stopPropagation(e);
                    //     showFarmDetails(farm.id);
                    // });

                    // Add hover effects
                    layer.on('mouseover', function (e) {
                        this.setStyle({
                            weight: farm.validation_status ? 4 : 3,
                            fillOpacity: farm.validation_status ? 0.6 : 0.3
                        });
                    });

                    layer.on('mouseout', function (e) {
                        this.setStyle(getFarmStyle(farm));
                    });

                    // Update counts
                    if (farm.validation_status) {
                        validatedCount++;
                    } else {
                        nonValidatedCount++;
                    }
                    statusCounts[farm.status]++;

                    farmLayers.addLayer(layer);
                    console.log('Successfully created polygon for farm', farm.id, 'Status:', farm.status, 'Validation:', farm.validation_status);
                } else {
                    console.warn('Not enough coordinates for farm', farm.id, ':', leafletCoords.length);
                }

            } catch (error) {
                console.error('Error creating polygon for farm:', farm.id, error);
                console.error('Farm boundary data:', farm.boundary);
            }
        }

        // Create point marker if no boundary but location available
        if (!layer && farm.location && farm.location.coordinates) {
            try {
                let coords = farm.location.coordinates;

                // Handle location coordinate format
                if (Array.isArray(coords[0]) && coords[0].length === 1) {
                    // Convert from [[lng], [lat]] to [lat, lng]
                    coords = [coords[1][0], coords[0][0]];
                } else {
                    // Already in [lng, lat] format
                    coords = [coords[1], coords[0]];
                }

                const markerStyle = getMarkerStyle(farm);
                
                layer = L.circleMarker(coords, {
                    ...markerStyle,
                    farmId: farm.id,
                    farmData: farm
                });

                // Add popup with status and validation info
                layer.bindPopup(createFarmPopup(farm));

                // Add click event
                
                // Add hover effects for markers
                layer.on('mouseover', function (e) {
                    this.setStyle({
                        radius: farm.validation_status ? 12 : 10,
                        fillOpacity: 1
                    });
                });

                layer.on('mouseout', function (e) {
                    this.setStyle(getMarkerStyle(farm));
                });

                // Update counts
                if (farm.validation_status) {
                    validatedCount++;
                } else {
                    nonValidatedCount++;
                }
                statusCounts[farm.status]++;

                farmLayers.addLayer(layer);
                console.log('Successfully created marker for farm', farm.id, 'Status:', farm.status, 'Validation:', farm.validation_status);

            } catch (error) {
                console.error('Error creating marker for farm:', farm.id, error);
            }
        }

        if (!layer) {
            console.warn('Could not create any layer for farm:', farm.id);
        }
    });

    // Update statistics displays
    updateValidationStats(validatedCount, nonValidatedCount);
    // updateStatusStats(statusCounts);
    
    // Fit map to show all farms if we have any
    const layers = farmLayers.getLayers();
    if (layers.length > 0) {
        console.log('Fitting bounds for', layers.length, 'layers');
        console.log('Status counts:', statusCounts);
        console.log('Validated:', validatedCount, 'Non-validated:', nonValidatedCount);
        fitToBounds();
    } else {
        console.warn('No layers were created');
        showToast('No farm boundaries could be displayed', 'warning');
    }
}


// Function to distribute tree icons within a polygon - FIXED VERSION
function distributeTreesInPolygon(polygonCoords, farm) {
    const treeCount = calculateTreeCountForFarm(farm);
    
    if (treeCount === 0) return;

    // Create a temporary polygon to work with
    const polygon = L.polygon(polygonCoords);
    const bounds = polygon.getBounds();
    
    // Calculate area using a simple approximation instead of geodesicArea
    const area = calculatePolygonArea(polygonCoords);
    
    // Determine optimal number of icons to display (max 30 for performance)
    const maxIcons = Math.min(Math.max(5, Math.floor(treeCount / 10)), 30);
    
    console.log(`Optimal number of icons for farm ${farm.id}: ${maxIcons}`);
    console.log(`Area of polygon: ${area} square meters`);
    
    // Generate points using random distribution within bounds
    const treePoints = generateRandomPointsInPolygon(polygon, bounds, maxIcons);
    
    // Add tree icons at generated points
    treePoints.forEach(point => {
        addTreeIcon(point, farm);
    });
    
    console.log(`Added ${treePoints.length} tree icons for farm ${farm.id}`);
}

// Simple polygon area calculation (approximate)
function calculatePolygonArea(coords) {
    if (!coords || coords.length < 3) return 0;
    
    let area = 0;
    const n = coords.length;
    
    for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        area += coords[i][1] * coords[j][0]; // lat * lng
        area -= coords[j][1] * coords[i][0]; // lat * lng
    }
    
    area = Math.abs(area) / 2;
    
    // Convert to square meters (approximate)
    // This is a simplified conversion that works reasonably well for small areas
    const centerLat = coords.reduce((sum, coord) => sum + coord[0], 0) / n;
    const metersPerDegree = 111319.9 * Math.cos(centerLat * Math.PI / 180);
    return area * metersPerDegree * metersPerDegree;
}

// Check if point is inside polygon (improved version)
function isPointInPolygon(point, polygon) {
    // First check if point is within polygon bounds for quick rejection
    if (!polygon.getBounds().contains(point)) {
        return false;
    }
    
    // Use ray casting algorithm for accurate point-in-polygon check
    return pointInPolygon(point, polygon.getLatLngs()[0]);
}

// Ray casting algorithm for point in polygon
function pointInPolygon(point, vs) {
   
    const x = point.lat, y = point.lng;
    let inside = false;
    
    for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
        const xi = vs[i].lat, yi = vs[i].lng;
        const xj = vs[j].lat, yj = vs[j].lng;
        
        const intersect = ((yi > y) != (yj > y))
            && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
    }
    
    return inside;
}

// Generate random points within polygon bounds - IMPROVED VERSION
function generateRandomPointsInPolygon(polygon, bounds, maxPoints) {
    const points = [];
    const maxAttempts = maxPoints * 5; // Increased attempts for better distribution
    
    for (let i = 0; i < maxAttempts && points.length < maxPoints; i++) {
        const lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
        const lng = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
        const point = L.latLng(lat, lng);
        
        // Check if point is inside polygon using improved algorithm
        if (pointInPolygon(point, polygon.getLatLngs()[0])) {
            points.push([lat, lng]);
        }
    }
    
    // If we didn't get enough points, try a grid-based approach
    if (points.length < maxPoints && points.length > 0) {
        const additionalPoints = generateGridPointsInPolygon(polygon, bounds, maxPoints - points.length);
        points.push(...additionalPoints);
    }
    console.log(`Generated ${points.length} points within polygon`);
    return points;
}

// Grid-based point generation as fallback
function generateGridPointsInPolygon(polygon, bounds, numPoints) {
    const points = [];
    const latLngs = polygon.getLatLngs()[0];
    
    // Calculate grid size based on number of points needed
    const gridSize = Math.ceil(Math.sqrt(numPoints * 2));
    
    const latStep = (bounds.getNorth() - bounds.getSouth()) / gridSize;
    const lngStep = (bounds.getEast() - bounds.getWest()) / gridSize;
    
    for (let i = 0; i < gridSize && points.length < numPoints; i++) {
        for (let j = 0; j < gridSize && points.length < numPoints; j++) {
            const lat = bounds.getSouth() + (i * latStep) + (Math.random() * latStep * 0.3);
            const lng = bounds.getWest() + (j * lngStep) + (Math.random() * lngStep * 0.3);
            const point = L.latLng(lat, lng);
            
            if (pointInPolygon(point, latLngs)) {
                points.push([lat, lng]);
            }
        }
    }
    
    return points;
}

// Update the tree distribution call to handle errors gracefully
function safeDistributeTrees(polygonCoords, farm) {
    try {
        distributeTreesInPolygon(polygonCoords, farm);
    } catch (error) {
        console.warn('Error distributing trees for farm', farm.id, error);
        // Fallback: add a single tree icon at the center
        const polygon = L.polygon(polygonCoords);
        const center = polygon.getBounds().getCenter();
        addTreeIcon([center.lat, center.lng], farm);
    }
}



// Calculate number of trees for a farm
function calculateTreeCountForFarm(farm) {
    // If farm has tree_count data, use it
    if (farm.tree_count) {
        return farm.tree_count;
    }
    
    // Otherwise estimate based on area and typical density
    if (farm.area_hectares) {
        const typicalDensity = 150; // trees per hectare (average)
        return Math.round(farm.area_hectares * typicalDensity);
    }
    
    // Default fallback based on farm size
    return 50;
}

// Generate random points within polygon bounds
function generateRandomPointsInPolygon(polygon, bounds, maxPoints) {
    const points = [];
    const maxAttempts = maxPoints * 3; // Limit attempts to avoid infinite loop
    
    for (let i = 0; i < maxAttempts && points.length < maxPoints; i++) {
        const lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
        const lng = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
        const point = [lat, lng];
        
        // Check if point is inside polygon
        if (isPointInPolygon(point, polygon)) {
            points.push(point);
        }
    }
    
    return points;
}

 function isPointInPolygon(point, polygon) {
    return polygon.getBounds().contains(point) && polygon.contains(point);
}
// Check if point is inside polygon (simplified version)
function isPointInPolygon(point, polygon) {
    return polygon.getBounds().contains(point) && L.GeometryUtil.inside(point, polygon);
}

function isPointInPolygon(point, polygon) {
    const pt = turf.point([point.lng, point.lat]);
    const poly = turf.polygon([polygon.getLatLngs()[0].map(ll => [ll.lng, ll.lat])]);
    return turf.booleanPointInPolygon(pt, poly);
}

// Add beautiful tree icon
function addTreeIcon(coords, farm) {
    // Create custom tree icon with nice tree-like appearance
    const treeSize = 16 + Math.random() * 8; // Random size between 16-24px
    const treeColor = getTreeColor(farm);
    
    const treeIcon = L.divIcon({
        html: `
            <div style="
                width: ${treeSize}px;
                height: ${treeSize}px;
                position: relative;
                transform: translate(-50%, -50%);
            ">
                <!-- Tree trunk -->
                <div style="
                    position: absolute;
                    bottom: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: ${treeSize * 0.2}px;
                    height: ${treeSize * 0.4}px;
                    background: #8B4513;
                    border-radius: 1px;
                    z-index: 1;
                "></div>
                <!-- Tree crown -->
                <div style="
                    position: absolute;
                    top: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: ${treeSize * 0.8}px;
                    height: ${treeSize * 0.6}px;
                    background: ${treeColor};
                    border-radius: 50% 50% 40% 40%;
                    box-shadow: 0 0 2px rgba(0,0,0,0.3);
                    z-index: 2;
                "></div>
            </div>
        `,
        className: 'tree-icon',
        iconSize: [treeSize, treeSize],
        iconAnchor: [treeSize / 2, treeSize]
    });
    
    const treeMarker = L.marker(coords, {
        icon: treeIcon,
        zIndexOffset: 1000,
        farmId: farm.id,
        interactive: false // Make trees non-clickable
    });
    
    // Add to tree icons layer
    if (!window.treeIconsLayer) {
        window.treeIconsLayer = L.layerGroup();
        window.treeIconsLayer.addTo(map);
    }
    window.treeIconsLayer.addLayer(treeMarker);
}

// Get tree color based on farm status
function getTreeColor(farm) {
    const statusColors = {
        'active': '#22c55e', // Green
        'delayed': '#eab308', // Yellow
        'critical': '#ef4444', // Red
        'completed': '#15803d', // Dark Green
        'abandoned': '#6b7280' // Gray
    };
    
    return statusColors[farm.status] || '#22c55e';
}

// Update farm style to ensure polygons are visible
function getFarmStyle(farm) {
    const baseColor = getStatusColor(farm.status);
    
    return {
        weight: farm.validation_status ? 3 : 2,
        opacity: farm.validation_status ? 0.9 : 0.7,
        color: baseColor,
        fillColor: baseColor,
        fillOpacity: farm.validation_status ? 0.15 : 0.1, // Low opacity to see trees
        dashArray: farm.validation_status ? null : '5,5'
    };
}

// Function to clear tree icons
function clearTreeIcons() {
    if (window.treeIconsLayer) {
        window.treeIconsLayer.clearLayers();
    }
}

// Update marker style
function getMarkerStyle(farm) {
    const baseColor = getStatusColor(farm.status);
    
    return {
        radius: farm.validation_status ? 8 : 6,
        fillColor: baseColor,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    };
}

// Get status color
function getStatusColor(status) {
    const statusColors = {
        'active': '#22c55e',
        'delayed': '#eab308', 
        'critical': '#ef4444',
        'completed': '#15803d',
        'abandoned': '#6b7280'
    };
    return statusColors[status] || '#22c55e';
}

// Add CSS for tree icons
const treeIconStyles = `
    .tree-icon {
        background: transparent !important;
        border: none !important;
    }
    .tree-icon div {
        pointer-events: none;
    }
    .leaflet-marker-icon.tree-icon {
        background: transparent !important;
    }
`;

// Inject styles
if (!document.querySelector('#tree-icon-styles')) {
    const styleSheet = document.createElement("style");
    styleSheet.id = 'tree-icon-styles';
    styleSheet.innerText = treeIconStyles;
    document.head.appendChild(styleSheet);
}

// Make sure to call this when initializing the map
function initializeTreeLayer() {
    if (!window.treeIconsLayer) {
        window.treeIconsLayer = L.layerGroup();
        window.treeIconsLayer.addTo(map);
    }
}

// Call this after map initialization
// initializeTreeLayer();

// Update validation statistics display
function updateValidationStats(validated, nonValidated) {
    const statsElement = document.getElementById('validationStats');
    if (statsElement) {
        statsElement.innerHTML = `
            <div class="validation-stats">
                <span class="badge bg-success">✓ ${validated} Validated</span>
                <span class="badge bg-danger ms-2">✗ ${nonValidated} Pending</span>
            </div>
        `;
    }
    
    // Also update in console for debugging
    console.log(`Validation Stats: ${validated} validated, ${nonValidated} non-validated`);
}

// Update farm popup to show validation status
// Create farm popup content
function createFarmPopup(farm) {
    return `
        <div class="farm-popup">
            <div class="farm-name mb-2">${escapeHtml(farm.name)}</div>
            
            <div class="mb-3">
                <span class="farm-status" style="background-color: ${statusColors[farm.status] || '#6c757d'}">
                    ${farm.status.toUpperCase()}
                </span>
            </div>

            <table class="farm-details-table">
                <tbody>
                    <tr>
                        <td class="label-cell"><strong>Code:</strong></td>
                        <td class="value-cell">${farm.farm_code}</td>
                    </tr>
                    <tr>
                        <td class="label-cell"><strong>Farmer:</strong></td>
                        <td class="value-cell">${escapeHtml(farm.farmer_name)}</td>
                    </tr>
                    <tr>
                        <td class="label-cell"><strong>Area:</strong></td>
                        <td class="value-cell">${farm.area_hectares || 'N/A'} hectares</td>
                    </tr>
                    <tr>
                        <td class="label-cell"><strong>Crop:</strong></td>
                        <td class="value-cell">${farm.primary_crop || 'N/A'}</td>
                    </tr>
                </tbody>
            </table>

            <div class="mt-3 text-center">
                
                <a href="#" class="btn btn-link" onclick="showFarmDetails(${farm.id})">View Details</a>
            </div>
        </div>
    `;
}

// Function to update a specific farm's style after validation
function updateFarmStyle(farmId) {
    const layers = farmLayers.getLayers();
    const layer = layers.find(l => l.options.farmId === farmId);
    
    if (layer && layer.options.farmData) {
        // Update the farm data validation status
        layer.options.farmData.validation_status = true;
        
        // Update the layer style
        const newStyle = getFarmStyle(layer.options.farmData);
        layer.setStyle(newStyle);
        
        // Update the popup content
        layer.setPopupContent(createFarmPopup(layer.options.farmData));
        
        console.log('Updated farm style for farm:', farmId);
    }
}

// Search functionality
function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    const resultsContainer = document.getElementById('searchResults');

    if (!query) {
        resultsContainer.style.display = 'none';
        return;
    }

    // Simple client-side search
    const results = farmsData.filter(farm =>
        farm.farm_code.toLowerCase().includes(query.toLowerCase()) ||
        farm.name.toLowerCase().includes(query.toLowerCase()) ||
        farm.farmer_name.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 10); // Limit to 10 results

    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="search-result-item text-muted">No farms found</div>';
    } else {
        resultsContainer.innerHTML = results.map(farm => `
                <div class="search-result-item" onclick="zoomToFarm(${farm.id})">
                    <strong>${escapeHtml(farm.farm_code)}</strong><br>
                    <small>${escapeHtml(farm.name)} - ${escapeHtml(farm.farmer_name)}</small>
                </div>
            `).join('');
    }

    resultsContainer.style.display = 'block';
}

// Zoom to specific farm
function zoomToFarm(farmId) {
    const farm = farmsData.find(f => f.id === farmId);
    if (!farm) return;

    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('searchInput').value = '';

    // Find the layer for this farm
    const layer = farmLayers.getLayers().find(l => l.options.farmId === farmId);

    if (layer) {
        if (layer instanceof L.Polygon) {
            map.fitBounds(layer.getBounds(), { padding: [50, 50] });
        } else {
            map.setView(layer.getLatLng(), 15);
        }

        // Open popup
        layer.openPopup();

        // Show farm details
        showFarmDetails(farmId);
    }
}

// Show farm details in modal
function showFarmDetails(farmId) {
    const farm = farmsData.find(f => f.id === farmId);
    if (!farm) return;

    currentFarmId = farmId;

    const modalContent = `
            <div class="farm-details-grid">
                <div class="farm-details-section">
                    <h6>Farm Information</h6>
                    <div class="detail-row">
                        <span class="detail-label">Farm Code:</span>
                        <span class="detail-value">${farm.farm_code}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Name:</span>
                        <span class="detail-value">${escapeHtml(farm.name)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value"><span class="badge bg-${getStatusClass(farm.status)}">${farm.status}</span></span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Area:</span>
                        <span class="detail-value">${farm.area_hectares || 'N/A'} hectares</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Soil Type:</span>
                        <span class="detail-value">${farm.soil_type || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Irrigation:</span>
                        <span class="detail-value">${farm.irrigation_type || 'N/A'} (${farm.irrigation_coverage || 0}%)</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Validation:</span>
                        <span class="detail-value">${farm.validation_status ? '<span class="badge bg-success">Validated</span>' : '<span class="badge bg-warning">Not Validated</span>'}</span>
                    </div>
                </div>
                
                <div class="farm-details-section">
                    <h6>Farmer Information</h6>
                    <div class="detail-row">
                        <span class="detail-label">Name:</span>
                        <span class="detail-value">${escapeHtml(farm.farmer_name)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">National ID:</span>
                        <span class="detail-value">${farm.farmer_national_id}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Primary Crop:</span>
                        <span class="detail-value">${farm.primary_crop}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Experience:</span>
                        <span class="detail-value">${farm.years_of_experience} years</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Cooperative:</span>
                        <span class="detail-value">${farm.cooperative_membership || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Registration:</span>
                        <span class="detail-value">${farm.registration_date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Last Visit:</span>
                        <span class="detail-value">${farm.last_visit_date || 'Never'}</span>
                    </div>
                </div>
            </div>
           
        `;

    document.getElementById('farmDetails').innerHTML = modalContent;

    // Show/hide edit button based on boundary availability
    const editBtn = document.getElementById('editBoundaryBtn');
    editBtn.style.display = farm.has_boundary ? 'inline-block' : 'none';

    const farmModal = new bootstrap.Modal(document.getElementById('farmModal'));
    farmModal.show();
}

// Start editing boundary using Leaflet Draw
function startEditingBoundary() {

    const farm = farmsData.find(f => f.id === currentFarmId);
    if (!farm || !farm.boundary) {
        showToast('No boundary available for editing', 'warning');
        return;
    }

    // Find the existing polygon layer
    const existingLayer = farmLayers.getLayers().find(l => l.options.farmId === currentFarmId);
    if (!existingLayer || !(existingLayer instanceof L.Polygon)) {
        showToast('Could not find farm boundary for editing', 'error');
        return;
    }

    // Store reference to original polygon
    currentPolygon = existingLayer;

    // Get the coordinates
    const latlngs = existingLayer.getLatLngs()[0];

    // Hide original layer
    existingLayer.setStyle({ opacity: 0, fillOpacity: 0 });

    // Create new polygon for editing with vertices
    editingLayer = L.polygon(latlngs, {
        color: '#ff6b35',
        fillColor: '#ff6b35',
        fillOpacity: 0.3,
        weight: 3,
        dashArray: '10, 10'
    }).addTo(map);

    // Add vertices as draggable markers
    editingLayer.vertexMarkers = [];
    latlngs.forEach((latlng, index) => {
        const vertexMarker = L.marker(latlng, {
            draggable: true,
            icon: L.divIcon({
                className: 'vertex-marker',
                html: '<div style="background-color: #ff6b35; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>',
                iconSize: [16, 16]
            })
        }).addTo(map);

        vertexMarker.on('drag', function (e) {
            const marker = e.target;
            const newLatLng = marker.getLatLng();

            // Update the polygon vertex
            latlngs[index] = newLatLng;
            editingLayer.setLatLngs([latlngs]);
        });

        editingLayer.vertexMarkers.push(vertexMarker);
    });

    // Update UI
    document.getElementById('editBoundaryBtn').style.display = 'none';
    document.getElementById('saveBoundaryBtn').style.display = 'inline-block';
    document.getElementById('cancelEditBtn').style.display = 'inline-block';

    showToast('Drag the circle vertices to reshape the boundary', 'info');
}

// Save boundary changes to server
function saveBoundaryChanges() {
    if (!editingLayer || !currentFarmId) {
        showToast('No boundary changes to save', 'warning');
        return;
    }

    try {
        // Get updated coordinates from the edited layer
        const latlngs = editingLayer.getLatLngs()[0];
        const coordinates = latlngs.map(latlng => [latlng.lng, latlng.lat]);

        // Ensure polygon is closed
        const firstCoord = coordinates[0];
        const lastCoord = coordinates[coordinates.length - 1];
        if (firstCoord[0] !== lastCoord[0] || firstCoord[1] !== lastCoord[1]) {
            coordinates.push([firstCoord[0], firstCoord[1]]);
        }

        console.log('Saving coordinates:', coordinates);

        // Show saving indicator
        showToast('Saving boundary changes...', 'info');

        fetch(`/map/farm/${currentFarmId}/update-boundary/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                boundary_coordinates: coordinates
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Boundary updated successfully', 'success');
                    //reload the page
                    window.location.reload();

                    // Disable editing
                    editingLayer.disableEdit();

                    // Close modal and reload data
                    const farmModal = bootstrap.Modal.getInstance(document.getElementById('farmModal'));
                    if (farmModal) {
                        farmModal.hide();
                    }

                    // Reload farm data to show updated boundary
                    setTimeout(() => {
                        loadFarmData();
                    }, 500);

                } else {
                    showToast('Error updating boundary: ' + data.error, 'error');
                    cancelEditing();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error updating boundary', 'error');
                cancelEditing();
            });

    } catch (error) {
        console.error('Error saving boundary:', error);
        showToast('Error processing boundary data', 'error');
        cancelEditing();
    }
}


// Validate farm boundary
function validateBoundary() {
    if (!currentFarmId) {
        showToast('No farm selected for validation', 'warning');
        return;
    }

    // Show validation indicator
    showToast('Validating farm boundary...', 'info');

    fetch(`/map/farm/${currentFarmId}/validate-boundary/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({})  // Empty body since we just need to toggle the status
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Farm boundary validated successfully!', 'success');
            
            // Update the UI to reflect validation
            updateValidationUI(true);
            
            // Optionally close the modal
            const farmModal = bootstrap.Modal.getInstance(document.getElementById('farmModal'));
            if (farmModal) {
                farmModal.hide();
            }

            // reload the page
            window.location.reload();
            
            // Reload farm data to show updated validation status
            setTimeout(() => {
                loadFarmData();
            }, 500);
            
        } else {
            showToast('Error validating boundary: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error validating boundary', 'error');
    });
}

// Update UI to reflect validation status
function updateValidationUI(isValidated) {
    const validateBtn = document.getElementById('validateBoundaryBtn');
    const validationBadge = document.getElementById('validationBadge');
    
    if (isValidated) {
        // Update button to show it's validated
        validateBtn.innerHTML = '<i class="fas fa-check-circle"></i> Validated';
        validateBtn.classList.remove('btn-outline-warning');
        validateBtn.classList.add('btn-success');
        validateBtn.disabled = true;
        
        // Show validation badge if exists
        if (validationBadge) {
            validationBadge.innerHTML = '<i class="fas fa-check-circle"></i> Validated';
            validationBadge.className = 'badge bg-success';
        }
        
        // Add visual feedback on the map if needed
        if (currentFarmLayer) {
            currentFarmLayer.setStyle({
                color: '#28a745',
                weight: 4,
                fillOpacity: 0.2
            });
        }
    }
}

// Function to check and update validation status when modal opens
function updateValidationStatus(farmData) {
    const validateBtn = document.getElementById('validateBoundaryBtn');
    const validationBadge = document.getElementById('validationBadge');
    
    if (farmData.validation_status) {
        // Farm is already validated
        validateBtn.innerHTML = '<i class="fas fa-check-circle"></i> Validated';
        validateBtn.classList.remove('btn-outline-warning');
        validateBtn.classList.add('btn-success');
        validateBtn.disabled = true;
        
        if (validationBadge) {
            validationBadge.innerHTML = '<i class="fas fa-check-circle"></i> Validated';
            validationBadge.className = 'badge bg-success';
        }
    } else {
        // Farm needs validation
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Validate Boundary';
        validateBtn.classList.remove('btn-success');
        validateBtn.classList.add('btn-outline-warning');
        validateBtn.disabled = false;
        
        if (validationBadge) {
            validationBadge.innerHTML = '<i class="fas fa-clock"></i> Pending Validation';
            validationBadge.className = 'badge bg-warning';
        }
    }
}


function cancelEditing() {
    try {
        // Disable editing if enabled
        if (editingLayer && editingLayer.disableEdit) {
            editingLayer.disableEdit();
        }

        // Remove editing layer
        if (editingLayer && window.editableLayers) {
            window.editableLayers.removeLayer(editingLayer);
        }

        // Restore original polygon
        if (currentPolygon) {
            farmLayers.addLayer(currentPolygon);
            currentPolygon = null;
        }

    } catch (error) {
        console.error('Error cancelling editing:', error);
    } finally {
        // Reset UI
        document.getElementById('editBoundaryBtn').style.display = 'inline-block';
        document.getElementById('saveBoundaryBtn').style.display = 'none';
        document.getElementById('cancelEditBtn').style.display = 'none';

        editingLayer = null;
        showToast('Editing cancelled', 'info');
    }
}


function cancelEditing() {
    // Remove editing layer
    if (editingLayer) {
        map.removeLayer(editingLayer);
        editingLayer = null;
    }

    // Restore original polygon if it exists
    if (currentPolygon) {
        // Re-add original polygon to map and farmLayers
        map.addLayer(currentPolygon);
        currentPolygon = null;
    }

    // Reset UI
    document.getElementById('editBoundaryBtn').style.display = 'inline-block';
    document.getElementById('saveBoundaryBtn').style.display = 'none';
    document.getElementById('cancelEditBtn').style.display = 'none';

    showToast('Editing cancelled', 'info');
}


// Cancel editing
function cancelEditing() {
    // Remove draw control if it exists
    if (editingLayer && editingLayer.drawControl) {
        map.removeControl(editingLayer.drawControl);
    }

    if (editingLayer) {
        map.removeLayer(editingLayer);
        editingLayer = null;
    }

    if (currentPolygon) {
        currentPolygon.setStyle({
            opacity: 1,
            fillOpacity: 0.5
        });
        currentPolygon = null;
    }

    // Reset UI
    document.getElementById('editBoundaryBtn').style.display = 'inline-block';
    document.getElementById('saveBoundaryBtn').style.display = 'none';
    document.getElementById('cancelEditBtn').style.display = 'none';

    showToast('Editing cancelled', 'info');
}


;

// Toggle full screen mode
function toggleFullScreen() {
    const fullscreenContainer = document.getElementById('fullscreen-container');
    const body = document.body;

    if (!isFullScreen) {
        enterFullScreen(fullscreenContainer, body);
    } else {
        exitFullScreen(fullscreenContainer, body);
    }

    // Trigger map resize
    setTimeout(() => {
        map.invalidateSize(true);
        if (editingLayer) {
            editingLayer.redraw();
        }
        // Force redraw of all layers
        map.eachLayer(function (layer) {
            if (layer.redraw) {
                layer.redraw();
            }
        });
    }, 350);
}

function enterFullScreen(fullscreenContainer, body) {
    // Store original map position
    originalMapPosition = {
        center: map.getCenter(),
        zoom: map.getZoom()
    };

    // Apply full screen classes
    fullscreenContainer.classList.add('fullscreen-active');
    body.classList.add('fullscreen-mode');

    // Update button
    const fullScreenBtn = document.getElementById('fullScreenBtn');
    fullScreenBtn.innerHTML = '<i class="fas fa-compress"></i> Exit Full Screen';
    fullScreenBtn.classList.add('active');
    fullScreenBtn.classList.remove('btn-outline-info');
    fullScreenBtn.classList.add('btn-warning');

    isFullScreen = true;

    showToast('Full screen mode activated - Complete immersive experience!', 'success');

    // Additional resize after a bit to ensure everything is properly sized
    setTimeout(() => {
        map.invalidateSize(true);
        map.setView(originalMapPosition.center, originalMapPosition.zoom);
    }, 500);
}

function exitFullScreen(fullscreenContainer, body) {
    // Remove full screen classes
    fullscreenContainer.classList.remove('fullscreen-active');
    body.classList.remove('fullscreen-mode');

    // Restore original map position if available
    if (originalMapPosition) {
        setTimeout(() => {
            map.setView(originalMapPosition.center, originalMapPosition.zoom);
        }, 100);
    }

    // Update button
    const fullScreenBtn = document.getElementById('fullScreenBtn');
    fullScreenBtn.innerHTML = '<i class="fas fa-expand-arrows-alt"></i> Full Screen';
    fullScreenBtn.classList.remove('active');
    fullScreenBtn.classList.remove('btn-warning');
    fullScreenBtn.classList.add('btn-outline-info');

    isFullScreen = false;

    showToast('Full screen mode deactivated', 'info');

    // Ensure map is properly resized after exiting full screen
    setTimeout(() => {
        map.invalidateSize(true);
    }, 300);
}

// Handle escape key to exit full screen
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isFullScreen) {
        toggleFullScreen();
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function () {
    if (document.hidden && isFullScreen) {
        toggleFullScreen();
    }
});

// Handle window resize
window.addEventListener('resize', function () {
    if (isFullScreen) {
        setTimeout(() => {
            map.invalidateSize(true);
        }, 100);
    }
});

// Initialize full screen capability check
function checkFullScreenSupport() {
    const doc = document.documentElement;
    return !!(doc.requestFullscreen || doc.webkitRequestFullscreen || doc.msRequestFullscreen);
}

// Show notification if full screen not supported
if (!checkFullScreenSupport()) {
    console.warn('Full screen API not fully supported in this browser');
}

// Layer control functions
function toggleSatelliteLayer() {
    const checked = document.getElementById('satelliteLayer').checked;
    if (checked) {
        map.addLayer(satelliteLayer);
    } else {
        map.removeLayer(satelliteLayer);
    }
}

function toggleStreetLayer() {
    const checked = document.getElementById('streetLayer').checked;
    if (checked) {
        map.addLayer(streetLayer);
    } else {
        map.removeLayer(streetLayer);
    }
}

function toggleHybridLayer() {
    const checked = document.getElementById('hybridLayer').checked;
    if (checked) {
        map.addLayer(hybridLayer);
    } else {
        map.removeLayer(hybridLayer);
    }
}

// function toggleDarkLayer() {
//     const checked = document.getElementById').checked;
//     if (checked) {
//         map.addLaye);
//     } else {
//         map.removeLaye);
//     }
// }

function toggleFarmLayer() {
    const checked = document.getElementById('farmLayer').checked;
    if (checked) {
        map.addLayer(farmLayers);
    } else {
        map.removeLayer(farmLayers);
    }
}

function setFarmLayerOpacity(opacity) {
    farmLayers.eachLayer(layer => {
        if (layer instanceof L.Polygon) {
            layer.setStyle({ fillOpacity: opacity * 0.5 });
        } else if (layer instanceof L.CircleMarker) {
            layer.setStyle({ fillOpacity: opacity * 0.8 });
        }
    });
}

// Utility functions
function fitToBounds() {
    const layers = farmLayers.getLayers();
    if (layers.length > 0) {
        const bounds = L.latLngBounds();
        let validBoundsCount = 0;

        layers.forEach(layer => {
            try {
                if (layer instanceof L.Polygon) {
                    const layerBounds = layer.getBounds();
                    if (layerBounds.isValid()) {
                        bounds.extend(layerBounds);
                        validBoundsCount++;
                    }
                } else if (layer.getLatLng) {
                    const latLng = layer.getLatLng();
                    if (latLng && latLng.lat && latLng.lng) {
                        bounds.extend(latLng);
                        validBoundsCount++;
                    }
                }
            } catch (error) {
                console.error('Error extending bounds for layer:', error);
            }
        });

        if (validBoundsCount > 0 && bounds.isValid()) {
            map.fitBounds(bounds, { padding: [20, 20] });
            console.log('Successfully fitted bounds for', validBoundsCount, 'layers');
        } else {
            console.warn('No valid bounds to fit');
            showToast('Could not fit map to farm boundaries', 'warning');
        }
    } else {
        showToast('No farms to display', 'info');
    }
}

function clearSelection() {
    map.closePopup();
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('searchInput').value = '';
    cancelEditing();
    showToast('Selection cleared', 'info');
}

function getStatusClass(status) {
    const classes = {
        'active': 'success',
        'delayed': 'warning',
        'critical': 'danger',
        'completed': 'info',
        'abandoned': 'secondary'
    };
    return classes[status] || 'secondary';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.zIndex = '10000';
    toast.style.minWidth = '300px';
    toast.style.textAlign = 'center';
    toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document.body.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

function showLoading(message) {
    // Simple loading implementation
    console.log('Loading:', message);
}

function hideLoading() {
    // Hide loading
    console.log('Loading complete');
}

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeMap);

// Close search results when clicking outside
document.addEventListener('click', function (e) {
    if (!e.target.closest('.search-container')) {
        document.getElementById('searchResults').style.display = 'none';
    }
});