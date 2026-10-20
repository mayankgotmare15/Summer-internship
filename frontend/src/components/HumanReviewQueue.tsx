import React, { useState } from 'react';
import { CheckCircle, UserCheck } from 'lucide-react';
import { submitFeedback } from '../services/api';

interface ReviewItem {
  id: string;
  subject: string;
  text: string;
  predictedCategory: string;
  confidence: number;
  reason: string;
  priority: string;
  createdAt: string;
}

const INITIAL_QUEUE: ReviewItem[] = [
  {
    id: 'T-1042',
    subject: 'Outlook password loop & printer offline',
    text: 'outlook keeps asking password and my printer is also not working in the 4th floor finance bay',
    predictedCategory: 'Access',
    confidence: 0.54,
    reason: 'multi_issue',
    priority: 'Medium',
    createdAt: '12 mins ago',
  },
  {
    id: 'T-1045',
    subject: 'Access to migration repo vs project setup',
    text: 'request access to the project repo for the migration work along with local admin rights',
    predictedCategory: 'Internal Project',
    confidence: 0.61,
    reason: 'low_confidence',
    priority: 'High',
    createdAt: '24 mins ago',
  },
  {
    id: 'T-1049',
    subject: 'Misc query regarding desk equipment',
    text: 'general question regarding desk monitors and cable organizers for new team members',
    predictedCategory: 'Miscellaneous',
    confidence: 0.82,
    reason: 'miscellaneous',
    priority: 'Low',
    createdAt: '45 mins ago',
  },
];

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

export const HumanReviewQueue: React.FC = () => {
  const [queue, setQueue] = useState<ReviewItem[]>(INITIAL_QUEUE);
  const [selectedTicket, setSelectedTicket] = useState<ReviewItem | null>(queue[0] || null);
  const [targetCategory, setTargetCategory] = useState<string>('Access');
  const [targetPriority, setTargetPriority] = useState<string>('Medium');
  const [triageNote, setTriageNote] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSelect = (item: ReviewItem) => {
    setSelectedTicket(item);
    setTargetCategory(item.predictedCategory);
    setTargetPriority(item.priority);
    setTriageNote(`Agent resolved ${item.reason} triage`);
    setSuccessMsg(null);
  };

  const handleTriageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;

    try {
      await submitFeedback({
        prediction_id: 'triage-' + selectedTicket.id,
        kind: 'agent_correction',
        predicted_category: selectedTicket.predictedCategory,
        corrected_category: targetCategory,
        predicted_priority: selectedTicket.priority,
        corrected_priority: targetPriority,
        notes: triageNote,
      });

      setSuccessMsg(`Ticket ${selectedTicket.id} triaged to ${targetCategory}. Model feedback recorded!`);
      const remaining = queue.filter((t) => t.id !== selectedTicket.id);
      setQueue(remaining);
      setSelectedTicket(remaining[0] || null);
    } catch (err) {
      console.error('Failed to log triage feedback:', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-ink">Service Desk Human Review Queue</h2>
          <p className="text-sm text-muted-light">
            Review tickets where the model detected ambiguous multi-issues, low confidence, or miscellaneous scope.
          </p>
        </div>
        <div className="text-xs bg-san px-3 py-1.5 rounded-full border border-line-light font-mono text-ink">
          Pending Review: <strong>{queue.length} tickets</strong>
        </div>
      </div>

      {successMsg && (
        <div className="bg-status-success-bg border border-status-success/30 text-status-success p-3 rounded-card text-xs font-semibold flex items-center space-x-2">
          <CheckCircle className="w-4 h-4" />
          <span>{successMsg}</span>
        </div>
      )}

      {queue.length === 0 ? (
        <div className="bg-paper border border-line-light rounded-panel p-12 text-center shadow-card">
          <CheckCircle className="w-12 h-12 text-status-success mx-auto mb-3" />
          <h3 className="font-bold text-lg text-ink">Queue All Clear!</h3>
          <p className="text-xs text-muted-light mt-1">All ambiguous tickets have been triaged and logged as retraining data.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Ticket List */}
          <div className="md:col-span-1 space-y-3">
            {queue.map((item) => (
              <div
                key={item.id}
                onClick={() => handleSelect(item)}
                className={`p-4 rounded-card border transition-all cursor-pointer ${
                  selectedTicket?.id === item.id
                    ? 'bg-paper border-orange shadow-card ring-1 ring-orange'
                    : 'bg-paper/70 border-line-light hover:bg-paper'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono font-bold text-ink">{item.id}</span>
                  <span className="text-muted-light">{item.createdAt}</span>
                </div>
                <h4 className="text-sm font-bold text-ink line-clamp-1">{item.subject}</h4>
                <div className="flex items-center justify-between mt-2.5">
                  <span className="text-[11px] font-mono bg-status-warning-bg text-status-warning px-2 py-0.5 rounded font-bold uppercase">
                    {item.reason}
                  </span>
                  <span className="text-xs text-muted-light font-mono">
                    Conf: {Math.round(item.confidence * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Triage Detail & Decision */}
          {selectedTicket && (
            <div className="md:col-span-2 bg-paper border border-line-light rounded-panel p-6 shadow-card space-y-5">
              <div className="flex items-center justify-between border-b border-line-light pb-3">
                <div>
                  <span className="text-xs font-mono font-bold text-orange">{selectedTicket.id}</span>
                  <h3 className="text-base font-bold text-ink">{selectedTicket.subject}</h3>
                </div>
                <span className="text-xs bg-status-warning-bg text-status-warning px-2.5 py-1 rounded font-bold uppercase">
                  Flagged: {selectedTicket.reason}
                </span>
              </div>

              <div>
                <label className="text-xs font-bold text-muted-light uppercase block mb-1">
                  Requester Problem Text:
                </label>
                <div className="bg-san/50 border border-line-light p-3.5 rounded-card text-sm text-ink font-sans">
                  "{selectedTicket.text}"
                </div>
              </div>

              {/* Model suggestion comparison */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="bg-san/30 p-3 rounded-card border border-line-light">
                  <span className="text-muted-light block uppercase font-bold text-[10px]">Model Prediction</span>
                  <span className="text-sm font-bold text-ink mt-0.5 block">{selectedTicket.predictedCategory}</span>
                  <span className="text-muted-light text-[11px]">Confidence: {Math.round(selectedTicket.confidence * 100)}%</span>
                </div>
                <div className="bg-san/30 p-3 rounded-card border border-line-light">
                  <span className="text-muted-light block uppercase font-bold text-[10px]">Triage Fallback Policy</span>
                  <span className="text-sm font-bold text-ink mt-0.5 block">Human Service Desk</span>
                  <span className="text-muted-light text-[11px]">Action required before routing</span>
                </div>
              </div>

              {/* Triage Action Form */}
              <form onSubmit={handleTriageSubmit} className="space-y-4 border-t border-line-light pt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase text-ink mb-1">
                      Assign To Category:
                    </label>
                    <select
                      value={targetCategory}
                      onChange={(e) => setTargetCategory(e.target.value)}
                      className="w-full text-xs bg-san/60 border border-line-light rounded-input p-2.5 text-ink font-medium focus:ring-1 focus:ring-orange focus:outline-none"
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase text-ink mb-1">
                      Set Priority:
                    </label>
                    <select
                      value={targetPriority}
                      onChange={(e) => setTargetPriority(e.target.value)}
                      className="w-full text-xs bg-san/60 border border-line-light rounded-input p-2.5 text-ink font-medium focus:ring-1 focus:ring-orange focus:outline-none"
                    >
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                      <option value="Critical">Critical</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-ink mb-1">
                    Triage Notes (Audited):
                  </label>
                  <input
                    type="text"
                    value={triageNote}
                    onChange={(e) => setTriageNote(e.target.value)}
                    placeholder="Reason for category assignment..."
                    className="w-full text-xs bg-san/60 border border-line-light rounded-input px-3 py-2 text-ink focus:ring-1 focus:ring-orange focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-nero hover:bg-nero-700 text-white font-sans font-bold text-xs py-2.5 rounded-card transition-colors flex items-center justify-center space-x-2 shadow-sm"
                >
                  <UserCheck className="w-4 h-4" />
                  <span>Assign Ticket &amp; Log Model Feedback</span>
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
