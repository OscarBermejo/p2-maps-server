import React from 'react';
import './CitySelector.css';

function CitySelector({ cities, onSelectCity, onClose }) {
    return (
        <div className="city-selector-overlay">
            <div className="city-selector-modal">
                <h2>Select a City</h2>
                <p>Choose a city to explore TikTok restaurants:</p>
                <select 
                    onChange={(e) => onSelectCity(e.target.value)}
                    className="city-select"
                    defaultValue=""
                >
                    <option value="" disabled>Select a city...</option>
                    {cities
                        .filter(city => city) // Remove any null or empty values
                        .sort() // Sort alphabetically
                        .map((city, index) => (
                            <option key={index} value={city}>
                                {city}
                            </option>
                    ))}
                </select>
                <button onClick={onClose} className="close-button">
                    Close
                </button>
            </div>
        </div>
    );
}

export default CitySelector;