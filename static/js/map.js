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
    let satelliteLayer, streetLayer;
    
    // Status colors
    const statusColors = {
        'active': '#28a745',
        'delayed': '#ffc107',
        'critical': '#dc3545',
        'completed': '#17a2b8',
        'abandoned': '#6c757d'
    };
    
    // Initialize map
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
        
        // Add default layers
        streetLayer.addTo(map);
        satelliteLayer.addTo(map);
        
        // Add farm layers group
        farmLayers.addTo(map);
        
        // Add scale control
        L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
        
        // Load farm data
        loadFarmData();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize panel sections
        initializePanelSections();
    }
    
    // Initialize panel sections with toggle functionality
function initializePanelSections() {
    // Only set active sections for sections that exist in the controls panel
    const layersSection = document.getElementById('layers-section');
    const opacitySection = document.getElementById('opacity-section');
    const legendSection = document.getElementById('legend-section');
    const toolsSection = document.getElementById('tools-section');
    
    // Set initial active sections only if they exist
    if (layersSection) layersSection.classList.add('active');
    if (opacitySection) opacitySection.classList.add('active');
    
    // Add click handlers to section headers that exist
    document.querySelectorAll('.section-header').forEach(header => {
        const targetId = header.getAttribute('data-toggle');
        const sectionContent = document.getElementById(targetId);
        
        // Only add event listener if the target section exists
        if (sectionContent) {
            header.addEventListener('click', function() {
                const isActive = sectionContent.classList.contains('active');
                
                // Toggle active class
                this.classList.toggle('active');
                sectionContent.classList.toggle('active');
            });
        }
    });
    
    // Panel toggle functionality
    const togglePanelBtn = document.getElementById('togglePanel');
    if (togglePanelBtn) {
        togglePanelBtn.addEventListener('click', function() {
            const panel = document.querySelector('.map-controls-panel');
            if (panel) {
                panel.classList.toggle('collapsed');
                
                // Update icon
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
    
    // Setup event listeners
    // Setup event listeners
function setupEventListeners() {
    // Search functionality
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);
    document.getElementById('searchInput').addEventListener('input', handleSearchInput);
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') performSearch();
        if (e.key === 'Escape') clearSearch();
    });
    
    // Layer controls
    document.getElementById('satelliteLayer').addEventListener('change', toggleSatelliteLayer);
    document.getElementById('streetLayer').addEventListener('change', toggleStreetLayer);
    document.getElementById('farmLayer').addEventListener('change', toggleFarmLayer);
    
    // Opacity control
    document.getElementById('opacitySlider').addEventListener('input', function(e) {
        const opacity = e.target.value / 100;
        document.getElementById('opacityValue').textContent = `${e.target.value}%`;
        setFarmLayerOpacity(opacity);
    });
    
    // Map tools
    document.getElementById('refreshMap').addEventListener('click', loadFarmData);
    document.getElementById('fitToBounds').addEventListener('click', fitToBounds);
    document.getElementById('clearSelection').addEventListener('click', clearSelection);
    document.getElementById('fullScreenBtn').addEventListener('click', toggleFullScreen);
    
    // Edit boundary buttons
    document.getElementById('editBoundaryBtn').addEventListener('click', startEditingBoundary);
    document.getElementById('saveBoundaryBtn').addEventListener('click', saveBoundaryChanges);
    document.getElementById('cancelEditBtn').addEventListener('click', cancelEditing);

    window.addEventListener('resize', function() {
        if (isFullScreen) {
            setTimeout(() => {
                map.invalidateSize(true);
            }, 100);
        }
    });
}

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
document.addEventListener('keydown', function(e) {
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
    
    switch(e.key) {
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
// Close search results when clicking outside
document.addEventListener('click', function(e) {
    const searchContainer = document.querySelector('.search-top-container');
    const searchResults = document.getElementById('searchResults');
    
    // Check if search elements exist and if click is outside
    if (searchContainer && searchResults && searchResults.style.display !== 'none') {
        if (!searchContainer.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    }
});


    
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
    
    // Render farms on map
    function renderFarmsOnMap() {
        // Clear existing layers
        farmLayers.clearLayers();
        
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
                        layer = L.polygon(leafletCoords, {
                            color: statusColors[farm.status] || '#6c757d',
                            fillColor: statusColors[farm.status] || '#6c757d',
                            fillOpacity: 0.5,
                            weight: 2,
                            farmId: farm.id
                        });
                        
                        // Add popup
                        layer.bindPopup(createFarmPopup(farm));
                        
                        // Add click event
                        layer.on('click', function(e) {
                            L.DomEvent.stopPropagation(e);
                            showFarmDetails(farm.id);
                        });
                        
                        farmLayers.addLayer(layer);
                        console.log('Successfully created polygon for farm', farm.id);
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
                    
                    layer = L.circleMarker(coords, {
                        radius: 8,
                        fillColor: statusColors[farm.status] || '#6c757d',
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8,
                        farmId: farm.id
                    });
                    
                    // Add popup
                    layer.bindPopup(createFarmPopup(farm));
                    
                    // Add click event
                    layer.on('click', function(e) {
                        L.DomEvent.stopPropagation(e);
                        showFarmDetails(farm.id);
                    });
                    
                    farmLayers.addLayer(layer);
                    console.log('Successfully created marker for farm', farm.id);
                    
                } catch (error) {
                    console.error('Error creating marker for farm:', farm.id, error);
                }
            }
            
            if (!layer) {
                console.warn('Could not create any layer for farm:', farm.id);
            }
        });
        
        // Fit map to show all farms if we have any
        const layers = farmLayers.getLayers();
        if (layers.length > 0) {
            console.log('Fitting bounds for', layers.length, 'layers');
            fitToBounds();
        } else {
            console.warn('No layers were created');
            showToast('No farm boundaries could be displayed', 'warning');
        }
    }
    
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
                <small class="text-muted"><em>Click for details</em></small>
            </div>
        </div>
    `;
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
            ${farm.has_boundary ? '<div class="alert alert-info mt-3"><small><i class="fas fa-info-circle"></i> This farm has boundary data available for editing.</small></div>' : ''}
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

        vertexMarker.on('drag', function(e) {
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
    

    
    // Toggle full screen mode
//     function toggleFullScreen() {
//     const mapContainer = document.getElementById('map');
//     const controlsPanel = document.querySelector('.map-controls-panel');
    
//     if (!isFullScreen) {
//         // Enter full screen
//         mapContainer.classList.add('fullscreen-map');
//         document.body.style.overflow = 'hidden';
//         isFullScreen = true;
        
//         // Ensure controls stay on top
//         controlsPanel.style.zIndex = '10000';
        
//         // Store original position
//         originalMapPosition = {
//             center: map.getCenter(),
//             zoom: map.getZoom()
//         };
        
//         // Update button
//         document.getElementById('fullScreenBtn').innerHTML = '<i class="fas fa-compress"></i> Exit Full Screen';
        
//         showToast('Full screen mode activated', 'info');
//     } else {
//         // Exit full screen
//         mapContainer.classList.remove('fullscreen-map');
//         document.body.style.overflow = '';
//         isFullScreen = false;
        
//         // Reset z-index
//         controlsPanel.style.zIndex = '1000';
        
//         // Restore original position if available
//         if (originalMapPosition) {
//             map.setView(originalMapPosition.center, originalMapPosition.zoom);
//         }
        
//         // Update button
//         document.getElementById('fullScreenBtn').innerHTML = '<i class="fas fa-expand-arrows-alt"></i> Full Screen';
        
//         showToast('Full screen mode deactivated', 'info');
//     }
    
//     // Trigger map resize with a slight delay
//     setTimeout(() => {
//         map.invalidateSize(true);
//         if (editingLayer) {
//             editingLayer.redraw();
//         }
//     }, 350);
// }

// Global variables
// let isFullScreen = false;
// let originalMapPosition = null;

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
        map.eachLayer(function(layer) {
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
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isFullScreen) {
        toggleFullScreen();
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden && isFullScreen) {
        toggleFullScreen();
    }
});

// Handle window resize
window.addEventListener('resize', function() {
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
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container')) {
            document.getElementById('searchResults').style.display = 'none';
        }
    });