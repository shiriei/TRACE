import { Trace } from '../types/trace';

/**
 * TRACE Development / Demo Dataset (Phase 1 Revision)
 *
 * Clearly isolated, fictional, and neutral example observations used exclusively
 * to verify map rendering, marker interaction, category filtering, and Field Note presentation.
 *
 * Media captures are empty in Phase 1 demo data (`media: []`) to avoid fabricating
 * fake audio/video files.
 */
export const DEMO_TRACES: readonly Trace[] = [
  {
    id: 'demo-trace-01',
    title: 'Moss growing through concrete',
    description: 'Dense emerald bryophyte colonizing the expansion joint between walkway slabs.',
    category: 'Nature',
    latitude: 51.5065,
    longitude: -0.0915,
    createdAt: '2026-10-04T09:14:00Z',
    observation: 'Cool and damp to touch. Tiny spore capsules stand upright on crimson stalks despite constant foot traffic.',
    userNotes: 'Reminded me how living things reclaim stone when given even a millimeter of rain.',
    tags: ['bryophyte', 'urban-botany', 'resilience'],
    media: [],
  },
  {
    id: 'demo-trace-02',
    title: 'Three different bird calls near the same lane',
    description: 'Overlapping acoustic cadences resonating from an overgrown hawthorn hedgerow.',
    category: 'Sound',
    latitude: 51.5082,
    longitude: -0.0880,
    createdAt: '2026-10-05T07:42:00Z',
    observation: 'A rapid low trill, followed by a double whistling cadence, answered by a soft rhythmic tapping from deep within the brambles.',
    userNotes: 'Stood quiet under the canopy for ten minutes. The traffic sound seemed to fade behind their calls.',
    tags: ['birdsong', 'hedgerow', 'morning-sound'],
    media: [],
  },
  {
    id: 'demo-trace-03',
    title: 'Unusual drainage pattern',
    description: 'Hexagonal runoff channels hand-chiseled into weathered limestone curbing.',
    category: 'Structure',
    latitude: 51.5038,
    longitude: -0.0932,
    createdAt: '2026-10-06T15:20:00Z',
    observation: 'Instead of flowing directly into the modern gutter, rain runoff spirals into a subterranean stone culvert grate.',
    userNotes: 'Curious why hexagonal geometry was used here. The masonry looks late Victorian.',
    tags: ['curbing', 'masonry', 'hydrology'],
    media: [],
  },
  {
    id: 'demo-trace-04',
    title: 'Unmarked iron peg recessed in pavement',
    description: 'Worn circular iron marker set flush into paving flags with no municipal numbering.',
    category: 'Mystery',
    latitude: 51.5052,
    longitude: -0.0864,
    createdAt: '2026-10-07T11:05:00Z',
    observation: 'Produces a hollow ring when stepped on. Aligns geometrically with the old parish boundary line.',
    userNotes: 'No markings or surveyor stamps. Might be an old benchmark or boundary marker.',
    tags: ['relic', 'boundary', 'unsolved'],
    media: [],
  },
  {
    id: 'demo-trace-05',
    title: 'Old painted wall layers',
    description: 'Weathered exterior plaster revealing multiple historical strata of pigment.',
    category: 'Personal',
    latitude: 51.5029,
    longitude: -0.0898,
    createdAt: '2026-10-08T16:30:00Z',
    observation: 'Seven distinct color coats exposed: ochre, lead white, cobalt wash, and a faint corner of a stenciled botanical leaf.',
    userNotes: 'Felt like looking at forty years of seasons flaking away on one quiet street corner.',
    tags: ['palimpsest', 'pigment', 'time'],
    media: [],
  },
] as const;
