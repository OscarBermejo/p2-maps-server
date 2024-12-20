import React, { useState, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import 'mapbox-gl/dist/mapbox-gl.css';
import './Map.css';
import logger from '../utils/logger';

// At the top of your file, after imports
console.log('Mapbox Token:', process.env.REACT_APP_MAPBOX_TOKEN);

// Make sure the token is set before using it
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || '';

// Add this helper function near the other helper functions, before the return statement
const formatTagName = (tagName) => {
    return tagName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
};

// Add this helper function next to it
const getPriceLevelLabel = (level) => '$'.repeat(level);

function Map({ restaurants, selectedCity }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const mapContainer = useRef(null);
    const map = useRef(null);
    const [lng] = useState(13.4050);
    const [lat] = useState(52.5200);
    const [zoom] = useState(5);
    const markers = useRef([]);
    const [isMenuVisible, setIsMenuVisible] = useState(false);
    const activePopup = useRef(null);
    const [visitedRestaurants, setVisitedRestaurants] = useState(new Set());
    const [tags, setTags] = useState([]);
    const [selectedTags, setSelectedTags] = useState(new Set());
    const [filteredRestaurants, setFilteredRestaurants] = useState([]);
    const [selectedPriceLevels, setSelectedPriceLevels] = useState(new Set());

    // Initialize map
    useEffect(() => {
        if (map.current) return;

        map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/dark-v11',
            center: [lng, lat],
            zoom: zoom
        });

    }, [lng, lat, zoom]);

    // Add effect to handle city selection
    useEffect(() => {
        if (!map.current || !selectedCity) return;

        const flyToCity = async () => {
            logger.info(`City selected: ${selectedCity}`, {
                event_type: 'city_selection',
                city: selectedCity,
                timestamp: new Date().toISOString()
            });
            try {
                const response = await axios.get(
                    `https://api.mapbox.com/geocoding/v5/mapbox.places/${selectedCity}.json?access_token=${mapboxgl.accessToken}`
                );
                
                if (response.data.features.length > 0) {
                    const coordinates = response.data.features[0].center;
                    logger.info('City coordinates found', { coordinates });
                    map.current.flyTo({
                        center: coordinates,
                        zoom: 12,
                        essential: true
                    });
                }
            } catch (error) {
                logger.error('Error getting city coordinates', error);
            }
        };

        flyToCity();
    }, [selectedCity]);

    // Add this effect to handle clicks anywhere in the map container
    useEffect(() => {
        if (!mapContainer.current) return;

        // Store ref in a variable to use in cleanup
        const mapContainerElement = mapContainer.current;

        const handleOutsideClick = (e) => {
            if (activePopup.current) {
                const clickedMarker = e.target.closest('.custom-marker');
                const clickedPopup = e.target.closest('.mapboxgl-popup');
                const clickedPopupClose = e.target.closest('.mapboxgl-popup-close-button');

                if (!clickedMarker && !clickedPopup && !clickedPopupClose) {
                    activePopup.current.remove();
                    activePopup.current = null;
                }
            }
        };

        // Use stored reference
        mapContainerElement.addEventListener('click', handleOutsideClick);

        return () => {
            // Use stored reference in cleanup
            if (mapContainerElement) {
                mapContainerElement.removeEventListener('click', handleOutsideClick);
            }
        };
    }, []);

    // Add markers when restaurants data changes
    useEffect(() => {
        if (!map.current || !filteredRestaurants.length) return;

        // Clear existing markers
        markers.current.forEach(marker => marker.remove());
        markers.current = [];

        filteredRestaurants.forEach((restaurant) => {
            const coordinates = restaurant.coordinates.split(',').map(Number);

            // Create popup content
            const popupContent = document.createElement('div');
            popupContent.className = 'popup-container';
            popupContent.innerHTML = `
                <h3 class="popup-title">${restaurant.name}</h3>
                <p class="popup-text">${restaurant.location}</p>
                <p class="popup-text">
                    <span>Tel: ${restaurant.phone || 'Not available'}</span>
                    ${restaurant.rating ? ` • Rating: ${restaurant.rating}` : ''}
                    ${restaurant.price_level ? ` • Price: ${'$'.repeat(restaurant.price_level)}` : ''}
                </p>
            `;

            // Add videos if available
            if (restaurant.video_urls && restaurant.video_urls.length > 0) {
                const videosContainer = document.createElement('div');
                videosContainer.className = `videos-scroll-container ${restaurant.video_urls.length === 1 ? 'single-video' : ''}`;
                restaurant.video_urls.forEach((url, index) => {
                    const videoId = url.split('/video/')[1];
                    const embedUrl = `https://www.tiktok.com/embed/v2/${videoId}`;
                    
                    videosContainer.innerHTML += `
                        <div class="video-item">
                            <div class="video-wrapper">
                                <iframe
                                    src="${embedUrl}"
                                    class="tiktok-embed"
                                    allowFullScreen
                                    scrolling="no"
                                    title="TikTok video ${index + 1} for ${restaurant.name}"
                                ></iframe>
                            </div>
                        </div>
                    `;
                });
                popupContent.appendChild(videosContainer);
            }

            // Create popup
            const popup = new mapboxgl.Popup({
                maxWidth: '220px',
                className: 'custom-popup',
                closeButton: true,
                closeOnClick: false,
                anchor: 'center',
                offset: [0, 0]
            })
            .setLngLat(map.current.getCenter())
            .setDOMContent(popupContent);

            // Add event listener when popup closes
            popup.on('close', () => {
                activePopup.current = null;
            });

            // Create marker and add click event
            const el = document.createElement('div');
            el.className = `custom-marker${visitedRestaurants.has(restaurant.id) ? ' visited' : ''}`;

            const marker = new mapboxgl.Marker(el)
                .setLngLat([coordinates[1], coordinates[0]])
                .addTo(map.current);

            marker.getElement().addEventListener('click', () => {
                logger.info(`Restaurant clicked: ${restaurant.name} (ID: ${restaurant.id})`, {
                    event_type: 'restaurant_click',
                    restaurant: {
                        id: restaurant.id,
                        name: restaurant.name,
                        location: restaurant.location,
                        coordinates: restaurant.coordinates,
                        rating: restaurant.rating,
                        price_level: restaurant.price_level
                    }
                });
                // Log the restaurant click
                logger.info('Restaurant clicked', { restaurantId: restaurant.id, restaurantName: restaurant.name });

                // Mark restaurant as visited
                setVisitedRestaurants(prev => new Set(prev).add(restaurant.id));
                el.classList.add('visited');

                // If there's already an active popup, remove it
                if (activePopup.current) {
                    activePopup.current.remove();
                }

                // First center the map on the marker
                map.current.flyTo({
                    center: [coordinates[1], coordinates[0]],
                    zoom: map.current.getZoom(),
                    duration: 500  // Animation duration in milliseconds
                });

                // Wait for the map movement to finish before showing the popup
                setTimeout(() => {
                    // Show popup in center of screen
                    popup.setLngLat(map.current.getCenter()).addTo(map.current);
                    activePopup.current = popup;
                }, 500); // This timeout should match the flyTo duration
            });

            markers.current.push(marker);
        });

        return () => {
            markers.current.forEach(marker => marker.remove());
            markers.current = [];
            if (activePopup.current) {
                activePopup.current.remove();
                activePopup.current = null;
            }
        };
    }, [filteredRestaurants, visitedRestaurants]);

    const handleSearch = async (term) => {
        logger.info('Search performed', {
            event_type: 'search',
            search_term: term,
            results_count: searchResults.length
        });
        setSearchTerm(term);
        
        if (term.length > 2) {
            try {
                const response = await axios.get(
                    `https://api.mapbox.com/geocoding/v5/mapbox.places/${term}.json?access_token=${mapboxgl.accessToken}`
                );
                
                const locations = response.data.features.map(feature => ({
                    type: 'location',
                    name: feature.place_name,
                    coordinates: feature.center
                }));

                const filteredRestaurants = restaurants.filter(restaurant => 
                    restaurant.name.toLowerCase().includes(term.toLowerCase()) ||
                    restaurant.location.toLowerCase().includes(term.toLowerCase())
                ).map(r => ({
                    ...r,
                    type: 'restaurant'
                }));

                setSearchResults([...filteredRestaurants, ...locations]);
                logger.info('Search completed', { 
                    resultsCount: searchResults.length 
                });
            } catch (error) {
                logger.error('Error searching locations', error);
            }
        } else {
            setSearchResults([]);
        }
    };

    const handleResultSelect = (result) => {
        logger.info('Search result selected', {
            event_type: 'search_selection',
            selected_item: {
                type: result.type,
                name: result.name
            }
        });
        if (result.type === 'location') {
            map.current.flyTo({
                center: result.coordinates,
                zoom: 14
            });
        } else {
            const coordinates = result.coordinates.split(',').map(Number);
            map.current.flyTo({
                center: [coordinates[1], coordinates[0]],
                zoom: 14
            });
        }
        setSearchResults([]);
        setSearchTerm(result.name);
    };

    const handleTagClick = (tagId) => {
        setSelectedTags(prev => {
            const newTags = new Set(prev);
            if (newTags.has(tagId)) {
                newTags.delete(tagId);
            } else {
                newTags.add(tagId);
            }
            return newTags;
        });
    };

    useEffect(() => {
        const fetchTags = async () => {
            try {
                const apiUrl = process.env.NODE_ENV === 'development' 
                    ? 'http://localhost:8001' 
                    : 'http://63.177.129.94:8000';
                console.log('Fetching tags from:', `${apiUrl}/tags`);
                
                const response = await axios.get(`${apiUrl}/tags`);
                console.log('Tags fetched successfully:', response.data);
                setTags(response.data);
            } catch (error) {
                logger.error('Error fetching tags:', {
                    error: error.message,
                    status: error.response?.status,
                    data: error.response?.data,
                    config: error.config
                });
            }
        };
        fetchTags();
    }, []);

    useEffect(() => {
        let filtered = restaurants;
        
        // Filter by tags if any are selected
        if (selectedTags.size > 0) {
            filtered = filtered.filter(restaurant => 
                restaurant.tags?.some(tag => selectedTags.has(tag.id))
            );
        }
        
        // Filter by price levels if any are selected
        if (selectedPriceLevels.size > 0) {
            filtered = filtered.filter(restaurant => 
                restaurant.price_level && selectedPriceLevels.has(restaurant.price_level)
            );
        }
        
        setFilteredRestaurants(filtered);
    }, [restaurants, selectedTags, selectedPriceLevels]);

    const handlePriceLevelClick = (level) => {
        setSelectedPriceLevels(prev => {
            const newLevels = new Set(prev);
            if (newLevels.has(level)) {
                newLevels.delete(level);
            } else {
                newLevels.add(level);
            }
            return newLevels;
        });
    };

    return (
        <div className="map-wrapper">
            <button 
                className="menu-toggle-button" 
                onClick={() => setIsMenuVisible(!isMenuVisible)}
            >
                {isMenuVisible ? '×' : '☰'}
            </button>

            <div className={`left-container ${isMenuVisible ? 'visible' : ''}`}>
                <div className="title-search-container">
                    <h1 className="map-title">TikTok Restaurant Map</h1>
                    <div className="search-container">
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Search restaurants or locations..."
                            value={searchTerm}
                            onChange={(e) => handleSearch(e.target.value)}
                        />
                        
                        {searchResults.length > 0 && (
                            <div className="search-results">
                                {searchResults.map((result, index) => (
                                    <div
                                        key={index}
                                        onClick={() => handleResultSelect(result)}
                                        className="search-result-item"
                                    >
                                        <span>{result.type === 'restaurant' ? '🍽️' : '📍'}</span>
                                        <div>{result.name}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Price level filters without title */}
                    <div className="filter-section">
                        <div className="tags-container">
                            {[1, 2, 3, 4].map(level => (
                                <button
                                    key={`price-${level}`}
                                    className={`tag-button ${selectedPriceLevels.has(level) ? 'selected' : ''}`}
                                    onClick={() => handlePriceLevelClick(level)}
                                >
                                    {getPriceLevelLabel(level)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Tags container without title */}
                    <div className="filter-section">
                        <div className="tags-container">
                            {tags.map(tag => (
                                <button
                                    key={tag.id}
                                    className={`tag-button ${selectedTags.has(tag.id) ? 'selected' : ''}`}
                                    onClick={() => handleTagClick(tag.id)}
                                >
                                    {formatTagName(tag.name)}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
            <div ref={mapContainer} className="map-container" />
        </div>
    );
}

export default Map;