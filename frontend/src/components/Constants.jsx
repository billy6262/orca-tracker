// Constants and global variables
import React, { createContext, useContext, useState } from 'react';


//context for the date picker for the charts page
const DateContext = createContext();

export const useDateRange = () => useContext(DateContext);

export const DateProvider = ({ children }) => {
    const [startDate, setStartDate] = useState(new Date(new Date().setDate(new Date().getDate() - 30))); // Default to 30 days ago
    const [endDate, setEndDate] = useState(new Date());

    const updateDate = (start, end) => {
        setStartDate(start);
        setEndDate(end);
    }

    const formatDate = (date) => date.toISOString().split('T')[0]; // YYYY-MM-DD format
 


    return (
        <DateContext.Provider value={{ startDate, endDate, updateDate, formatDate }}>
            {children}
        </DateContext.Provider>
    );
};
