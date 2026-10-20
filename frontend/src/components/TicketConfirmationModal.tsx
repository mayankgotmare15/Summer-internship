import React from 'react';
import type { TicketCreatedOut } from '../types';

interface TicketConfirmationModalProps {
  ticket: TicketCreatedOut;
  onClose: () => void;
  onTrack: (ticketId: string) => void;
}

export const TicketConfirmationModal: React.FC<TicketConfirmationModalProps> = ({
  ticket,
  onClose,
  onTrack,
}) => {
  const formatTime = (isoString?: string | null) => {
    if (!isoString) return 'Pending SLA determination';
    try {
      const dt = new Date(isoString);
      return dt.toLocaleString('en-IN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return isoString;
    }
  };

  const isAutoRouted = ticket.decision === 'auto_route';
  const isAwaitingApproval = ticket.status === 'Awaiting approval';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden p-8">
        {/* Glow accent */}
        <div className="absolute -top-24 -right-24 w-60 h-60 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-60 h-60 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header with Success Icon */}
        <div className="flex items-start gap-4 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 font-semibold">
                {ticket.id}
              </span>
              <span
                className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                  ticket.priority === 'Critical'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : ticket.priority === 'High'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                }`}
              >
                {ticket.priority} Priority
              </span>
            </div>
            <h2 className="text-2xl font-bold text-slate-100 mt-1">Ticket Successfully Received</h2>
            <p className="text-sm text-slate-400">
              {isAwaitingApproval
                ? 'Your request has been routed for manager approval prior to fulfillment.'
                : isAutoRouted
                ? 'Intelligent Auto-Router classified and directly assigned your issue.'
                : 'Assigned to Service Desk Triage Queue for multi-issue review.'}
            </p>
          </div>
        </div>

        {/* Primary Ownership Promise Card (PRD 4B.1) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Named Owner / Triage Card */}
          <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              {isAwaitingApproval ? 'Approver' : 'Assigned Resolver'}
            </p>
            {ticket.assignee ? (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center font-bold text-indigo-300">
                  {ticket.assignee.name.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-100">{ticket.assignee.name}</p>
                  <p className="text-xs text-slate-400">
                    {ticket.assignee.role === 'team_lead' ? 'Team Lead' : 'Engineer (L2 Resolver)'} • {ticket.team.name}
                  </p>
                </div>
              </div>
            ) : isAwaitingApproval && ticket.awaiting_approval_from ? (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-600/30 border border-amber-500/40 flex items-center justify-center font-bold text-amber-300">
                  {ticket.awaiting_approval_from.name.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-100">{ticket.awaiting_approval_from.name}</p>
                  <p className="text-xs text-amber-400">Line Manager Approval Pending</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-300">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-100">{ticket.team.name}</p>
                  <p className="text-xs text-cyan-400">Triage by: {formatTime(ticket.review_promise_by)}</p>
                </div>
              </div>
            )}
          </div>

          {/* SLA Deadlines */}
          <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex flex-col justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">SLA Target Deadlines</p>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">First Response:</span>
                  <span className="font-medium text-slate-200">{formatTime(ticket.first_response_due)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Expected Resolution:</span>
                  <span className="font-semibold text-emerald-400">{formatTime(ticket.resolution_due)}</span>
                </div>
              </div>
            </div>
            <p className="text-[10px] text-slate-500 mt-2 flex items-center gap-1">
              <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Calculated using Business Hours (09:00 - 18:00 IST Mon-Fri).
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-sm font-medium transition"
          >
            Create Another
          </button>
          <button
            onClick={() => onTrack(ticket.id)}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-sm font-semibold shadow-lg shadow-indigo-500/20 flex items-center gap-2 transition"
          >
            <span>Track & Manage Ticket</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
