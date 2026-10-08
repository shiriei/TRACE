import React, { useState } from 'react';
import { TraceAIResult } from '../../../types';
import { interpretTraceObservation, TraceAIError } from '../../../services/api';

const DEFAULT_SAMPLE = 'I noticed moss growing between bricks near a drain.';

export const TraceAIInterpreter: React.FC = () => {
  const [observation, setObservation] = useState(DEFAULT_SAMPLE);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<TraceAIResult | null>(null);
  const [errorInfo, setErrorInfo] = useState<{ title: string; message: string } | null>(null);

  const handleInterpret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!observation.trim()) return;

    setIsLoading(true);
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
      setIsLoading(false);
    }
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

        <div className="ai-form-actions">
          <button
            type="submit"
            className="cta ai-submit-btn"
            disabled={isLoading || !observation.trim()}
          >
            {isLoading ? 'Interpreting...' : 'Leave a trace'}
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
          </div>
        </div>
      )}

      {/* Successful Result Display */}
      {result && !isLoading && (
        <div className="ai-result-card" style={{ borderColor: getCategoryColor(result.category) }}>
          <div className="ai-result-category" style={{ color: getCategoryColor(result.category) }}>
            <span className="ai-result-cat-icon">{getCategoryEmoji(result.category)}</span>
            <span className="ai-result-cat-name">{result.category}</span>
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
        </div>
      )}
    </div>
  );
};
