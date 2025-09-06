import React, { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { useDateRange } from "./Constants";


const ChartsDateBar = () => {
    const { startDate, endDate, updateDate, formatDate } = useDateRange();
    return (    
      <div className="container-fluid py-2">
        <div className="card border-0 shadow-sm">
          <div className="card-body py-3">
            <h6 className="text-uppercase text-muted fw-semibold small mb-3">Date Range</h6>
            <div className="row g-3 align-items-end">
              <div className="col-md-6">
                <label className="form-label mb-1 small text-secondary">Start</label>
                <DatePicker
                  selected={startDate}
                  onChange={(date) => updateDate(date, endDate)}
                  selectsStart
                  startDate={startDate}
                  endDate={endDate}
                  maxDate={endDate}
                  className="form-control form-control-sm"
                  dateFormat="yyyy-MM-dd"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label mb-1 small text-secondary">End</label>
                <DatePicker
                  selected={endDate}
                  onChange={(date) => updateDate(startDate, date)}
                  selectsEnd
                  startDate={startDate}
                  endDate={endDate}
                  minDate={startDate}
                  maxDate={new Date()}
                  className="form-control form-control-sm"
                  dateFormat="yyyy-MM-dd"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
};

export default ChartsDateBar;
