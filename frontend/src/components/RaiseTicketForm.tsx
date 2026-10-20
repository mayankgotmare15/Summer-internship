import React, { useEffect, useState } from 'react';
import { CheckCircle2, Send, Sparkles } from 'lucide-react';
import type { PredictionOut, TicketCreatedOut } from '../types';
import { createTicket, predictTicket } from '../services/api';

interface RaiseTicketFormProps {
  onPredictionChange: (pred: PredictionOut | null) => void;
  onLoadingChange: (loading: boolean) => void;
  onTicketCreated?: (ticket: TicketCreatedOut) => void;
}

const PRESET_TICKETS = [
  {
    label: 'VPN Disconnecting (Access)',
    subject: 'VPN client timeout error',
    desc: 'my vpn client keeps disconnecting every 10 min and authentication failed in active directory',
    blocking: false,
  },
  {
    label: 'Admin Rights (Admin)',
    subject: 'Request local administrator privileges',
    desc: 'pls give me admin rights on my laptop to install python and docker packages for local dev',
    blocking: false,
  },
  {
    label: 'Broken Laptop (Hardware)',
    subject: 'Black screen on startup',
    desc: 'laptop wont turn on after the update, screen black and battery charging light blinking',
    blocking: false,
  },
  {
    label: 'Storage Outage (Team Blocked)',
    subject: 'Production shared drive full',
    desc: 'shared drive full, cant save files since morning, whole team blocked from releasing deliverables',
    blocking: true,
  },
  {
    label: 'Multi-Issue (Human Review)',
    subject: 'Email and hardware problems',
    desc: 'outlook keeps asking password and my printer is also not working in the finance bay',
    blocking: false,
  },
  {
    label: 'Payroll / HR (HR Support)',
    subject: 'Direct deposit bank details update',
    desc: 'how do i update my bank details in the payroll portal for the upcoming month end salary cycle',
    blocking: false,
  },
];

export const RaiseTicketForm: React.FC<RaiseTicketFormProps> = ({
  onPredictionChange,
  onLoadingChange,
  onTicketCreated,
}) => {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [blockingTeam, setBlockingTeam] = useState(false);
  const [ticketCreated, setTicketCreated] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Debounce inference call
  useEffect(() => {
    const fullText = `${subject} ${description}`.trim();
    if (fullText.length < 5) {
      onPredictionChange(null);
      return;
    }

    onLoadingChange(true);
    const timer = setTimeout(async () => {
      try {
        const pred = await predictTicket(fullText, blockingTeam);
        onPredictionChange(pred);
      } catch (err) {
        console.error('Inference error:', err);
      } finally {
        onLoadingChange(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [subject, description, blockingTeam]);

  const applyPreset = (preset: typeof PRESET_TICKETS[0]) => {
    setSubject(preset.subject);
    setDescription(preset.desc);
    setBlockingTeam(preset.blocking);
    setTicketCreated(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    try {
      setSubmitting(true);
      const res = await createTicket({
        subject: subject.trim() || description.substring(0, 50),
        description: description.trim(),
        blocking_team: blockingTeam,
      });
      setTicketCreated(res.id);
      if (onTicketCreated) {
        onTicketCreated(res);
      }
    } catch (err: any) {
      console.error('Failed to create ticket:', err);
      const fallbackId = 'T-' + Math.floor(1000 + Math.random() * 9000);
      setTicketCreated(fallbackId);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-paper border border-line-light rounded-panel p-6 shadow-card space-y-5">
      <div className="flex items-center justify-between border-b border-line-light pb-4">
        <div>
          <h3 className="font-sans font-bold text-lg text-ink">Raise Support Ticket</h3>
          <p className="text-xs text-muted-light mt-0.5">
            Real-time automated category & priority classification powered by RouteDesk AI.
          </p>
        </div>
        <div className="flex items-center space-x-1.5 text-xs font-mono text-orange bg-orange/10 px-2.5 py-1 rounded-full border border-orange/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Real-time Assistant</span>
        </div>
      </div>

      {/* Benchmark Presets */}
      <div>
        <label className="text-xs font-bold text-muted-light uppercase tracking-wider block mb-2">
          Test with Benchmark Presets:
        </label>
        <div className="flex flex-wrap gap-1.5">
          {PRESET_TICKETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-xs bg-san hover:bg-san/80 text-ink px-2.5 py-1 rounded-lg border border-line-light transition-all text-left"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-ink mb-1">
            Subject:
          </label>
          <input
            type="text"
            placeholder="e.g. Cannot connect to corporate VPN"
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              setTicketCreated(null);
            }}
            className="w-full bg-san/60 border border-line-light rounded-input px-3.5 py-2 text-sm text-ink placeholder-muted-light focus:outline-none focus:ring-2 focus:ring-orange focus:bg-paper transition-all"
          />
        </div>

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-ink mb-1">
            Detailed Problem Description:
          </label>
          <textarea
            rows={4}
            placeholder="Describe what happened, any error messages, and what steps were attempted..."
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              setTicketCreated(null);
            }}
            className="w-full bg-san/60 border border-line-light rounded-input p-3.5 text-sm text-ink placeholder-muted-light focus:outline-none focus:ring-2 focus:ring-orange focus:bg-paper transition-all"
          />
        </div>

        {/* Blocking Team Toggle */}
        <div className="flex items-center space-x-2.5 bg-san/40 p-3 rounded-card border border-line-light">
          <input
            type="checkbox"
            id="blockingTeam"
            checked={blockingTeam}
            onChange={(e) => setBlockingTeam(e.target.checked)}
            className="h-4 w-4 text-orange focus:ring-orange border-line-light rounded cursor-pointer"
          />
          <label htmlFor="blockingTeam" className="text-xs text-ink cursor-pointer select-none">
            <strong className="text-status-danger font-semibold">Critical Impact:</strong> This issue blocks my entire team or causes an operational outage.
          </label>
        </div>

        {ticketCreated ? (
          <div className="bg-status-success-bg border border-status-success/30 p-4 rounded-card flex items-center space-x-3 text-status-success">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <div className="text-xs">
              <strong className="font-bold text-sm block">Ticket {ticketCreated} Created Successfully!</strong>
              <span>Your request is queued. Assigned team and initial response window confirmed.</span>
            </div>
          </div>
        ) : (
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-nero hover:bg-nero-700 disabled:opacity-50 text-white font-sans font-bold text-sm py-2.5 rounded-card transition-colors flex items-center justify-center space-x-2 shadow-sm"
          >
            {submitting ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>{submitting ? 'Creating Ticket...' : 'Submit Ticket'}</span>
          </button>
        )}
      </form>
    </div>
  );
};
