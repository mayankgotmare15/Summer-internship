import React, { useEffect, useState } from 'react';
import type { TicketDetailOut, UserProfile } from '../types';
import { changeTicketStatus, getTicket, postTicketMessage } from '../services/api';
import { EscalationModal } from './EscalationModal';

interface TicketDetailModalProps {
  ticketId: string;
  currentUser?: UserProfile | null;
  onClose: () => void;
}

export const TicketDetailModal: React.FC<TicketDetailModalProps> = ({
  ticketId,
  currentUser,
  onClose,
}) => {
  const [ticket, setTicket] = useState<TicketDetailOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newMsg, setNewMsg] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [postingMsg, setPostingMsg] = useState(false);
  const [showEscalate, setShowEscalate] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTicket(ticketId);
      setTicket(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load ticket details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [ticketId]);

  const handlePostMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMsg.trim() || !ticket) return;

    try {
      setPostingMsg(true);
      await postTicketMessage(ticket.id, newMsg.trim(), isInternal);
      setNewMsg('');
      setIsInternal(false);
      setActionSuccess(
        ticket.status === 'Waiting on requester' && currentUser?.role === 'requester'
          ? 'Reply posted! SLA clock automatically resumed to "In progress".'
          : 'Update posted to ticket thread.'
      );
      setTimeout(() => setActionSuccess(null), 4000);
      await fetchDetail();
    } catch (err: any) {
      setError(err.message || 'Failed to post message');
    } finally {
      setPostingMsg(false);
    }
  };

  const handleStatusChange = async (toStatus: string) => {
    if (!ticket) return;
    try {
      setStatusUpdating(true);
      const updated = await changeTicketStatus(ticket.id, toStatus, `Status updated to ${toStatus}`);
      setTicket(updated);
      setActionSuccess(`Status changed to ${toStatus}`);
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update status');
    } finally {
      setStatusUpdating(false);
    }
  };

  const formatTime = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    try {
      return new Date(isoString).toLocaleString('en-IN', {
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

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-3">
          <span className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading ticket details...</span>
        </div>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 max-w-md text-center">
          <p className="text-rose-400 font-semibold mb-2">Ticket Not Found</p>
          <p className="text-xs text-slate-400 mb-4">{error || 'Could not retrieve ticket details.'}</p>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const isPaused = ticket.clock_state === 'paused' || ticket.status === 'Waiting on requester';
  const isAgentOrResolver =
    currentUser?.role === 'agent' ||
    currentUser?.role === 'engineer' ||
    currentUser?.role === 'team_lead' ||
    currentUser?.role === 'manager';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Glow accents */}
        <div className="absolute -top-32 -right-32 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header Bar */}
        <div className="p-6 pb-4 border-b border-slate-800 flex items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 font-bold">
                {ticket.id}
              </span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                  ticket.status === 'Resolved'
                    ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                    : ticket.status === 'Waiting on requester'
                    ? 'bg-amber-500/15 border border-amber-500/30 text-amber-300'
                    : ticket.status === 'In progress'
                    ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-300'
                    : 'bg-indigo-500/15 border border-indigo-500/30 text-indigo-300'
                }`}
              >
                {ticket.status}
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                {ticket.category}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  ticket.priority === 'Critical'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold'
                    : ticket.priority === 'High'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {ticket.priority} ({ticket.priority_source})
              </span>
              {ticket.is_escalated && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold flex items-center gap-1">
                  <span>🚨 Escalation</span>
                  <span className="px-1.5 py-0.2 rounded bg-rose-600/40 text-[10px]">{ticket.escalation_level}</span>
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-slate-100">{ticket.subject}</h2>
          </div>

          <div className="flex items-center gap-2">
            {/* Requester Escalation Button (PRD 4B.6) */}
            <button
              onClick={() => setShowEscalate(true)}
              className="px-3.5 py-1.5 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
            >
              <span>Escalate</span>
              <span>⚡</span>
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 flex items-center justify-center transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Success Alert */}
        {actionSuccess && (
          <div className="mx-6 mt-3 p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <span>✓</span>
            <span>{actionSuccess}</span>
          </div>
        )}

        {/* Scrollable Main Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* SLA Clock & Owner Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Clock Widget */}
            <div
              className={`p-4 rounded-2xl border ${
                isPaused
                  ? 'bg-amber-500/5 border-amber-500/30'
                  : 'bg-indigo-500/5 border-indigo-500/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  SLA Clock
                </span>
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-medium flex items-center gap-1.5 ${
                    isPaused
                      ? 'bg-amber-500/20 text-amber-300'
                      : 'bg-emerald-500/20 text-emerald-300'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      isPaused ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'
                    }`}
                  />
                  {isPaused ? 'Paused (Waiting on requester)' : 'Clock Running'}
                </span>
              </div>
              <p className="text-lg font-bold text-slate-100">
                Resolution: {formatTime(ticket.resolution_due)}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                First Response:{' '}
                {ticket.first_responded_at ? (
                  <span className="text-emerald-400 font-medium">
                    ✓ Met ({formatTime(ticket.first_responded_at)})
                  </span>
                ) : (
                  <span>Due by {formatTime(ticket.first_response_due)}</span>
                )}
              </p>
            </div>

            {/* Ownership Card */}
            <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/60">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Named Owner & Team
              </span>
              {ticket.assignee ? (
                <div>
                  <p className="text-sm font-bold text-slate-100">{ticket.assignee.name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {ticket.assignee.role === 'team_lead' ? 'Team Lead' : 'Engineer (L2)'} • {ticket.team.name}
                  </p>
                  <p className="text-[11px] text-indigo-400 font-mono mt-1">{ticket.assignee.email}</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-bold text-cyan-400">{ticket.team.name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">In Service Desk Triage Queue</p>
                </div>
              )}
            </div>

            {/* Status Transition Control (for Agent/Resolver) */}
            <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/60">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Status Controls
              </span>
              <div className="flex flex-wrap gap-1.5">
                {['In progress', 'Waiting on requester', 'Resolved'].map((st) => (
                  <button
                    key={st}
                    onClick={() => handleStatusChange(st)}
                    disabled={statusUpdating || ticket.status === st}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                      ticket.status === st
                        ? 'bg-indigo-600/30 border-indigo-500/60 text-indigo-200 cursor-default'
                        : 'bg-slate-800 border-slate-700 hover:border-slate-600 text-slate-300'
                    }`}
                  >
                    {st === 'Waiting on requester' ? '⏸️ Wait Requester' : st}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-slate-500 mt-2">
                Selecting &quot;Wait Requester&quot; automatically pauses SLA countdown.
              </p>
            </div>
          </div>

          {/* Issue Description */}
          <div className="p-4 rounded-2xl bg-slate-800/20 border border-slate-800">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
              Original Issue Description
            </span>
            <p className="text-xs text-slate-200 whitespace-pre-line leading-relaxed">
              {ticket.description}
            </p>
          </div>

          {/* Conversation & Activity Feed */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Activity & Conversation Thread ({ticket.messages.length})
              </span>
              <span className="text-[11px] text-slate-500 font-mono">
                Created: {formatTime(ticket.created_at)}
              </span>
            </div>

            <div className="space-y-3">
              {ticket.messages.map((m) => {
                const isInternalNote = m.kind === 'internal';
                return (
                  <div
                    key={m.id}
                    className={`p-3.5 rounded-2xl border text-xs ${
                      isInternalNote
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                        : 'bg-slate-800/50 border-slate-700/60 text-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-100">{m.author_name || 'System'}</span>
                        {isInternalNote && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-medium">
                            Internal Note
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">{formatTime(m.created_at)}</span>
                    </div>
                    <p className="whitespace-pre-line leading-relaxed text-slate-300">{m.body}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Reply Box */}
          <form onSubmit={handlePostMessage} className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/60">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Post an Update / Reply
              </label>
              {isAgentOrResolver && (
                <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isInternal}
                    onChange={(e) => setIsInternal(e.target.checked)}
                    className="rounded bg-slate-700 border-slate-600 text-amber-500 focus:ring-0"
                  />
                  <span>Internal Note (staff only)</span>
                </label>
              )}
            </div>

            <textarea
              rows={2}
              placeholder={
                isPaused && currentUser?.role === 'requester'
                  ? 'Replying will automatically resume the SLA clock and switch status to "In progress"...'
                  : 'Type message or update here...'
              }
              value={newMsg}
              onChange={(e) => setNewMsg(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition resize-none"
            />

            <div className="flex items-center justify-between mt-2.5">
              <span className="text-[11px] text-slate-500">
                {isPaused && currentUser?.role === 'requester' && (
                  <span className="text-amber-400 font-medium">
                    ⚡ Clock auto-resumes upon requester message.
                  </span>
                )}
              </span>
              <button
                type="submit"
                disabled={postingMsg || !newMsg.trim()}
                className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition"
              >
                {postingMsg ? (
                  <span>Sending...</span>
                ) : (
                  <>
                    <span>Post Update</span>
                    <span>💬</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Escalation Modal */}
      {showEscalate && (
        <EscalationModal
          ticket={ticket}
          onClose={() => setShowEscalate(false)}
          onSuccess={(msg) => {
            setShowEscalate(false);
            setActionSuccess(msg);
            fetchDetail();
          }}
        />
      )}
    </div>
  );
};
