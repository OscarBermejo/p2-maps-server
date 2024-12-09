import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Map from './components/Map';
import CitySelector from './components/CitySelector';
import './App.css';
import logger from './utils/logger';

function App() {
    const [restaurants, setRestaurants] = useState([]);
    const [cities, setCities] = useState([]);
    const [error, setError] = useState(null);
    const [showCitySelector, setShowCitySelector] = useState(true);
    const [selectedCity, setSelectedCity] = useState(null);

    const API_URL = process.env.REACT_APP_API_URL || 'http://52.59.148.23:8000';

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