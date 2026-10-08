/**
 * TRACE Map Configuration
 *
 * Keeps map tile provider, attribution, default center, and zoom bounds
 * centralized and easily configurable via environment variables or defaults.
 */

export const MAP_CONFIG = {
  // Tile Provider: Default OpenStreetMap standard tiles (No API key required)
  tileUrl:
    import.meta.env.VITE_MAP_TILE_URL ||
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',

  // Mandatory OpenStreetMap Attribution
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',

  // Default coordinate center (anchored to the demo observation cluster)
  defaultCenter: [51.505, -0.09] as [number, number],
  defaultZoom: 15,
  minZoom: 12,
  maxZoom: 18,
} as const;
