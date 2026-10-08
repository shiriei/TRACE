import React, { useState } from 'react';
import { TraceMediaItem, AudioMediaItem, VoiceMediaItem, VideoMediaItem, PhotoMediaItem } from '../../../types/trace';

interface TraceMediaGalleryProps {
  media: TraceMediaItem[];
}

function formatDuration(seconds?: number): string {
  if (!seconds || seconds <= 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export const TraceMediaGallery: React.FC<TraceMediaGalleryProps> = ({ media }) => {
  const [playingMediaId, setPlayingMediaId] = useState<string | null>(null);

  if (!media || media.length === 0) {
    return (
      <div className="field-media-empty">
        <svg
          className="field-media-empty-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
          <circle cx="12" cy="13" r="3" />
        </svg>
        <span className="field-media-empty-text">No capture attached yet.</span>
      </div>
    );
  }

  return (
    <div className="field-media-gallery" aria-label="Field captures">
      <div className="field-media-list">
        {media.map((item) => {
          if (item.type === 'photo') {
            const photo = item as PhotoMediaItem;
            return (
              <figure key={photo.id} className="field-media-item field-media-photo">
                <img
                  src={photo.thumbnailUri || photo.uri}
                  alt={photo.caption || photo.filename}
                  className="field-photo-img"
                  loading="lazy"
                />
                {photo.caption && (
                  <figcaption className="field-media-caption">{photo.caption}</figcaption>
                )}
              </figure>
            );
          }

          if (item.type === 'video') {
            const video = item as VideoMediaItem;
            return (
              <div key={video.id} className="field-media-item field-media-video">
                <div className="field-video-preview">
                  {video.thumbnailUri ? (
                    <img src={video.thumbnailUri} alt={video.filename} className="field-video-thumb" />
                  ) : (
                    <div className="field-video-placeholder">
                      <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                        <polygon points="5 3 19 12 5 21 5 3" />
                      </svg>
                    </div>
                  )}
                  {video.duration && (
                    <span className="field-media-duration">{formatDuration(video.duration)}</span>
                  )}
                </div>
                <div className="field-video-meta">
                  <span className="field-media-filename">{video.filename}</span>
                  {video.caption && <p className="field-media-caption">{video.caption}</p>}
                </div>
              </div>
            );
          }

          if (item.type === 'audio' || item.type === 'voice') {
            const audio = item as AudioMediaItem | VoiceMediaItem;
            const isVoice = item.type === 'voice';
            const isPlaying = playingMediaId === audio.id;

            return (
              <div
                key={audio.id}
                className={`field-media-item field-media-audio ${isVoice ? 'field-media-voice' : ''}`}
              >
                <button
                  type="button"
                  className="field-audio-play-btn"
                  onClick={() => setPlayingMediaId(isPlaying ? null : audio.id)}
                  aria-label={isPlaying ? 'Pause audio' : 'Play audio capture'}
                >
                  {isPlaying ? (
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                      <rect x="6" y="4" width="4" height="16" />
                      <rect x="14" y="4" width="4" height="16" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                  )}
                </button>
                <div className="field-audio-details">
                  <div className="field-audio-headline">
                    <span className="field-audio-badge">
                      {isVoice ? 'Voice Note' : 'Field Sound'}
                    </span>
                    <span className="field-media-filename">{audio.filename}</span>
                  </div>
                  {audio.duration && (
                    <span className="field-media-duration">{formatDuration(audio.duration)}</span>
                  )}
                  {isVoice && (audio as VoiceMediaItem).transcriptDraft && (
                    <blockquote className="field-voice-transcript">
                      &ldquo;{(audio as VoiceMediaItem).transcriptDraft}&rdquo;
                    </blockquote>
                  )}
                </div>

                {/* If audio has local URI, support native playback */}
                {audio.uri && (
                  <audio
                    src={audio.uri}
                    controls={false}
                    onPlay={() => setPlayingMediaId(audio.id)}
                    onEnded={() => setPlayingMediaId(null)}
                  />
                )}
              </div>
            );
          }

          return (
            <div key={item.id} className="field-media-item field-media-generic">
              <span className="field-media-filename">{item.filename}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
