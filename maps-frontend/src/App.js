import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Map from './components/Map';
import CitySelector from './components/CitySelector';
import './App.css';
import logger from './utils/logger';
import { v4 as uuidv4 } from 'uuid';

function App() {
    const [restaurants, setRestaurants] = useState([]);
    const [cities, setCities] = useState([]);
    const [error, setError] = useState(null);
    const [showCitySelector, setShowCitySelector] = useState(true);
    const [selectedCity, setSelectedCity] = useState(null);

    const API_URL = process.env.REACT_APP_API_URL || 
        (process.env.NODE_ENV === 'development' 
            ? 'http://63.177.129.94:8001'    // Development API
            : 'http://63.177.129.94:8000');    // Production API

    useEffect(() => {
        const sessionId = uuidv4();
        const userAgent = window.navigator.userAgent;
        const platform = window.navigator.platform;
        const screenSize = `${window.screen.width}x${window.screen.height}`;
        const language = window.navigator.language;
        const isMobile = /iPhone|iPad|iPod|Android/i.test(userAgent);

        logger.info('New session started', {
            event_type: 'session_start',
            session_id: sessionId,
            system_info: {
                user_agent: userAgent,
                platform: platform,
                screen_size: screenSize,
                language: language,
                device_type: isMobile ? 'mobile' : 'desktop',
                browser: getBrowserInfo(userAgent),
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
            }
        });

        localStorage.setItem('session_id', sessionId);

        // Add performance metrics
        const performance = window.performance;
        logger.info('Performance metrics', {
            event_type: 'performance',
            load_time: performance.timing.loadEventEnd - performance.timing.navigationStart,
            dom_ready: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            memory: performance.memory ? {
                used_js_heap: performance.memory.usedJSHeapSize,
                total_js_heap: performance.memory.totalJSHeapSize
            } : null
        });
    }, []);

    const getBrowserInfo = (userAgent) => {
        const browsers = {
            chrome: /chrome/i,
            safari: /safari/i,
            firefox: /firefox/i,
            opera: /opera/i,
            edge: /edge/i,
            ie: /msie|trident/i
        };

        for (const [browser, regex] of Object.entries(browsers)) {
            if (regex.test(userAgent)) {
                return browser;
            }
        }
        return 'unknown';
    };

    useEffect(() => {
        const fetchData = async () => {
            logger.info('Initiating data fetch');
            try {
                const [restaurantsRes, citiesRes] = await Promise.all([
                    axios.get(`${API_URL}/restaurants`),
                    axios.get(`${API_URL}/cities`)
                ]);
                
                logger.info('Data fetch successful', {
                    restaurantsCount: restaurantsRes.data.length,
                    citiesCount: citiesRes.data.length
                });
                
                setRestaurants(restaurantsRes.data);
                setCities(citiesRes.data);
            } catch (err) {
                logger.error('Error fetching data', err);
                setError(err.message);
            }
        };
        fetchData();
    }, [API_URL]);

    const handleCitySelect = (city) => {
        logger.info('City selected', { city });
        setSelectedCity(city);
        if (city) {
            setShowCitySelector(false);
        }
    };

    return (
        <div className="app-container">
            {error && <div className="error-message">Error: {error}</div>}
            {showCitySelector && (
                <CitySelector
                    cities={cities}
                    onSelectCity={handleCitySelect}
                    onClose={() => setShowCitySelector(false)}
                />
            )}
            {restaurants.length === 0 ? (
                <div>Loading restaurants...</div>
            ) : (
                <Map 
                    restaurants={restaurants}
                    selectedCity={selectedCity}
                />
            )}
        </div>
    );
}

export default App;