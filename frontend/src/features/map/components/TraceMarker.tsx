import React, { useMemo } from 'react';
import { Marker, Popup } from 'react-leaflet';
import { Trace } from '../../../types/trace';
import { createTraceIcon } from '../utils/markerIcons';
import { TraceDetailCard } from './TraceDetailCard';

interface TraceMarkerProps {
  trace: Trace;
  isSelected?: boolean;
  onSelect?: (trace: Trace) => void;
}

export const TraceMarker: React.FC<TraceMarkerProps> = ({
  trace,
  isSelected = false,
  onSelect,
}) => {
  if (
    trace.latitude == null ||
    trace.longitude == null ||
    isNaN(trace.latitude) ||
    isNaN(trace.longitude)
  ) {
    return null;
  }

  const icon = useMemo(() => {
    return createTraceIcon(trace.category, isSelected);
  }, [trace.category, isSelected]);

  return (
    <Marker
      position={[trace.latitude, trace.longitude]}
      icon={icon}
      eventHandlers={{
        click: () => {
          onSelect?.(trace);
        },
      }}
    >
      <Popup className="trace-custom-popup" closeButton={false}>
        <TraceDetailCard trace={trace} isCompact={true} />
      </Popup>
    </Marker>
  );
};
