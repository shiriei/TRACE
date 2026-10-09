import React, { useEffect, useRef, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, useMap, useMapEvents, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Trace } from '../../../types/trace';
import { MAP_CONFIG } from '../config';
import { TraceMarker } from './TraceMarker';
import { createPlacementIcon } from '../utils/markerIcons';

export interface PlacementState {
  mode: 'gps' | 'manual';
  position: [number, number]; // [lat, lng]
}

interface TraceMapProps {
  traces: Trace[];
  selectedTraceId?: string | null;
  onSelectTrace?: (trace: Trace) => void;
  recenterTrigger: number;
  onRecenter: () => void;
  placement?: PlacementState | null;
  onPlacementPositionChange?: (pos: [number, number]) => void;
  onConfirmPlacement?: () => void;
  onCancelPlacement?: () => void;
  isPlacingInProgress?: boolean;
  onDeleteTrace?: (trace: Trace) => void;
}

/**
 * Ensures Leaflet map fits bounds, animates recentering, pans to selected traces,
 * and handles container resizing while safely ignoring unplaced traces.
 */
const MapViewController: React.FC<{
  validTraces: Trace[];
  selectedTrace?: Trace | null;
  recenterTrigger: number;
  placement?: PlacementState | null;
}> = ({ validTraces, selectedTrace, recenterTrigger, placement }) => {
  const map = useMap();
  const isInitialMount = useRef(true);

  // Fits the map to the currently relevant trace markers
  const fitToTraces = useCallback(
    (animate = true) => {
      // If currently placing, focus on placement position
      if (placement) {
        map.setView(placement.position, 16, { animate });
        return;
      }

      if (!validTraces || validTraces.length === 0) {
        map.setView(MAP_CONFIG.defaultCenter, MAP_CONFIG.defaultZoom, { animate });
        return;
      }

      if (validTraces.length === 1) {
        map.setView([validTraces[0].latitude!, validTraces[0].longitude!], 16, { animate });
        return;
      }

      const bounds = L.latLngBounds(
        validTraces.map((t) => [t.latitude!, t.longitude!] as [number, number])
      );
      if (bounds.isValid()) {
        map.fitBounds(bounds, {
          padding: [60, 60],
          maxZoom: 16,
          animate,
        });
      }
    },
    [map, validTraces, placement]
  );

  // Initial bounds fit on mount with invalidateSize
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      const timer = setTimeout(() => {
        map.invalidateSize();
        if (validTraces.length > 0 && !placement) {
          fitToTraces(false);
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [map, fitToTraces, validTraces, placement]);

  // Re-fit when user clicks Recenter button or changes category filter
  useEffect(() => {
    if (recenterTrigger > 0) {
      fitToTraces(true);
    }
  }, [recenterTrigger, fitToTraces]);

  // Center smoothly on newly selected trace
  useEffect(() => {
    if (selectedTrace && selectedTrace.latitude != null && selectedTrace.longitude != null && !placement) {
      map.panTo([selectedTrace.latitude, selectedTrace.longitude], {
        animate: true,
        duration: 0.6,
      });
    }
  }, [selectedTrace, map, placement]);


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

/**
 * Handles map click interactions for placement mode.
 */
const MapPlacementHandler: React.FC<{
  placement: PlacementState | null;
  onPositionChange?: (pos: [number, number]) => void;
}> = ({ placement, onPositionChange }) => {
  const map = useMap();
  const prevMode = useRef<string | null>(null);

  useMapEvents({
    click: (e) => {
      if (placement && onPositionChange) {
        onPositionChange([e.latlng.lat, e.latlng.lng]);
      }
    },
  });

  // Pan to placement position when placement starts or mode switches
  useEffect(() => {
    if (placement && placement.mode !== prevMode.current) {
      prevMode.current = placement.mode;
      map.setView(placement.position, 16, { animate: true });
    } else if (!placement) {
      prevMode.current = null;
    }
  }, [placement, map]);

  return null;
};

export const TraceMap: React.FC<TraceMapProps> = ({
  traces,
  selectedTraceId,
  onSelectTrace,
  recenterTrigger,
  onRecenter,
  placement = null,
  onPlacementPositionChange,
  onConfirmPlacement,
  onCancelPlacement,
  isPlacingInProgress = false,
  onDeleteTrace,
}) => {
  // Exclude unplaced traces from map marker rendering and bounds calculations
  const validGeoTraces = useMemo(() => {
    return traces.filter(
      (t) =>
        t.latitude != null &&
        t.longitude != null &&
        !isNaN(t.latitude) &&
        !isNaN(t.longitude)
    );
  }, [traces]);

  const selectedTrace = validGeoTraces.find((t) => t.id === selectedTraceId) || null;

  return (
    <div className={`journal-map-wrapper ${placement ? 'journal-map-wrapper--placing' : ''}`}>
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
          validTraces={validGeoTraces}
          selectedTrace={selectedTrace}
          recenterTrigger={recenterTrigger}
          placement={placement}
        />

        <MapPlacementHandler
          placement={placement}
          onPositionChange={onPlacementPositionChange}
        />

        {/* Persistent Trace Markers */}
        {validGeoTraces.map((trace) => (
          <TraceMarker
            key={trace.id}
            trace={trace}
            isSelected={trace.id === selectedTraceId && !placement}
            onSelect={placement ? undefined : onSelectTrace}
            onDelete={onDeleteTrace}
          />
        ))}

        {/* Draggable Temporary Placement Marker */}
        {placement && (
          <Marker
            position={placement.position}
            draggable={true}
            icon={createPlacementIcon(placement.mode)}
            eventHandlers={{
              dragend: (e) => {
                const marker = e.target;
                const pos = marker.getLatLng();
                onPlacementPositionChange?.([pos.lat, pos.lng]);
              },
            }}
          />
        )}
      </MapContainer>

      {/* Interactive Placement Overlay Banner */}
      {placement && (
        <aside className="map-placement-banner" aria-label="Trace placement prompt">
          <div className="map-placement-banner-inner">
            <div className="map-placement-banner-text">
              {placement.mode === 'gps' ? (
                <>
                  <h3 className="map-placement-title">Your location</h3>
                  <p className="map-placement-hint">Drag the marker if you want to adjust it.</p>
                </>
              ) : (
                <>
                  <h3 className="map-placement-title">Place your trace</h3>
                  <p className="map-placement-hint">Choose where this discovery belongs on your map.</p>
                </>
              )}
            </div>

            <div className="map-placement-coords-tag">
              📍 {placement.position[0].toFixed(4)}° N, {Math.abs(placement.position[1]).toFixed(4)}° W
            </div>

            <div className="map-placement-actions">
              <button
                type="button"
                className="cta map-placement-confirm-btn"
                onClick={onConfirmPlacement}
                disabled={isPlacingInProgress}
                aria-busy={isPlacingInProgress}
              >
                {isPlacingInProgress ? 'Placing trace...' : 'Place Trace Here'}
              </button>
              {onCancelPlacement && (
                <button
                  type="button"
                  className="btn-secondary map-placement-cancel-btn"
                  onClick={onCancelPlacement}
                  disabled={isPlacingInProgress}
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </aside>
      )}

      {/* Recenter Map Floating Button */}
      {!placement && (
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
              <path d="M12 2v4M12 18v4M2 12h3M19 12h3" />
            </svg>
            <span className="recenter-text">Recenter map</span>
          </button>
        </div>
      )}

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



      {/* Empty State Overlay */}
      {validGeoTraces.length === 0 && !placement && (
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
