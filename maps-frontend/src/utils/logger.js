const logger = {
    info: (message, data = {}) => {
        console.log(`[INFO] ${message}`, data);
        // You could add API call here to send logs to backend
    },
    error: (message, error = null) => {
        console.error(`[ERROR] ${message}`, error);
        // You could add API call here to send logs to backend
    },
    warn: (message, data = {}) => {
        console.warn(`[WARN] ${message}`, data);
        // You could add API call here to send logs to backend
    }
};

export default logger;