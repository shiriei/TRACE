import React, { useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Trace } from '../../../types/trace';
import { MAP_CONFIG } from '../config';
import { TraceMarker } from './TraceMarker';

interface TraceMapProps {
  traces: Trace[];
  selectedTraceId?: string | null;
  onSelectTrace?: (trace: Trace) => void;
  recenterTrigger: number;
  onRecenter: () => void;
}

/**
 * Ensures Leaflet map fits bounds, animates recentering, pans to selected traces,
 * and handles container resizing.
 */
const MapViewController: React.FC<{
  traces: Trace[];
  selectedTrace?: Trace | null;
  recenterTrigger: number;
}> = ({ traces, selectedTrace, recenterTrigger }) => {
  const map = useMap();
  const isInitialMount = useRef(true);

  // Fits the map to the currently relevant trace markers
  const fitToTraces = useCallback(
    (animate = true) => {
      if (!traces || traces.length === 0) {
        map.setView(MAP_CONFIG.defaultCenter, MAP_CONFIG.defaultZoom, { animate });
        return;
      }

      if (traces.length === 1) {
        map.setView([traces[0].latitude, traces[0].longitude], 16, { animate });
        return;
      }

      const bounds = L.latLngBounds(
        traces.map((t) => [t.latitude, t.longitude] as [number, number])
      );
      map.fitBounds(bounds, {
        padding: [60, 60],
        maxZoom: 16,
        animate,
      });
    },
    [map, traces]
  );

  // Initial bounds fit on mount
  useEffect(() => {
    if (isInitialMount.current && traces.length > 0) {
      fitToTraces(false);
      isInitialMount.current = false;
    }
  }, [fitToTraces, traces]);

  // Re-fit when user clicks the Recenter button
  useEffect(() => {
    if (recenterTrigger > 0) {
      fitToTraces(true);
    }
  }, [recenterTrigger, fitToTraces]);

  // Re-fit when category filter changes trace count/list
  useEffect(() => {
    if (!isInitialMount.current) {
      fitToTraces(true);
    }
  }, [traces, fitToTraces]);

  // Center smoothly on newly selected trace
  useEffect(() => {
    if (selectedTrace) {
      map.panTo([selectedTrace.latitude, selectedTrace.longitude], {
        animate: true,
        duration: 0.6,
      });
    }
  }, [selectedTrace, map]);

  // Handle window and container resize
  useEffect(() => {
    const handleResize = () => {
      map.invalidateSize();
    };

    window.addEventListener('resize', handleResize);
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);

    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timer);
    };
  }, [map]);

  return null;
};

export const TraceMap: React.FC<TraceMapProps> = ({
  traces,
  selectedTraceId,
  onSelectTrace,
  recenterTrigger,
  onRecenter,
}) => {
  const selectedTrace = traces.find((t) => t.id === selectedTraceId) || null;

  return (
    <div className="journal-map-wrapper">
      <MapContainer
        center={MAP_CONFIG.defaultCenter}
        zoom={MAP_CONFIG.defaultZoom}
        minZoom={MAP_CONFIG.minZoom}
        maxZoom={MAP_CONFIG.maxZoom}
        scrollWheelZoom={true}
        className="journal-leaflet-map"
      >
        <TileLayer
          url={MAP_CONFIG.tileUrl}
          attribution={MAP_CONFIG.attribution}
        />

        <MapViewController
          traces={traces}
          selectedTrace={selectedTrace}
          recenterTrigger={recenterTrigger}
        />

        {traces.map((trace) => (
          <TraceMarker
            key={trace.id}
            trace={trace}
            isSelected={trace.id === selectedTraceId}
            onSelect={onSelectTrace}
          />
        ))}
      </MapContainer>

      {/* Recenter Map Floating Button */}
      <div className="map-overlay-recenter">
        <button
          type="button"
          className="journal-recenter-btn"
          onClick={onRecenter}
          title="Recenter map to all visible discoveries"
          aria-label="Recenter map view"
        >
          <svg
            className="recenter-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            width="15"
            height="15"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
          </svg>
          <span className="recenter-text">Recenter map</span>
        </button>
      </div>

      {/* Unexplored Territory Inset Badge */}
      <div className="map-overlay-unexplored">
        <div className="map-unexplored-card">
          <svg className="unexplored-dashed-orbit" viewBox="0 0 28 28" fill="none">
            <circle cx="14" cy="14" r="10" stroke="#8c7c6e" strokeWidth="1.5" strokeDasharray="3 2" />
            <circle cx="14" cy="14" r="3" fill="#2d6a4f" />
          </svg>
          <div className="unexplored-copy">
            <span className="unexplored-label">Unexplored</span>
            <span className="unexplored-sublabel">territory</span>
          </div>
        </div>
      </div>

      {/* Illustrated Compass Rose Badge */}
      <div className="map-overlay-compass" aria-hidden="true" title="Living Cartography Compass">
        <svg viewBox="0 0 44 44" fill="none" width="40" height="40">
          <circle cx="22" cy="22" r="18" stroke="#8c7c6e" strokeWidth="1" strokeDasharray="2 2" />
          <polygon points="22 6 25 22 22 20 19 22 22 6" fill="#b45309" stroke="#78350f" strokeWidth="0.8" />
          <polygon points="22 38 25 22 22 24 19 22 22 38" fill="#e7e5e4" stroke="#78716c" strokeWidth="0.8" />
          <polygon points="6 22 22 25 20 22 22 19 6 22" fill="#e7e5e4" stroke="#78716c" strokeWidth="0.8" />
          <polygon points="38 22 22 25 24 22 22 19 38 22" fill="#e7e5e4" stroke="#78716c" strokeWidth="0.8" />
          <circle cx="22" cy="22" r="2.5" fill="#2c221b" />
          <text x="22" y="5" fontSize="6" fontWeight="bold" textAnchor="middle" fill="#78350f" fontFamily="serif">N</text>
        </svg>
      </div>

      {/* Empty State Overlay */}
      {traces.length === 0 && (
        <div className="journal-map-empty-overlay">
          <div className="journal-empty-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="32" height="32">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            <h4>No discoveries in this category</h4>
            <p>Select &ldquo;All&rdquo; or click Recenter to view all discoveries.</p>
            <button
              type="button"
              className="btn-secondary"
              onClick={onRecenter}
              style={{ marginTop: '0.75rem' }}
            >
              Reset View
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
