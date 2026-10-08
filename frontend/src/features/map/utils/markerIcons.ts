import L from 'leaflet';
import { TraceCategory } from '../../../types/trace';

interface CategoryStyle {
  label: string;
  primaryColor: string;
  bgTint: string;
  borderColor: string;
  svgIcon: string;
}

/**
 * Whimsical field journal marker styling palette.
 * Inspired by botanical inks, field notebook stamps, and natural pigments.
 */
export const CATEGORY_STYLES: Record<TraceCategory, CategoryStyle> = {
  Nature: {
    label: 'Nature Finding',
    primaryColor: '#2d6a4f',
    bgTint: '#e8f5e9',
    borderColor: '#386641',
    // Delicate botanical leaf & seedling flourish
    svgIcon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="#2d6a4f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22v-9" />
        <path d="M12 13c3.5 0 6.5-2.5 7-7-4.5.5-7 3.5-7 7Z" fill="#a7c957" fill-opacity="0.35" />
        <path d="M12 17c-2.5 0-5-1.5-5.5-5 3.5.5 5 2.5 5.5 5Z" fill="#a7c957" fill-opacity="0.35" />
      </svg>
    `,
  },
  Sound: {
    label: 'Sound & Song Notice',
    primaryColor: '#b45309',
    bgTint: '#fef3c7',
    borderColor: '#92400e',
    // Whimsical musical resonance & birdsong waveform
    svgIcon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="#92400e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 10v4" />
        <path d="M7 7v10" />
        <path d="M11 4v16" />
        <path d="M15 8v8" />
        <path d="M19 6v12" />
        <path d="M22 11v2" />
      </svg>
    `,
  },
  Structure: {
    label: 'Masonry & Structure Finding',
    primaryColor: '#57534e',
    bgTint: '#f5f5f4',
    borderColor: '#44403c',
    // Hand-hewn stone arch & architectural geometry
    svgIcon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="#44403c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 20h16" />
        <path d="M6 20V10a6 6 0 0 1 12 0v10" fill="#e7e5e4" fill-opacity="0.5" />
        <path d="M10 20v-5a2 2 0 0 1 4 0v5" />
      </svg>
    `,
  },
  Mystery: {
    label: 'Mystery & Curio',
    primaryColor: '#6d28d9',
    bgTint: '#ede9fe',
    borderColor: '#5b21b6',
    // Star & keyhole curiosity mark
    svgIcon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="#5b21b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="#ddd6fe" fill-opacity="0.4" />
      </svg>
    `,
  },
  Personal: {
    label: 'Personal Observation',
    primaryColor: '#0369a1',
    bgTint: '#e0f2fe',
    borderColor: '#0284c7',
    // Storybook journal compass & quill point
    svgIcon: `
      <svg viewBox="0 0 24 24" fill="none" stroke="#0369a1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="#bae6fd" fill-opacity="0.4" />
      </svg>
    `,
  },
};

/**
 * Creates a custom illustrated Leaflet DivIcon for a field-journal pin.
 */
export function createTraceIcon(category: TraceCategory, isSelected: boolean = false): L.DivIcon {
  const style = CATEGORY_STYLES[category] || CATEGORY_STYLES.Personal;
  const size = isSelected ? 38 : 32;
  const selectedClass = isSelected ? 'field-pin--selected' : '';

  const html = `
    <div 
      class="field-pin-wrapper ${selectedClass}"
      data-category="${category}"
      aria-label="${style.label}"
      role="img"
    >
      <div 
        class="field-pin-disc"
        style="
          background-color: ${style.bgTint};
          border: 2px solid ${style.borderColor};
        "
      >
        <span class="field-pin-symbol" style="color: ${style.primaryColor};">
          ${style.svgIcon}
        </span>
      </div>
      <div class="field-pin-nib" style="border-top-color: ${style.borderColor};"></div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'field-journal-leaflet-icon',
    iconSize: [size, size + 8],
    iconAnchor: [size / 2, size + 8],
    popupAnchor: [0, -(size + 6)],
  });
}

/**
 * Creates a distinctive, draggable temporary marker for trace placement.
 */
export function createPlacementIcon(mode: 'gps' | 'manual'): L.DivIcon {
  const isGps = mode === 'gps';
  const color = isGps ? '#0284c7' : '#d97706';
  const bgTint = isGps ? '#f0f9ff' : '#fffbeb';
  const size = 44;

  const svgInner = isGps
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 22px; height: 22px;">
        <circle cx="12" cy="12" r="3.5" fill="${color}" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
      </svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 22px; height: 22px;">
        <path d="M12 21s-6-5.5-6-10a6 6 0 0 1 12 0c0 4.5-6 10-6 10z" fill="${color}" fill-opacity="0.3" />
        <circle cx="12" cy="11" r="2.5" fill="${color}" />
      </svg>`;

  const html = `
    <div class="field-placement-pin-wrapper">
      <div class="field-placement-pulse" style="border-color: ${color};"></div>
      <div class="field-placement-disc" style="background-color: ${bgTint}; border: 2.5px solid ${color};">
        <span class="field-placement-symbol">
          ${svgInner}
        </span>
      </div>
      <div class="field-placement-nib" style="border-top-color: ${color};"></div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'field-journal-placement-icon',
    iconSize: [size, size + 12],
    iconAnchor: [size / 2, size + 12],
  });
}
