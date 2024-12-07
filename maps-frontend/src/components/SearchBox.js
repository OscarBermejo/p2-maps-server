import React, { useState } from 'react';
import './SearchBox.css';

function SearchBox({ restaurants, onSearch }) {
    const [searchTerm, setSearchTerm] = useState('');

    const handleSearch = (e) => {
        const value = e.target.value;
        setSearchTerm(value);
        
        // Filter restaurants based on search term
        const filtered = restaurants.filter(restaurant => 
            restaurant.name.toLowerCase().includes(value.toLowerCase()) ||
            restaurant.restaurant_type.toLowerCase().includes(value.toLowerCase()) ||
            restaurant.location.toLowerCase().includes(value.toLowerCase())
        );
        
        onSearch(filtered);
    };

    return (
        <div className="search-container">
            <input
                type="text"
                placeholder="Search restaurants..."
                value={searchTerm}
                onChange={handleSearch}
                className="search-input"
            />
        </div>
    );
}

export default SearchBox;