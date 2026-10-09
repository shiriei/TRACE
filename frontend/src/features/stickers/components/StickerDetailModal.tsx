import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { OwnedSticker, StickerTheme } from '../../../types/sticker';

export interface StickerDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  owned: OwnedSticker | null;
}

const THEME_LABELS: Record<StickerTheme, { label: string; icon: string }> = {
  botanical: { label: 'Botanical Specimen', icon: '🌿' },
  creatures: { label: 'Creature Encounter', icon: '🐌' },
  vintage: { label: 'Vintage Field Stamp', icon: '📜' },
  humor: { label: 'Field Humor', icon: '🍄' },
  cozy: { label: 'Cozy Hearth', icon: '☕' },
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

export const StickerDetailModal: React.FC<StickerDetailModalProps> = ({
  isOpen,
  onClose,
  owned,
}) => {
  const [imageError, setImageError] = useState(false);
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  const def = owned?.sticker;
  const palette = def
    ? THEME_PALETTES[def.theme] || THEME_PALETTES.botanical
    : THEME_PALETTES.botanical;

  // Reset image fallback when owned sticker changes
  useEffect(() => {
    setImageError(false);
  }, [owned?.id, def?.asset_path]);

  // Handle ESC key, focus management, body scroll lock, and suppress floating bee in popup
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    // Autofocus close button for accessible keyboard dismissal
    closeBtnRef.current?.focus();

    // Prevent background scrolling while modal is open
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    document.body.classList.add('has-sticker-modal-open');

    // Ensure the drifting bee element from workspace is suppressed while popup is open
    const beeEl = document.getElementById('bee');
    const prevBeeDisplay = beeEl?.style.display;
    if (beeEl) {
      beeEl.style.display = 'none';
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = originalOverflow;
      document.body.classList.remove('has-sticker-modal-open');
      if (beeEl && prevBeeDisplay !== undefined) {
        beeEl.style.display = prevBeeDisplay;
      }
    };
  }, [isOpen, onClose]);

  if (!isOpen || !owned || !def) {
    return null;
  }

  const handleImageError = () => {
    setImageError(true);
  };

  const hasAccessibleImage = Boolean(def.is_asset_available && !imageError);

  const formattedDate = new Date(owned.unlocked_at).toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const sourceLabel =
    owned.source === 'daily_reward'
      ? 'Daily Exploration Reward'
      : owned.source === 'milestone_reward'
      ? 'Milestone Pack Reward'
      : 'Special Achievement';

  const modalContent = (
    <div
      className="sticker-detail-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="sticker-detail-modal paper"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sticker-detail-title"
        onClick={(e) => e.stopPropagation()}
        style={{
          borderColor: palette.border,
        }}
      >
        {/* Modal Top Bar */}
        <div className="sticker-detail-top-bar">
          <div
            className="sticker-detail-theme-tag"
            style={{ color: palette.accent, backgroundColor: palette.bg, borderColor: palette.border }}
          >
            <span aria-hidden="true">{THEME_LABELS[def.theme]?.icon || '🌿'}</span>
            <span>{THEME_LABELS[def.theme]?.label || def.theme}</span>
          </div>

          <button
            ref={closeBtnRef}
            type="button"
            className="sticker-detail-close-btn"
            onClick={onClose}
            aria-label="Close sticker details"
          >
            ✕
          </button>
        </div>

        {/* Specimen Frame & Artwork */}
        <div
          className="sticker-detail-art-frame"
          style={{ backgroundColor: palette.bg, borderColor: palette.border }}
        >
          {hasAccessibleImage ? (
            <img
              src={`/${def.asset_path}`}
              alt={def.name}
              className="sticker-detail-img"
              onError={handleImageError}
            />
          ) : (
            <div className="sticker-detail-stamp-wrap">
              <div
                className="sticker-journal-stamp sticker-journal-stamp--large"
                style={{ borderColor: palette.accent }}
              >
                <span className="stamp-icon stamp-icon--large" aria-hidden="true">
                  {THEME_LABELS[def.theme]?.icon || '🌿'}
                </span>
                <span className="stamp-theme-label" style={{ color: palette.accent }}>
                  {THEME_LABELS[def.theme]?.label || def.theme}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Artwork Status Banner */}
        {!hasAccessibleImage && (
          <div className="sticker-artwork-status-card" role="status">
            <div className="artwork-status-badge">
              <span className="status-dot" aria-hidden="true" />
              <span>Artwork coming soon</span>
            </div>
            <p className="artwork-status-text">
              Observation certified in your journal. Official transparent PNG artwork illustration is currently in studio preparation.
            </p>
          </div>
        )}

        {/* Name & Quote */}
        <div className="sticker-detail-info">
          <div className="sticker-detail-title-row">
            <h3 id="sticker-detail-title" className="sticker-detail-name">
              {def.name}
            </h3>
            <span className={`sticker-rarity-pill sticker-rarity--${def.rarity}`}>
              {def.rarity}
            </span>
          </div>

          <blockquote className="sticker-detail-quote">
            “{def.description}”
          </blockquote>

          {/* Metadata Grid */}
          <div className="sticker-detail-meta-grid">
            <div className="meta-grid-item">
              <span className="meta-label">Earned On</span>
              <span className="meta-value">{formattedDate}</span>
            </div>

            <div className="meta-grid-item">
              <span className="meta-label">Award Source</span>
              <span className="meta-value">{sourceLabel}</span>
            </div>

            {owned.unlock_reason && (
              <div className="meta-grid-item meta-grid-item--full">
                <span className="meta-label">Journal Note</span>
                <span className="meta-value meta-value--reason">{owned.unlock_reason}</span>
              </div>
            )}
          </div>

          {/* Tags */}
          {def.tags && def.tags.length > 0 && (
            <div className="sticker-detail-tags-row" aria-label="Field tags">
              {def.tags.map((tag) => (
                <span key={tag} className="sticker-tag-chip">
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="sticker-detail-actions">
            {hasAccessibleImage ? (
              <a
                href={`/${def.asset_path}`}
                download={`${def.name.toLowerCase().replace(/\s+/g, '-')}.png`}
                className="btn-download-sticker"
                role="button"
              >
                📥 Download PNG
              </a>
            ) : (
              <button
                type="button"
                className="btn-download-sticker btn-download-sticker--disabled"
                disabled
                aria-disabled="true"
                title="Artwork coming soon — download action disabled"
              >
                📥 Download PNG (Artwork coming soon)
              </button>
            )}

            <button
              type="button"
              className="btn-secondary sticker-detail-dismiss-btn"
              onClick={onClose}
            >
              Return to Journal
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};
