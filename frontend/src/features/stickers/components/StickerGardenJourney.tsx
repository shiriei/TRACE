import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  OwnedSticker,
  StickerDefinition,
  StickerPackDefinition,
  StickerTheme,
  StreakSummaryResponse,
} from '../../../types/sticker';
import { stickerService } from '../../../services/stickerService';

interface StickerGardenJourneyProps {
  onBackToMap?: () => void;
}

const THEME_LABELS: Record<StickerTheme, { label: string; icon: string }> = {
  botanical: { label: 'Botanical', icon: '🌿' },
  creatures: { label: 'Creatures', icon: '🐌' },
  vintage: { label: 'Vintage', icon: '📜' },
  humor: { label: 'Humor', icon: '🍄' },
  cozy: { label: 'Cozy', icon: '☕' },
  planner: { label: 'Field Tabs', icon: '🧭' },
};

const THEME_PALETTES: Record<StickerTheme, { bg: string; border: string; accent: string }> = {
  botanical: { bg: '#eef6f0', border: '#a8d5b5', accent: '#3b7a57' },
  creatures: { bg: '#fdf6ee', border: '#f3cba5', accent: '#b06526' },
  vintage: { bg: '#f8f4ec', border: '#d7c7aa', accent: '#725a3a' },
  humor: { bg: '#fbf0f4', border: '#f0bcd0', accent: '#a63a66' },
  cozy: { bg: '#f6f3ed', border: '#d5c7b3', accent: '#695742' },
  planner: { bg: '#eef4f8', border: '#a8cde3', accent: '#2b6589' },
};

export const StickerGardenJourney: React.FC<StickerGardenJourneyProps> = ({ onBackToMap }) => {
  const [streakSummary, setStreakSummary] = useState<StreakSummaryResponse | null>(null);
  const [collection, setCollection] = useState<OwnedSticker[]>([]);
  const [catalogue, setCatalogue] = useState<StickerDefinition[]>([]);
  const [packs, setPacks] = useState<StickerPackDefinition[]>([]);
  const [activeThemeFilter, setActiveThemeFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summary, userColl, allPacks, allStickers] = await Promise.all([
        stickerService.getStreakSummary(),
        stickerService.getUserCollection(),
        stickerService.getPacks(),
        stickerService.getCatalogue(),
      ]);
      setStreakSummary(summary);
      setCollection(userColl);
      setPacks(allPacks);
      setCatalogue(allStickers);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load Sticker Garden';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    // Refresh if a new trace is recorded in another tab or view
    const handleTraceSaved = () => {
      loadData();
    };
    window.addEventListener('trace:saved', handleTraceSaved);
    return () => {
      window.removeEventListener('trace:saved', handleTraceSaved);
    };
  }, [loadData]);

  const ownedStickerMap = useMemo(() => {
    const map = new Map<string, OwnedSticker>();
    collection.forEach((item) => map.set(item.sticker_id, item));
    return map;
  }, [collection]);

  const filteredCollection = useMemo(() => {
    if (activeThemeFilter === 'all') return collection;
    return collection.filter((item) => item.sticker.theme === activeThemeFilter);
  }, [collection, activeThemeFilter]);

  if (isLoading && !streakSummary) {
    return (
      <div className="sticker-garden-container paper">
        <div className="sticker-garden-loading" role="status">
          <div className="sticker-garden-spinner" aria-hidden="true" />
          <p>Gathering your field stickers and exploration journey...</p>
        </div>
      </div>
    );
  }

  if (error && !streakSummary) {
    return (
      <div className="sticker-garden-container paper">
        <div className="sticker-garden-error" role="alert">
          <h3>Could not load Sticker Garden</h3>
          <p>{error}</p>
          <button type="button" className="btn-secondary" onClick={loadData}>
            Try again
          </button>
        </div>
      </div>
    );
  }

  const currentStreak = streakSummary?.current_streak ?? 0;
  const longestStreak = streakSummary?.longest_streak ?? 0;
  const totalDays = streakSummary?.total_qualifying_days ?? 0;
  const stickersOwnedCount = streakSummary?.total_stickers_owned ?? collection.length;
  const todayQualified = streakSummary?.today_qualified ?? false;

  return (
    <div className="sticker-garden-container paper" id="stickers-journey">
      {/* Garden Header */}
      <header className="sticker-garden-header">
        <div className="sticker-garden-header-text">
          <div className="sticker-garden-title-row">
            <span className="sticker-garden-badge-pill" aria-hidden="true">🌱 Field Journal Rewards</span>
            {onBackToMap && (
              <button
                type="button"
                className="sticker-garden-back-btn"
                onClick={onBackToMap}
                title="Return to Living Map"
              >
                ← Back to Living Map
              </button>
            )}
          </div>
          <h2 className="sticker-garden-title">Sticker Garden</h2>
          <p className="sticker-garden-subtitle">
            Notice the world, leave your trace, and grow your field journal collection.
          </p>
        </div>
      </header>

      {/* Exploration Streak & Summary Metrics */}
      <section className="sticker-garden-metrics-row" aria-label="Journey overview">
        <div className="sticker-metric-card sticker-metric-card--streak">
          <div className="sticker-metric-icon-wrap" aria-hidden="true">
            <svg
              className={`streak-flame-icon ${currentStreak > 0 ? 'streak-flame-icon--active' : 'streak-flame-icon--dormant'}`}
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2C9.5 6.5 12 9.5 10 12.5C8.8 10.8 8.5 9 8.5 9C5 12.8 5 17 8 19.8C10.5 22.1 14.5 22.1 17 19.8C19.8 17.2 20 12.8 15.5 8C15.5 8 15.5 10.5 14 11C13.5 8 14 5 12 2Z"
                fill="url(#gardenStreakFlame)"
              />
              <defs>
                <linearGradient id="gardenStreakFlame" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#ff8533" />
                  <stop offset="1" stopColor="#e8590c" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="sticker-metric-body">
            <span className="sticker-metric-label">Current Streak</span>
            <div className="sticker-metric-val">
              {currentStreak} <span className="sticker-metric-unit">{currentStreak === 1 ? 'day' : 'days'}</span>
            </div>
            <p className="sticker-metric-footnote">
              {todayQualified ? '✓ Qualified today' : 'Pending today’s trace'} • Longest: {longestStreak} {longestStreak === 1 ? 'day' : 'days'}
            </p>
          </div>
        </div>

        <div className="sticker-metric-card">
          <div className="sticker-metric-icon-wrap" aria-hidden="true">
            <span className="sticker-metric-emoji">🗺️</span>
          </div>
          <div className="sticker-metric-body">
            <span className="sticker-metric-label">Exploration Days</span>
            <div className="sticker-metric-val">
              {totalDays} <span className="sticker-metric-unit">{totalDays === 1 ? 'day' : 'days'}</span>
            </div>
            <p className="sticker-metric-footnote">Calendar days with recorded traces</p>
          </div>
        </div>

        <div className="sticker-metric-card">
          <div className="sticker-metric-icon-wrap" aria-hidden="true">
            <span className="sticker-metric-emoji">🌸</span>
          </div>
          <div className="sticker-metric-body">
            <span className="sticker-metric-label">Stickers Earned</span>
            <div className="sticker-metric-val">
              {stickersOwnedCount} <span className="sticker-metric-unit">of {catalogue.length}</span>
            </div>
            <p className="sticker-metric-footnote">Permanent additions in field collection</p>
          </div>
        </div>
      </section>

      {/* Today's Reward Status Card */}
      <section className="sticker-today-callout" aria-label="Today's exploration status">
        <div className="sticker-today-content">
          <div className="sticker-today-badge">
            {todayQualified ? (
              <span className="today-badge today-badge--qualified">✓ Today's Trace Recorded</span>
            ) : (
              <span className="today-badge today-badge--pending">⏳ Today's Trace Pending</span>
            )}
          </div>
          <h3 className="sticker-today-title">
            {todayQualified ? "Today's Exploration Completed!" : 'Keep Your Habit Blooming'}
          </h3>
          <p className="sticker-today-desc">
            {streakSummary?.today_reward_reason ||
              (todayQualified
                ? 'Your observation today counts toward your streak and unlocked today’s sticker reward!'
                : 'Save any trace today to extend your streak and receive your next daily sticker.')}
          </p>
        </div>
        {streakSummary?.next_milestone_days && streakSummary.days_to_next_milestone !== null && (
          <div className="sticker-next-goal-box">
            <span className="next-goal-label">Next Milestone Target</span>
            <span className="next-goal-threshold">{streakSummary.next_milestone_days} Days</span>
            <span className="next-goal-remaining">
              {streakSummary.days_to_next_milestone === 0
                ? 'Unlocked!'
                : `${streakSummary.days_to_next_milestone} ${streakSummary.days_to_next_milestone === 1 ? 'day' : 'days'} remaining`}
            </span>
          </div>
        )}
      </section>

      {/* Prominent My Collection / Sticker Journal Section */}
      <section className="sticker-collection-section" id="my-collection" aria-label="Earned sticker collection">
        <div className="collection-header-row">
          <div>
            <h3 className="section-title">My Collection ({collection.length})</h3>
            <p className="section-subtitle">Earned stickers permanently preserved in your personal field journal.</p>
          </div>

          {/* Theme Filters */}
          <div className="sticker-theme-filters" role="group" aria-label="Filter collection by theme">
            <button
              type="button"
              className={`theme-filter-chip ${activeThemeFilter === 'all' ? 'active' : ''}`}
              onClick={() => setActiveThemeFilter('all')}
            >
              All ({collection.length})
            </button>
            {(Object.keys(THEME_LABELS) as StickerTheme[]).map((thm) => {
              const count = collection.filter((c) => c.sticker.theme === thm).length;
              return (
                <button
                  key={thm}
                  type="button"
                  className={`theme-filter-chip ${activeThemeFilter === thm ? 'active' : ''}`}
                  onClick={() => setActiveThemeFilter(thm)}
                >
                  {THEME_LABELS[thm].icon} {THEME_LABELS[thm].label} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {collection.length === 0 ? (
          <div className="sticker-collection-empty">
            <div className="empty-album-icon" aria-hidden="true">📖</div>
            <h4>Your Sticker Journal is Waiting</h4>
            <p>
              You haven’t collected any stickers yet! Step outside, record your first daily observation on the map,
              and your first sticker reward will arrive right here in your journal.
            </p>
            {onBackToMap && (
              <button
                type="button"
                className="cta empty-start-exploring-btn"
                onClick={onBackToMap}
                style={{ marginTop: '16px' }}
              >
                Start Exploring
              </button>
            )}
          </div>
        ) : filteredCollection.length === 0 ? (
          <div className="sticker-collection-empty">
            <p>No stickers earned in this category yet. Keep exploring to expand your collection!</p>
          </div>
        ) : (
          <div className="sticker-grid">
            {filteredCollection.map((owned) => {
              const def = owned.sticker;
              const palette = THEME_PALETTES[def.theme] || THEME_PALETTES.botanical;

              return (
                <div
                  key={owned.id}
                  className="sticker-card"
                  style={{
                    backgroundColor: palette.bg,
                    borderColor: palette.border,
                  }}
                >
                  {/* Sticker Artwork / Intentional Journal Stamp Placeholder */}
                  <div className="sticker-card-art-frame">
                    {def.is_asset_available ? (
                      <img
                        src={`/${def.asset_path}`}
                        alt={def.name}
                        className="sticker-card-img"
                        loading="lazy"
                      />
                    ) : (
                      <div className="sticker-journal-stamp" style={{ borderColor: palette.accent }}>
                        <span className="stamp-icon" aria-hidden="true">
                          {THEME_LABELS[def.theme]?.icon || '🌿'}
                        </span>
                        <span className="stamp-theme-label" style={{ color: palette.accent }}>
                          {THEME_LABELS[def.theme]?.label || def.theme}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Sticker Metadata */}
                  <div className="sticker-card-content">
                    <div className="sticker-rarity-row">
                      <span className={`sticker-rarity-pill sticker-rarity--${def.rarity}`}>
                        {def.rarity}
                      </span>
                      <span className="sticker-source-pill">
                        {owned.source === 'daily_reward'
                          ? 'Daily Reward'
                          : owned.source === 'milestone_reward'
                          ? 'Milestone'
                          : 'Awarded'}
                      </span>
                    </div>

                    <h4 className="sticker-card-name">{def.name}</h4>
                    <p className="sticker-card-caption">“{def.description}”</p>

                    <div className="sticker-card-earned-date">
                      Earned {new Date(owned.unlocked_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Milestone Progression Track */}
      <section className="sticker-milestones-section" aria-label="Milestone journey">
        <div className="section-title-wrap">
          <h3 className="section-title">Milestone Journey</h3>
          <p className="section-subtitle">
            Walk with an open eye. Unlock commemorative curated packs at 7, 30, 50, and 100 consecutive days.
          </p>
        </div>

        <div className="milestones-track">
          {streakSummary?.milestones.map((ms) => {
            const packDef = packs.find((p) => p.id === ms.pack_id);
            const statusClass = ms.is_achieved
              ? 'milestone-card--achieved'
              : ms.is_current
              ? 'milestone-card--current'
              : 'milestone-card--locked';

            const progressPct = Math.min(
              100,
              Math.max(0, Math.round((currentStreak / ms.streak_threshold) * 100))
            );

            return (
              <div key={ms.id} className={`milestone-card ${statusClass}`}>
                <div className="milestone-step-header">
                  <span className="milestone-threshold-pill">{ms.streak_threshold} Days</span>
                  <span className="milestone-status-chip">
                    {ms.is_achieved ? '✓ Achieved' : ms.is_current ? '✦ In Progress' : '🔒 Locked'}
                  </span>
                </div>

                <h4 className="milestone-name">{ms.name}</h4>
                <p className="milestone-desc">{packDef?.description || 'Commemorative reward pack'}</p>

                <div className="milestone-progress-bar-wrap" aria-hidden="true">
                  <div className="milestone-progress-bar-fill" style={{ width: `${progressPct}%` }} />
                </div>

                <div className="milestone-footer">
                  <span className="milestone-days-left">
                    {ms.is_achieved
                      ? 'Pack Unlocked'
                      : ms.days_remaining === 0
                      ? 'Ready to claim'
                      : `${ms.days_remaining} ${ms.days_remaining === 1 ? 'day' : 'days'} to unlock`}
                  </span>
                  <span className="milestone-stickers-count">
                    {packDef?.sticker_ids.length || 3} Stickers
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Reward Packs Section */}
      <section className="sticker-packs-section" aria-label="Milestone reward packs">
        <div className="section-title-wrap">
          <h3 className="section-title">Commemorative Sticker Packs</h3>
          <p className="section-subtitle">
            Curated collections unlocked through sustained exploration habits.
          </p>
        </div>

        <div className="packs-grid">
          {packs.map((pack) => {
            const threshold = pack.milestone_requirement.threshold || 7;
            const milestoneStatus = streakSummary?.milestones.find((m) => m.pack_id === pack.id);
            const isUnlocked = milestoneStatus?.is_achieved ?? (currentStreak >= threshold);

            // How many stickers in pack are owned
            const ownedInPack = pack.sticker_ids.filter((id) => ownedStickerMap.has(id)).length;

            return (
              <div
                key={pack.id}
                className={`pack-card ${isUnlocked ? 'pack-card--unlocked' : 'pack-card--locked'}`}
              >
                <div className="pack-card-header">
                  <span className="pack-threshold-badge">{threshold}-Day Milestone</span>
                  <span className={`pack-status-badge ${isUnlocked ? 'unlocked' : 'locked'}`}>
                    {isUnlocked ? '✓ Unlocked' : '🔒 Locked'}
                  </span>
                </div>

                <h4 className="pack-name">{pack.name}</h4>
                <p className="pack-description">{pack.description}</p>

                <div className="pack-contents-summary">
                  <span className="pack-contents-label">Includes {pack.sticker_ids.length} stickers:</span>
                  <div className="pack-stickers-pill-row">
                    {pack.sticker_ids.map((sId) => {
                      const def = catalogue.find((s) => s.id === sId);
                      const isOwned = ownedStickerMap.has(sId);
                      return (
                        <span
                          key={sId}
                          className={`pack-sticker-tag ${isOwned ? 'owned' : 'unowned'}`}
                          title={isOwned ? `Earned: ${def?.name || sId}` : `Included in pack: ${def?.name || sId}`}
                        >
                          {isOwned ? '✓ ' : '• '}
                          {def?.name || sId}
                        </span>
                      );
                    })}
                  </div>
                </div>

                <div className="pack-card-footer">
                  <span className="pack-completion-status">
                    {ownedInPack}/{pack.sticker_ids.length} Collected
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};
