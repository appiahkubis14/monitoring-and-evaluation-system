  // Update opacity value display
                            document.getElementById('baseOpacitySlider').addEventListener('input', function(e) {
                                document.getElementById('baseOpacityValue').textContent = e.target.value + '%';
                            });

                            // Handle layer selection
                            document.querySelectorAll('.layer-radio').forEach(radio => {
                                radio.addEventListener('change', function(e) {
                                    // Update visual selection state
                                    document.querySelectorAll('.layer-card').forEach(card => {
                                        card.classList.remove('active');
                                    });
                                    e.target.closest('.layer-card').classList.add('active');
                                    
                                    // Here you would typically update the map base layer
                                    const layerType = e.target.id.replace('Layer', '').toLowerCase();
                                    console.log('Selected base layer:', layerType);
                                    
                                    // Dispatch custom event for map integration
                                    const event = new CustomEvent('basemapChange', {
                                        detail: { layer: layerType, opacity: document.getElementById('baseOpacitySlider').value }
                                    });
                                    document.dispatchEvent(event);
                                });
                            });

                            // Toggle section visibility
                            document.querySelector('.section-header').addEventListener('click', function() {
                                const content = document.getElementById('base-maps-section');
                                const icon = this.querySelector('.toggle-icon');
                                
                                content.classList.toggle('collapsed');
                                this.classList.toggle('active');
                            });

                            // Handle image loading
                            document.querySelectorAll('.layer-image').forEach(img => {
                                img.addEventListener('load', function() {
                                    this.classList.add('loaded');
                                });
                                
                                // Fallback for error handling
                                img.addEventListener('error', function() {
                                    console.warn('Failed to load layer image:', this.src);
                                    // You could set a fallback background color or pattern here
                                    this.style.background = 'var(--bs-secondary-bg)';
                                    this.style.display = 'flex';
                                    this.style.alignItems = 'center';
                                    this.style.justifyContent = 'center';
                                    this.innerHTML = '<i class="fas fa-map" style="font-size: 24px; color: var(--bs-muted-color);"></i>';
                                });
                            });

                            // Initialize first layer as active
                            document.querySelector('.layer-radio:checked').closest('.layer-card').classList.add('active');

                            // Handle opacity changes
                            document.getElementById('baseOpacitySlider').addEventListener('change', function(e) {
                                const event = new CustomEvent('opacityChange', {
                                    detail: { opacity: e.target.value }
                                });
                                document.dispatchEvent(event);
                            });