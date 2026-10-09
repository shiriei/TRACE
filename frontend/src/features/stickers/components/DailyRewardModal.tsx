import React, { useEffect, useRef } from 'react';
import { OwnedSticker, StickerPackDefinition } from '../../../types/sticker';

export interface DailyRewardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSeeCollection: () => void;
  awardedSticker: OwnedSticker;
  streak: number;
  longestStreak?: number;
  milestonesUnlocked?: StickerPackDefinition[];
}

const THEME_LABELS: Record<string, { label: string; icon: string }> = {
  botanical: { label: 'Botanical', icon: '🌿' },
  creatures: { label: 'Creatures', icon: '🐌' },
  vintage: { label: 'Vintage', icon: '📜' },
  humor: { label: 'Humor', icon: '🍄' },
  cozy: { label: 'Cozy', icon: '☕' },
  planner: { label: 'Field Tabs', icon: '🧭' },
};

const THEME_PALETTES: Record<string, { bg: string; border: string; accent: string }> = {
  botanical: { bg: '#eef6f0', border: '#a8d5b5', accent: '#3b7a57' },
  creatures: { bg: '#fdf6ee', border: '#f3cba5', accent: '#b06526' },
  vintage: { bg: '#f8f4ec', border: '#d7c7aa', accent: '#725a3a' },
  humor: { bg: '#fbf0f4', border: '#f0bcd0', accent: '#a63a66' },
  cozy: { bg: '#f6f3ed', border: '#d5c7b3', accent: '#695742' },
  planner: { bg: '#eef4f8', border: '#a8cde3', accent: '#2b6589' },
};

export const DailyRewardModal: React.FC<DailyRewardModalProps> = ({
  isOpen,
  onClose,
  onSeeCollection,
  awardedSticker,
  streak,
  longestStreak = 0,
  milestonesUnlocked = [],
}) => {
  const primaryBtnRef = useRef<HTMLButtonElement>(null);

  // Keyboard navigation: Escape key closes modal, autofocus primary button
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    primaryBtnRef.current?.focus();

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !awardedSticker) return null;

  const sticker = awardedSticker.sticker;
  const theme = sticker.theme || 'botanical';
  const palette = THEME_PALETTES[theme] || THEME_PALETTES.botanical;
  const themeMeta = THEME_LABELS[theme] || { label: theme, icon: '🌿' };

  // Context-aware celebratory heading
  const getCelebrationTitle = () => {
    if (streak > 1) {
      return 'Your streak is growing!';
    }
    if (longestStreak > 1) {
      return 'Your exploration journey continues!';
    }
    return 'Exploration streak started!';
  };

  const getSubheading = () => {
    if (streak > 1) {
      return `Day ${streak} completed! You’re noticing the real world one discovery at a time.`;
    }
    if (longestStreak > 1) {
      return `Welcome back to the trail! Your previous stickers are safe in your field journal.`;
    }
    return `You left your first trace today! Every sustained habit begins with a single observation.`;
  };

  return (
    <div
      className="reward-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="celebration-title"
      onClick={onClose}
    >
      <div
        className="reward-modal paper"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        {/* Dismiss Button */}
        <button
          type="button"
          className="reward-modal-close-btn"
          onClick={onClose}
          aria-label="Dismiss and keep exploring"
        >
          &times;
        </button>

        {/* Celebratory Header */}
        <div className="reward-modal-header">
          <div className="reward-streak-badge-wrap">
            <div className="reward-streak-pill" title={`${streak}-day exploration streak`}>
              <svg
                className="streak-flame-icon streak-flame-icon--active"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M12 2C9.5 6.5 12 9.5 10 12.5C8.8 10.8 8.5 9 8.5 9C5 12.8 5 17 8 19.8C10.5 22.1 14.5 22.1 17 19.8C19.8 17.2 20 12.8 15.5 8C15.5 8 15.5 10.5 14 11C13.5 8 14 5 12 2Z"
                  fill="url(#rewardFlameGrad)"
                />
                <defs>
                  <linearGradient
                    id="rewardFlameGrad"
                    x1="12"
                    y1="2"
                    x2="12"
                    y2="22"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop stopColor="#ff8533" />
                    <stop offset="1" stopColor="#e8590c" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="reward-streak-number">{streak}</span>
              <span className="reward-streak-label">{streak === 1 ? 'Day Streak' : 'Days Streak'}</span>
            </div>
          </div>

          <h2 id="celebration-title" className="reward-modal-title">
            {getCelebrationTitle()}
          </h2>
          <p className="reward-modal-subheading">{getSubheading()}</p>
        </div>

        {/* Sticker Reveal Card */}
        <div
          className="reward-sticker-card"
          style={{
            backgroundColor: palette.bg,
            borderColor: palette.border,
          }}
        >
          <div className="reward-sticker-art-wrap">
            {sticker.is_asset_available ? (
              <img
                src={`/${sticker.asset_path}`}
                alt={sticker.name}
                className="reward-sticker-img"
              />
            ) : (
              <div
                className="reward-stamp-placeholder"
                style={{ borderColor: palette.accent }}
              >
                <span className="reward-stamp-emoji" aria-hidden="true">
                  {themeMeta.icon}
                </span>
                <span className="reward-stamp-theme" style={{ color: palette.accent }}>
                  {themeMeta.label}
                </span>
              </div>
            )}
          </div>

          <div className="reward-sticker-details">
            <div className="reward-sticker-rarity-row">
              <span className={`reward-rarity-pill reward-rarity--${sticker.rarity}`}>
                {sticker.rarity}
              </span>
              <span className="reward-source-tag">Daily Reward</span>
            </div>

            <h3 className="reward-sticker-name">{sticker.name}</h3>
            <p className="reward-sticker-caption">“{sticker.description}”</p>

            <div className="reward-confirmed-message" role="status">
              <span className="confirmed-check" aria-hidden="true">✓</span> Added to your Sticker Journal
            </div>
          </div>
        </div>

        {/* Milestone Unlocks (if achieved on this trace) */}
        {milestonesUnlocked.length > 0 && (
          <div className="reward-milestone-unlocked-banner">
            <div className="milestone-unlocked-title">
              <span aria-hidden="true">🏆</span> Milestone Pack Unlocked!
            </div>
            {milestonesUnlocked.map((pack) => (
              <div key={pack.id} className="milestone-unlocked-item">
                <strong>{pack.name}</strong> — {pack.description}
              </div>
            ))}
          </div>
        )}

        {/* Modal Actions */}
        <div className="reward-modal-actions">
          <button
            type="button"
            ref={primaryBtnRef}
            className="cta reward-modal-primary-btn"
            onClick={onSeeCollection}
          >
            See my collection
          </button>
          <button
            type="button"
            className="btn-secondary reward-modal-secondary-btn"
            onClick={onClose}
          >
            Keep exploring
          </button>
        </div>
      </div>
    </div>
  );
};
