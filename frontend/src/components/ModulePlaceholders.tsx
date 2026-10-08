import React from 'react';

const MODULES = [
  {
    phase: 'Phase 3 (Planned)',
    name: 'Personal Trace Map',
    desc: 'Local cartographic view rendering discovered traces and evolving physical territory.',
  },
  {
    phase: 'Phase 1 (Planned)',
    name: 'Trace Capture',
    desc: 'Intake interface for sensory observations, field notes, and optional coordinates.',
  },
  {
    phase: 'Phase 4 (Planned)',
    name: 'Exploration Missions',
    desc: 'Contextual, enigmatic clues generated from previous traces to inspire your next walk.',
  },
  {
    phase: 'Phase 4 (Planned)',
    name: 'Pattern Insights',
    desc: 'Local intelligence evaluating relationships and thematic clusters between observations.',
  },
  {
    phase: 'Phase 1 (Planned)',
    name: 'Discovery History',
    desc: 'Chronological archive of all field observations and recorded physical artifacts.',
  },
];

export const ModulePlaceholders: React.FC = () => {
  return (
    <section className="modules-section">
      <div className="section-header">
        <h3 className="section-title">Product Roadmap Modules</h3>
        <p className="section-subtitle">
          Visual scaffold for upcoming functional capabilities. No mock data or fake AI is generated.
        </p>
      </div>

      <div className="module-grid">
        {MODULES.map((mod) => (
          <div key={mod.name} className="module-card">
            <div className="module-phase">{mod.phase}</div>
            <h4 className="module-name">{mod.name}</h4>
            <p className="module-desc">{mod.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
};
