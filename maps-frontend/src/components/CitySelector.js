import React from 'react';
import './CitySelector.css';

function CitySelector({ cities, onSelectCity, onClose }) {
    return (
        <div className="city-selector-overlay">
            <div className="city-selector-container">
                <div className="content-container">
                    <div className="city-selector-description">
                        <h1>TikTok Restaurant Maps</h1>
                        <p>Discover restaurants that have gone viral on TikTok! Select a city to explore food spots that have been featured in popular TikTok videos.</p>
                    </div>
                    <h2>Select a City</h2>
                    <select 
                        onChange={(e) => onSelectCity(e.target.value)}
                        className="city-select"
                    >
                        <option value="">Choose a city...</option>
                        {cities.map((city, index) => (
                            <option key={index} value={city}>
                                {city}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
}

export default CitySelector;