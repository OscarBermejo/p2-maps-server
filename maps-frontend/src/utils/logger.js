import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://63.177.129.94:8000';

const logger = {
    info: (message, data = {}) => {
        const sessionId = localStorage.getItem('session_id');
        console.log(message, { ...data, session_id: sessionId });  // Keep console logging for development
        
        // Send to backend
        axios.post(`${API_URL}/log`, {
            level: 'INFO',
            message: message,
            data: {
                ...data,
                session_id: sessionId
            },
            timestamp: new Date().toISOString()
        }).catch(error => {
            console.error('Error sending log to backend:', error);
        });
    },
    
    error: (message, error = {}) => {
        const sessionId = localStorage.getItem('session_id');
        console.error(message, { ...error, session_id: sessionId });  // Keep console logging for development
        
        // Send to backend
        axios.post(`${API_URL}/log`, {
            level: 'ERROR',
            message: message,
            error: error.toString(),
            stack: error.stack,
            session_id: sessionId,
            timestamp: new Date().toISOString()
        }).catch(error => {
            console.error('Error sending log to backend:', error);
        });
    }
};

window.onerror = function(msg, url, lineNo, columnNo, error) {
    logger.error('JavaScript error', {
        message: msg,
        url: url,
        line: lineNo,
        column: columnNo,
        stack: error ? error.stack : null
    });
    return false;
};

export default logger;