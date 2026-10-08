import React from 'react';
import { TraceCategory } from '../../../types/trace';

/**
 * 🌿 Nature Thumbnail: Botanical Field Specimen
 * Leaves, moss, plant sprigs, and small wildflower.
 * "I noticed something alive or natural here."
 */
export const NatureThumb: React.FC = () => (
  <svg
    viewBox="0 0 80 80"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="field-thumb-svg"
    aria-label="Nature discovery illustration"
  >
    {/* Soft paper watercolor wash background */}
    <rect width="80" height="80" rx="8" fill="#eaf4ec" />
    <circle cx="40" cy="40" r="32" fill="#d4ebd8" opacity="0.6" />

    {/* Delicate moss clusters at base */}
    <path
      d="M16 68 Q24 58 32 68 Q40 56 48 68 Q56 59 64 68"
      stroke="#5aa469"
      strokeWidth="3.5"
      strokeLinecap="round"
      fill="none"
    />
    <path
      d="M20 64 Q26 56 32 64 Q38 54 44 64"
      stroke="#4f7f6a"
      strokeWidth="2.5"
      strokeLinecap="round"
      fill="none"
    />

    {/* Botanical stem */}
    <path
      d="M38 68 C38 52 36 34 46 16"
      stroke="#2c4a3f"
      strokeWidth="2.4"
      strokeLinecap="round"
    />

    {/* Primary serrated green leaves */}
    <path
      d="M40 48 C30 46 22 36 28 26 C36 30 38 42 40 48 Z"
      fill="#5aa469"
      stroke="#2c4a3f"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    <path d="M30 36 C34 38 38 44 40 48" stroke="#2c4a3f" strokeWidth="1.2" />

    <path
      d="M42 36 C52 34 60 24 54 14 C46 18 44 30 42 36 Z"
      fill="#6ea97a"
      stroke="#2c4a3f"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    <path d="M50 24 C46 26 44 32 42 36" stroke="#2c4a3f" strokeWidth="1.2" />

    {/* Small top sprout & golden flower bud */}
    <path
      d="M45 18 C48 10 54 8 56 12 C54 16 48 18 45 18 Z"
      fill="#98ce9f"
      stroke="#2c4a3f"
      strokeWidth="1.4"
    />
    <circle cx="48" cy="14" r="3.2" fill="#f3c63f" stroke="#2c4a3f" strokeWidth="1.4" />
  </svg>
);

/**
 * 🔊 Sound Thumbnail: Listening & Acoustic Cadence
 * Songbird perched singing with radiating acoustic curves and musical note.
 * "I heard something here."
 */
export const SoundThumb: React.FC = () => (
  <svg
    viewBox="0 0 80 80"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="field-thumb-svg"
    aria-label="Sound discovery illustration"
  >
    {/* Amber acoustic wash */}
    <rect width="80" height="80" rx="8" fill="#fcf3e3" />
    <circle cx="40" cy="40" r="32" fill="#fce4be" opacity="0.6" />

    {/* Hedgerow perch branch */}
    <path
      d="M12 56 C28 54 48 56 68 52"
      stroke="#2c4a3f"
      strokeWidth="2.5"
      strokeLinecap="round"
    />
    <path d="M24 55 Q20 48 14 50" stroke="#2c4a3f" strokeWidth="1.8" strokeLinecap="round" />
    <path d="M52 54 Q56 46 62 48" stroke="#5aa469" strokeWidth="2" strokeLinecap="round" />

    {/* Singing Songbird */}
    {/* Bird body */}
    <path
      d="M26 46 C22 36 28 26 38 24 C46 25 52 30 50 40 C46 48 34 50 26 46 Z"
      fill="#e8a33d"
      stroke="#2c4a3f"
      strokeWidth="2"
      strokeLinejoin="round"
    />
    {/* Bird wing */}
    <path
      d="M28 42 C34 36 42 38 40 46 C34 48 29 46 28 42 Z"
      fill="#b45309"
      stroke="#2c4a3f"
      strokeWidth="1.6"
    />
    {/* Eye & open singing beak */}
    <circle cx="44" cy="30" r="1.8" fill="#2c4a3f" />
    <path d="M48 28 L56 26 L50 33 Z" fill="#f3c63f" stroke="#2c4a3f" strokeWidth="1.5" />

    {/* Radiating sound waves from beak */}
    <path
      d="M58 20 C62 24 62 32 58 36"
      stroke="#e8a33d"
      strokeWidth="2.2"
      strokeLinecap="round"
    />
    <path
      d="M64 14 C70 20 70 38 64 44"
      stroke="#b45309"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeDasharray="2 3"
    />

    {/* Little musical note */}
    <path
      d="M56 12 L60 10 V18 M60 18 A2 2 0 1 1 56 18 A2 2 0 0 1 60 18"
      stroke="#2c4a3f"
      strokeWidth="1.4"
      fill="#2c4a3f"
      strokeLinecap="round"
    />
  </svg>
);

/**
 * 🧱 Structure Thumbnail: Observed Architectural Object
 * Weathered masonry stone wall, drainage pattern, curb lines.
 * "I noticed something built or arranged here."
 */
export const StructureThumb: React.FC = () => (
  <svg
    viewBox="0 0 80 80"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="field-thumb-svg"
    aria-label="Structure discovery illustration"
  >
    {/* Stone grey wash */}
    <rect width="80" height="80" rx="8" fill="#eef2f5" />
    <circle cx="40" cy="40" r="32" fill="#dce4eb" opacity="0.6" />

    {/* Masonry stone courses */}
    <rect x="14" y="18" width="24" height="14" rx="2" fill="#cbd5e1" stroke="#2c4a3f" strokeWidth="1.8" />
    <rect x="42" y="18" width="24" height="14" rx="2" fill="#b0bec5" stroke="#2c4a3f" strokeWidth="1.8" />

    <rect x="10" y="34" width="18" height="14" rx="2" fill="#b0bec5" stroke="#2c4a3f" strokeWidth="1.8" />
    <rect x="31" y="34" width="26" height="14" rx="2" fill="#cbd5e1" stroke="#2c4a3f" strokeWidth="1.8" />
    <rect x="60" y="34" width="10" height="14" rx="2" fill="#b0bec5" stroke="#2c4a3f" strokeWidth="1.8" />

    {/* Curb edge & hexagonal drainage culvert */}
    <path d="M8 50 L72 50" stroke="#6f8294" strokeWidth="3" strokeLinecap="round" />
    <rect x="22" y="52" width="36" height="16" rx="4" fill="#94a3b8" stroke="#2c4a3f" strokeWidth="2" />

    {/* Drain iron slits */}
    <line x1="28" y1="56" x2="28" y2="64" stroke="#2c4a3f" strokeWidth="2" strokeLinecap="round" />
    <line x1="34" y1="56" x2="34" y2="64" stroke="#2c4a3f" strokeWidth="2" strokeLinecap="round" />
    <line x1="40" y1="56" x2="40" y2="64" stroke="#2c4a3f" strokeWidth="2" strokeLinecap="round" />
    <line x1="46" y1="56" x2="46" y2="64" stroke="#2c4a3f" strokeWidth="2" strokeLinecap="round" />
    <line x1="52" y1="56" x2="52" y2="64" stroke="#2c4a3f" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

/**
 * 🔎 Mystery Thumbnail: Investigation & Curiosity
 * Magnifying glass inspecting an enigmatic marking / iron peg clue.
 * "Something here doesn't quite make sense."
 */
export const MysteryThumb: React.FC = () => (
  <svg
    viewBox="0 0 80 80"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="field-thumb-svg"
    aria-label="Mystery discovery illustration"
  >
    {/* Enigmatic purple wash */}
    <rect width="80" height="80" rx="8" fill="#f4effa" />
    <circle cx="40" cy="40" r="32" fill="#e5d8f5" opacity="0.6" />

    {/* Ground pavement flags & strange circular peg mark */}
    <line x1="12" y1="46" x2="68" y2="46" stroke="#c9b88c" strokeWidth="1.6" strokeDasharray="3 3" />
    <circle cx="34" cy="38" r="14" fill="#d8c5ee" stroke="#8a56c9" strokeWidth="2" strokeDasharray="3 2" />

    {/* Mystery question mark & star clue inside peg */}
    <text
      x="34"
      y="43"
      textAnchor="middle"
      fontSize="15"
      fontFamily="Patrick Hand, cursive"
      fill="#8a56c9"
      fontWeight="bold"
    >
      ?
    </text>

    {/* Magnifying Glass focused on the mark */}
    <circle cx="42" cy="34" r="18" fill="#ffffff" fillOpacity="0.45" stroke="#2c4a3f" strokeWidth="2.4" />
    <circle cx="42" cy="34" r="15" stroke="#8a56c9" strokeWidth="1.2" opacity="0.8" />
    {/* Glass lens reflection glint */}
    <path d="M34 24 Q42 20 50 26" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" />

    {/* Brass handle */}
    <path
      d="M55 47 L68 62"
      stroke="#2c4a3f"
      strokeWidth="4.5"
      strokeLinecap="round"
    />
    <path
      d="M56 48 L66 60"
      stroke="#e8a33d"
      strokeWidth="2.4"
      strokeLinecap="round"
    />

    {/* Tiny curiosity sparkles */}
    <path d="M22 18 L24 14 L26 18 L30 20 L26 22 L24 26 L22 22 L18 20 Z" fill="#8a56c9" opacity="0.8" />
    <circle cx="62" cy="18" r="1.5" fill="#8a56c9" />
  </svg>
);

/**
 * 💙 Personal Thumbnail: Personal Field Journal Keepsake
 * Pocket field journal notebook, pressed leaf, bookmark, and heart.
 * "This mattered to me."
 */
export const PersonalThumb: React.FC = () => (
  <svg
    viewBox="0 0 80 80"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="field-thumb-svg"
    aria-label="Personal discovery illustration"
  >
    {/* Soft sky blue & paper wash */}
    <rect width="80" height="80" rx="8" fill="#eaf3f8" />
    <circle cx="40" cy="40" r="32" fill="#d2e8f4" opacity="0.6" />

    {/* Pocket field journal notebook (rotated slightly) */}
    <g transform="rotate(-4 40 40)">
      {/* Back cover shadow */}
      <rect x="20" y="16" width="40" height="50" rx="4" fill="#c3dbe8" />
      {/* Front leather cover */}
      <rect x="18" y="14" width="40" height="50" rx="4" fill="#2f84b6" stroke="#2c4a3f" strokeWidth="2" />

      {/* Cream paper pages edge */}
      <rect x="22" y="18" width="32" height="42" rx="2" fill="#fbf4de" stroke="#2c4a3f" strokeWidth="1.2" />

      {/* Ruled lines inside journal */}
      <line x1="26" y1="26" x2="50" y2="26" stroke="#c9b88c" strokeWidth="1.2" />
      <line x1="26" y1="32" x2="48" y2="32" stroke="#c9b88c" strokeWidth="1.2" />
      <line x1="26" y1="38" x2="46" y2="38" stroke="#c9b88c" strokeWidth="1.2" />

      {/* Little warm heart sketch */}
      <path
        d="M38 46 C38 44 35 42 33 44 C31 46 33 49 38 53 C43 49 45 46 43 44 C41 42 38 44 38 46 Z"
        fill="#d6457f"
        stroke="#2c4a3f"
        strokeWidth="1.2"
      />

      {/* Bookmark ribbon dangling */}
      <path
        d="M36 14 V66 L40 62 L44 66 V14"
        fill="#d6457f"
        stroke="#2c4a3f"
        strokeWidth="1"
      />
    </g>

    {/* Tiny field pencil */}
    <g transform="rotate(35 56 46)">
      <rect x="52" y="30" width="6" height="28" rx="1" fill="#f3c63f" stroke="#2c4a3f" strokeWidth="1.2" />
      <polygon points="52 30 55 24 58 30" fill="#fbf4de" stroke="#2c4a3f" strokeWidth="1.2" />
      <polygon points="54 26 55 24 56 26" fill="#2c4a3f" />
    </g>
  </svg>
);

export const TRACE_ILLUSTRATIONS: Record<TraceCategory, React.ReactElement> = {
  Nature: <NatureThumb />,
  Sound: <SoundThumb />,
  Structure: <StructureThumb />,
  Mystery: <MysteryThumb />,
  Personal: <PersonalThumb />,
};

export const CATEGORY_MEANINGS: Record<TraceCategory, string> = {
  Nature: 'Alive or growing',
  Sound: 'Discovered by hearing',
  Structure: 'Built or arranged',
  Mystery: 'Worth investigating',
  Personal: 'Mattered to me',
};
