import React from 'react';
import { useTimeBucket } from './Constants.jsx';

const TimeBucketControl = () => {
  const { timeBucket, updateTimeBucket } = useTimeBucket();

  const buckets = Array.from({ length: 8 }, (_, i) => ({
    index: i,
    label: `${i * 6}-${(i + 1) * 6}h`
  }));

  return (
    <div
      style={{
        position: 'absolute',
        top: 136,        // just below navbar and map controlls
        left: 12,
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        padding: '8px',
        background: 'rgba(248,249,250,0.92)',
        border: '1px solid #d0d5da',
        borderRadius: '6px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
        maxHeight: `calc(100vh - 80px)`,
        overflowY: 'auto'
      }}
    >
      {buckets.map(b => {
        const active = timeBucket === b.index;
        return (
          <button
            key={b.index}
            type="button"
            aria-pressed={active}
            onClick={() => updateTimeBucket(b.index)}
            className={`btn btn-sm ${active ? 'btn-primary' : 'btn-outline-primary'}`}
            style={{
              minWidth: '68px',
              fontSize: '0.7rem',
              padding: '4px 6px',
              lineHeight: 1.1
            }}
          >
            {b.label}
          </button>
        );
      })}
    </div>
  );
};

export default TimeBucketControl;