import React, { useState, useRef, useEffect } from 'react';
import { TraceAIResult, TraceCategory, TRACE_CATEGORIES } from '../../../types';
import { interpretTraceObservation, TraceAIError } from '../../../services/api';

const DEFAULT_SAMPLE = 'I noticed moss growing between bricks near a drain.';

interface TraceAIInterpreterProps {
  initialCategory?: TraceCategory | null;
  onTraceReady?: (data: {
    observation: string;
    result?: TraceAIResult | null;
    photoFile?: File | null;
    audioFile?: File | null;
    selectedCategory?: TraceCategory | null;
  }) => void;
}

export const TraceAIInterpreter: React.FC<TraceAIInterpreterProps> = ({
  initialCategory,
  onTraceReady,
}) => {
  const [observation, setObservation] = useState(DEFAULT_SAMPLE);
  const [selectedCategory, setSelectedCategory] = useState<TraceCategory | null>(
    initialCategory || null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<TraceAIResult | null>(null);
  const [errorInfo, setErrorInfo] = useState<{ title: string; message: string } | null>(null);

  // Attachment states
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioPreviewUrl, setAudioPreviewUrl] = useState<string | null>(null);

  const isInterpretingRef = useRef(false);
  const isPlacingRef = useRef(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const photoInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
      if (audioPreviewUrl) URL.revokeObjectURL(audioPreviewUrl);
    };
  }, [photoPreviewUrl, audioPreviewUrl]);

  // Sync initialCategory when changed externally
  useEffect(() => {
    if (initialCategory !== undefined) {
      setSelectedCategory(initialCategory);
    }
  }, [initialCategory]);

  const handleChoosePhoto = () => {
    photoInputRef.current?.click();
  };

  const handleChooseAudio = () => {
    audioInputRef.current?.click();
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
      setPhotoFile(file);
      setPhotoPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (audioPreviewUrl) URL.revokeObjectURL(audioPreviewUrl);
      setAudioFile(file);
      setAudioPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleRemovePhoto = () => {
    if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
    setPhotoFile(null);
    setPhotoPreviewUrl(null);
    if (photoInputRef.current) photoInputRef.current.value = '';
  };

  const handleRemoveAudio = () => {
    if (audioPreviewUrl) URL.revokeObjectURL(audioPreviewUrl);
    setAudioFile(null);
    setAudioPreviewUrl(null);
    if (audioInputRef.current) audioInputRef.current.value = '';
  };

  const handleInterpret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isInterpretingRef.current || isLoading || isSubmitting || !observation.trim()) return;

    isInterpretingRef.current = true;
    setIsLoading(true);
    setIsSubmitting(true);
    setErrorInfo(null);
    setResult(null);

    try {
      const aiResult = await interpretTraceObservation(observation.trim());
      setResult(aiResult);
    } catch (err: unknown) {
      if (err instanceof TraceAIError) {
        setErrorInfo({
          title: err.userTitle,
          message: err.userMessage,
        });
      } else {
        setErrorInfo({
          title: "TRACE couldn't interpret this observation.",
          message: 'Try describing what you noticed in a little more detail.',
        });
      }
    } finally {
      isInterpretingRef.current = false;
      setIsLoading(false);
      setIsSubmitting(false);
    }
  };

  const handlePlaceOnMap = () => {
    if (isPlacingRef.current || !onTraceReady) return;
    isPlacingRef.current = true;
    const effectiveCategory = selectedCategory || (result ? result.category : 'Personal');
    onTraceReady({
      observation,
      result: result ? { ...result, category: effectiveCategory } : null,
      photoFile,
      audioFile,
      selectedCategory,
    });
    setTimeout(() => {
      isPlacingRef.current = false;
    }, 600);
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Nature':
        return 'var(--nature)';
      case 'Sound':
        return 'var(--sound)';
      case 'Structure':
        return 'var(--structure)';
      case 'Mystery':
        return 'var(--mystery)';
      case 'Personal':
        return 'var(--personal)';
      default:
        return 'var(--moss)';
    }
  };

  const getCategoryEmoji = (category: string) => {
    switch (category) {
      case 'Nature':
        return '🌿';
      case 'Sound':
        return '🔊';
      case 'Structure':
        return '🏛';
      case 'Mystery':
        return '🔎';
      case 'Personal':
        return '💙';
      default:
        return '🌱';
    }
  };

  return (
    <div className="ai-interpreter-card paper" id="ai-interpreter">
      <form onSubmit={handleInterpret} className="ai-interpreter-form">
        {/* Category Lens Selection */}
        <div className="ai-category-select-group">
          <div className="ai-category-select-header">
            <span className="ai-category-select-label">Category lens</span>
            {selectedCategory ? (
              <button
                type="button"
                className="ai-category-clear-btn"
                onClick={() => setSelectedCategory(null)}
                title="Clear selected category to let AI classify automatically"
              >
                Reset to Auto-detect
              </button>
            ) : (
              <span className="ai-category-hint">Auto-detecting via local AI</span>
            )}
          </div>
          <div className="ai-category-chips" role="radiogroup" aria-label="Select trace category lens">
            {TRACE_CATEGORIES.map((cat) => {
              const isSelected = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  className={`ai-category-chip ${isSelected ? 'ai-category-chip--selected' : ''}`}
                  style={{
                    borderColor: isSelected ? getCategoryColor(cat) : undefined,
                    color: isSelected ? getCategoryColor(cat) : undefined,
                  }}
                  onClick={() => setSelectedCategory(isSelected ? null : cat)}
                  title={isSelected ? `Selected: ${cat} (click to deselect)` : `Select ${cat}`}
                >
                  <span className="ai-category-chip-icon">{getCategoryEmoji(cat)}</span>
                  <span className="ai-category-chip-name">{cat}</span>
                </button>
              );
            })}
          </div>
        </div>

        <label htmlFor="observation-input" className="ai-input-label">
          What did you notice?
        </label>
        <textarea
          id="observation-input"
          className="ai-textarea"
          rows={3}
          value={observation}
          onChange={(e) => setObservation(e.target.value)}
          placeholder="I noticed moss growing between bricks near a drain."
          disabled={isLoading}
        />

        {/* Hidden File Inputs */}
        <input
          type="file"
          ref={photoInputRef}
          accept="image/jpeg,image/png,image/webp,image/gif"
          style={{ display: 'none' }}
          onChange={handlePhotoChange}
          aria-label="Choose a photo"
        />
        <input
          type="file"
          ref={audioInputRef}
          accept="audio/mpeg,audio/wav,audio/ogg,audio/webm,audio/x-m4a,audio/aac,audio/flac"
          style={{ display: 'none' }}
          onChange={handleAudioChange}
          aria-label="Choose an audio file"
        />

        {/* Selected Photo Preview */}
        {photoFile && photoPreviewUrl && (
          <div className="attachment-preview-card attachment-preview-photo">
            <div className="attachment-preview-header">
              <span className="attachment-type-badge">📷 Photo attachment</span>
              <button
                type="button"
                className="btn-remove-attachment"
                onClick={handleRemovePhoto}
              >
                Remove attachment
              </button>
            </div>
            <div className="attachment-photo-body">
              <img
                src={photoPreviewUrl}
                alt={photoFile.name}
                className="attachment-photo-thumb"
              />
              <div className="attachment-file-details">
                <strong className="attachment-filename">{photoFile.name}</strong>
                <small className="attachment-filesize">
                  {(photoFile.size / 1024).toFixed(1)} KB
                </small>
                <button
                  type="button"
                  className="btn-change-attachment"
                  onClick={handleChoosePhoto}
                >
                  Choose a photo
                </button>
              </div>
            </div>
          </div>
        )}

        {audioFile && audioPreviewUrl && (
          <div className="attachment-preview-card attachment-preview-audio">
            <div className="attachment-preview-header">
              <span className="attachment-type-badge">🎙️ Audio attachment</span>
              <button
                type="button"
                className="btn-remove-attachment"
                onClick={handleRemoveAudio}
              >
                Remove attachment
              </button>
            </div>
            <div className="attachment-audio-body">
              <div className="attachment-audio-info">
                <span className="attachment-audio-icon">🔊</span>
                <div className="attachment-file-details">
                  <strong className="attachment-filename">{audioFile.name}</strong>
                  <small className="attachment-filesize">
                    {(audioFile.size / 1024).toFixed(1)} KB
                  </small>
                </div>
              </div>
              <audio
                controls
                src={audioPreviewUrl}
                className="attachment-audio-player"
              />
              <button
                type="button"
                className="btn-change-attachment"
                onClick={handleChooseAudio}
                style={{ alignSelf: 'flex-start', marginTop: '6px' }}
              >
                Choose an audio file
              </button>
            </div>
          </div>
        )}

        <div className="ai-form-actions">
          <div className="trace-media-actions-bar">
            {!photoFile && (
              <button
                type="button"
                className="btn-media-action"
                onClick={handleChoosePhoto}
                title="Choose a photo to attach to this observation"
              >
                <span className="media-action-icon">📷</span>
                <span>Add a photo</span>
              </button>
            )}

            {!audioFile && (
              <button
                type="button"
                className="btn-media-action"
                onClick={handleChooseAudio}
                title="Choose an audio file to attach to this observation"
              >
                <span className="media-action-icon">🎙️</span>
                <span>Add audio</span>
              </button>
            )}
          </div>

          <button
            type="submit"
            className="cta ai-submit-btn"
            disabled={isLoading || isSubmitting || !observation.trim()}
          >
            {isLoading || isSubmitting ? 'Interpreting...' : 'Leave a trace'}
          </button>
        </div>
      </form>

      {/* Loading feedback */}
      {isLoading && (
        <div className="ai-loading-box">
          <span className="ai-loading-spinner" />
          <span>Interpreting observation...</span>
        </div>
      )}

      {/* Error State */}
      {errorInfo && !isLoading && (
        <div className="ai-error-box" role="alert">
          <div className="ai-error-content">
            <h4 className="ai-error-title">{errorInfo.title}</h4>
            <p className="ai-error-message">{errorInfo.message}</p>
            {onTraceReady && (
              <div style={{ marginTop: '0.75rem' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() =>
                    onTraceReady({
                      observation,
                      result: null,
                      photoFile,
                      audioFile,
                      selectedCategory,
                    })
                  }
                  style={{ fontSize: '1rem', padding: '6px 14px' }}
                >
                  Place trace without AI &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Successful Result Display */}
      {result && !isLoading && (() => {
        const displayCategory = selectedCategory || result.category;
        const isUserSelected = !!selectedCategory;
        return (
          <div className="ai-result-card" style={{ borderColor: getCategoryColor(displayCategory) }}>
            <div className="ai-result-category" style={{ color: getCategoryColor(displayCategory) }}>
              <span className="ai-result-cat-icon">{getCategoryEmoji(displayCategory)}</span>
              <span className="ai-result-cat-name">{displayCategory}</span>
              {isUserSelected && (
                <span className="ai-result-selected-tag">Selected</span>
              )}
            </div>

            <h4 className="ai-result-title">{result.title}</h4>
            <p className="ai-result-summary">{result.summary}</p>

            {result.tags && result.tags.length > 0 && (
              <div className="ai-result-tags">
                {result.tags.map((tag) => (
                  <span key={tag} className="ai-result-tag">
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {onTraceReady && (
              <div style={{ marginTop: '1rem', textAlign: 'right' }}>
                <button
                  type="button"
                  className="cta"
                  onClick={handlePlaceOnMap}
                  style={{ fontSize: '1.05rem', padding: '8px 16px' }}
                >
                  Place on Map &rarr;
                </button>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
};

