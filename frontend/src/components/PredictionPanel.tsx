import React, { useState } from 'react';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import type { FeedbackIn, PredictionOut } from '../types';
import { submitFeedback } from '../services/api';

interface PredictionPanelProps {
  prediction: PredictionOut | null;
  loading: boolean;
}

const CATEGORIES = [
  'Access',
  'Administrative rights',
  'Hardware',
  'HR Support',
  'Internal Project',
  'Miscellaneous',
  'Purchase',
  'Storage',
];

export const PredictionPanel: React.FC<PredictionPanelProps> = ({
  prediction,
  loading,
}) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [correctedCat, setCorrectedCat] = useState('');
  const [correctedPrio, setCorrectedPrio] = useState('Medium');
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [submittingFb, setSubmittingFb] = useState(false);

  if (loading) {
    return (
      <div className="bg-paper border border-line-light rounded-panel p-6 shadow-card flex flex-col items-center justify-center min-h-[360px] text-center">
        <div className="w-12 h-12 rounded-full border-4 border-orange/20 border-t-orange animate-spin mb-4"></div>
        <h4 className="font-sans font-bold text-lg text-ink">Analyzing Ticket Semantics...</h4>
        <p className="text-sm text-muted-light max-w-xs mt-1">
          Evaluating confidence against champion threshold <strong className="font-mono text-ink">τ=0.69</strong>
        </p>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="bg-paper border border-dashed border-line-light rounded-panel p-8 shadow-card flex flex-col items-center justify-center min-h-[360px] text-center">
        <div className="w-14 h-14 rounded-2xl bg-san flex items-center justify-center text-orange mb-3">
          <Bot className="w-7 h-7" />
        </div>
        <h4 className="font-sans font-bold text-lg text-ink">Dual-Head ML Prediction</h4>
        <p className="text-sm text-muted-light max-w-sm mt-1">
          Type or select a benchmark ticket on the left. The model will predict the resolver queue, confidence score, and priority in real-time.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs font-mono text-muted-light">
          <span className="bg-san px-2 py-1 rounded">Macro-F1: 0.855</span>
          <span className="bg-san px-2 py-1 rounded">Threshold: 0.69</span>
          <span className="bg-san px-2 py-1 rounded">P95: &lt;50ms</span>
        </div>
      </div>
    );
  }

  const isAuto = prediction.decision === 'auto_route';
  const confPct = Math.round(prediction.category_confidence * 100);

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingFb(true);
    const payload: FeedbackIn = {
      prediction_id: prediction.prediction_id,
      kind: 'requester_not_quite',
      predicted_category: prediction.category,
      corrected_category: correctedCat || prediction.category,
      predicted_priority: prediction.priority,
      corrected_priority: correctedPrio,
      notes: feedbackNotes || 'Corrected via intake feedback widget',
    };
    try {
      await submitFeedback(payload);
      setFeedbackSubmitted(true);
      setShowFeedback(false);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingFb(false);
    }
  };

  return (
    <div className="bg-paper border border-line-light rounded-panel p-6 shadow-card space-y-6">
      {/* Top Banner: Decision Card */}
      <div
        className={`p-4 rounded-card border flex items-start justify-between ${
          isAuto
            ? 'bg-status-success-bg/40 border-status-success/30'
            : 'bg-status-warning-bg/40 border-status-warning/30'
        }`}
      >
        <div className="flex items-start space-x-3">
          {isAuto ? (
            <div className="w-9 h-9 rounded-full bg-status-success text-white flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-9 h-9 rounded-full bg-status-warning text-white flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
          )}
          <div>
            <div className="flex items-center space-x-2">
              <span
                className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                  isAuto ? 'bg-status-success text-white' : 'bg-status-warning text-white'
                }`}
              >
                {isAuto ? 'Auto-Route Confirmed' : 'Human Review Required'}
              </span>
              <span className="text-xs font-mono text-muted-light">
                τ={prediction.threshold}
              </span>
            </div>
            <p className="text-sm font-semibold text-ink mt-1">
              {isAuto
                ? `Confidence exceeds threshold. Direct routing to ${prediction.routed_team.name}.`
                : prediction.review_reason === 'multi_issue'
                ? 'Multiple distinct issues detected. Sent to Service Desk triage.'
                : prediction.review_reason === 'low_confidence'
                ? `Confidence (${confPct}%) is below automation threshold (${Math.round(prediction.threshold * 100)}%).`
                : 'Ticket routed to human review.'}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono bg-san text-ink px-2 py-1 rounded">
            {prediction.latency_ms} ms
          </span>
        </div>
      </div>

      {/* Main Prediction Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Category & Confidence */}
        <div className="bg-san/50 border border-line-light p-4 rounded-card">
          <span className="text-xs uppercase font-bold text-muted-light tracking-wider">
            Predicted Category
          </span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-lg font-bold text-ink">{prediction.category}</span>
            <span className="font-mono font-bold text-orange text-sm">{confPct}%</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-san h-2 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                confPct >= 69 ? 'bg-orange' : 'bg-status-warning'
              }`}
              style={{ width: `${confPct}%` }}
            ></div>
          </div>
        </div>

        {/* Priority & Source */}
        <div className="bg-san/50 border border-line-light p-4 rounded-card">
          <span className="text-xs uppercase font-bold text-muted-light tracking-wider">
            Assigned Priority
          </span>
          <div className="flex items-baseline justify-between mt-1">
            <span
              className={`px-2 py-0.5 rounded text-sm font-bold ${
                prediction.priority === 'Critical'
                  ? 'bg-status-danger-bg text-status-danger'
                  : prediction.priority === 'High'
                  ? 'bg-orange/20 text-orange'
                  : 'bg-san text-ink'
              }`}
            >
              {prediction.priority}
            </span>
            <span className="text-xs font-mono text-muted-light">
              via {prediction.priority_source}
            </span>
          </div>
          <p className="text-[11px] text-muted-light mt-2">
            {prediction.priority_source === 'rule'
              ? 'Elevated by keyword / team outage rule'
              : 'Classified by priority model'}
          </p>
        </div>
      </div>

      {/* Suggested Team & Top Categories */}
      <div className="border-t border-line-light pt-4 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-light font-medium">Assigned Resolver Queue:</span>
          <strong className="text-ink font-semibold">{prediction.routed_team.name} ({prediction.routed_team.code})</strong>
        </div>

        {/* Top Keywords / Salient features */}
        {prediction.top_keywords && prediction.top_keywords.length > 0 && (
          <div>
            <span className="text-xs text-muted-light block mb-1 font-medium">
              Explainability Features:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {prediction.top_keywords.map((kw, idx) => (
                <span
                  key={idx}
                  className="bg-san text-ink text-xs px-2 py-0.5 rounded border border-line-light font-mono"
                >
                  #{kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Feedback Notification Alert */}
      {feedbackSubmitted && (
        <div className="bg-status-success-bg border border-status-success/40 text-status-success p-3 rounded-lg text-xs font-medium flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Feedback captured! Retraining cycle will ingest this label correction.</span>
        </div>
      )}

      {/* Not Quite Right? Drawer */}
      <div className="border-t border-line-light pt-3">
        <button
          type="button"
          onClick={() => {
            setShowFeedback(!showFeedback);
            setCorrectedCat(prediction.category);
          }}
          className="text-xs text-orange font-bold hover:underline flex items-center space-x-1"
        >
          <span>Not quite right? Provide feedback</span>
          {showFeedback ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showFeedback && (
          <form onSubmit={handleFeedbackSubmit} className="mt-3 bg-san/70 p-3 rounded-lg border border-line-light space-y-2.5">
            <div>
              <label className="text-[11px] font-bold text-muted-light uppercase block">
                Correct Category:
              </label>
              <select
                value={correctedCat}
                onChange={(e) => setCorrectedCat(e.target.value)}
                className="w-full text-xs bg-paper border border-line-light rounded px-2 py-1.5 mt-0.5 text-ink focus:outline-none focus:ring-1 focus:ring-orange"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[11px] font-bold text-muted-light uppercase block">
                Correct Priority:
              </label>
              <select
                value={correctedPrio}
                onChange={(e) => setCorrectedPrio(e.target.value)}
                className="w-full text-xs bg-paper border border-line-light rounded px-2 py-1.5 mt-0.5 text-ink focus:outline-none focus:ring-1 focus:ring-orange"
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
            <div>
              <input
                type="text"
                placeholder="Optional correction note..."
                value={feedbackNotes}
                onChange={(e) => setFeedbackNotes(e.target.value)}
                className="w-full text-xs bg-paper border border-line-light rounded px-2 py-1.5 text-ink focus:outline-none focus:ring-1 focus:ring-orange"
              />
            </div>
            <button
              type="submit"
              disabled={submittingFb}
              className="w-full bg-nero text-white text-xs font-bold py-1.5 rounded hover:bg-nero-700 transition-colors"
            >
              {submittingFb ? 'Submitting...' : 'Submit Correction'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
