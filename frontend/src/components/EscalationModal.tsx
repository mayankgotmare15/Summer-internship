import React, { useEffect, useState } from 'react';
import type { DirectoryMember, EscalateIn, TicketDetailOut } from '../types';
import { escalateTicket, getDirectoryMembers } from '../services/api';

interface EscalationModalProps {
  ticket: TicketDetailOut;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export const EscalationModal: React.FC<EscalationModalProps> = ({ ticket, onClose, onSuccess }) => {
  const [members, setMembers] = useState<DirectoryMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [reasonCode, setReasonCode] = useState<EscalateIn['reason_code']>('business_critical');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMembers() {
      try {
        setLoadingMembers(true);
        const data = await getDirectoryMembers();
        setMembers(data);
        // Preselect team lead if available
        const lead = data.find((m) => m.role === 'team_lead' && !m.on_leave);
        if (lead) {
          setSelectedUserId(lead.id);
        } else if (data.length > 0) {
          setSelectedUserId(data[0].id);
        }
      } catch (err: any) {
        console.error('Failed to load directory:', err);
      } finally {
        setLoadingMembers(false);
      }
    }
    loadMembers();
  }, []);

  const filteredMembers = members.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.email.toLowerCase().includes(search.toLowerCase()) ||
      m.role.toLowerCase().includes(search.toLowerCase()) ||
      m.team.toLowerCase().includes(search.toLowerCase())
  );

  const selectedMember = members.find((m) => m.id === selectedUserId);
  const eligibility = ticket.escalation_eligibility;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) {
      setError('Please select an escalation recipient from the directory.');
      return;
    }
    if (note.trim().length < 10) {
      setError('Justification note must be at least 10 characters long.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const res = await escalateTicket(ticket.id, {
        target_user_id: selectedUserId,
        reason_code: reasonCode,
        note: note.trim(),
      });
      onSuccess(res.message || 'Escalation submitted successfully.');
    } catch (err: any) {
      setError(err.message || 'Escalation failed due to guardrail constraints.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden p-6 md:p-8 max-h-[90vh] flex flex-col">
        {/* Glow accent */}
        <div className="absolute -top-24 -right-24 w-60 h-60 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 font-semibold">
                PRD 4B.6 Guardrails
              </span>
              <span className="text-xs text-slate-400">Escalation Request</span>
            </div>
            <h2 className="text-xl font-bold text-slate-100 mt-1">Escalate Ticket {ticket.id}</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto py-4 space-y-5 pr-1">
          {/* Guardrails Info Banner */}
          <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-slate-300">Rate Limit:</span>
              <span className="font-semibold text-slate-100">
                {eligibility.used_last_24h || 0} / {eligibility.max_per_24h || 2} used (24h)
              </span>
            </div>
            <div className="text-slate-400">Cooldown: 60 minutes</div>
          </div>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
              <span className="text-base leading-none">⚠️</span>
              <div>
                <p className="font-semibold">Guardrail Validation Alert</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* Reason Code */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Reason for Escalation
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {[
                { code: 'business_critical', label: 'Business Critical', desc: 'Higher severity than initially recorded' },
                { code: 'wrong_team', label: 'Wrong Team / Misrouted', desc: 'Triggers automated AI retraining event' },
                { code: 'no_response', label: 'No Response within SLA', desc: 'Assignee has not responded on thread' },
                { code: 'deadline_at_risk', label: 'Target Deadline at Risk', desc: 'Pending external dependency' },
                { code: 'other', label: 'Other Justification', desc: 'Special project requirement' },
              ].map((r) => (
                <label
                  key={r.code}
                  className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                    reasonCode === r.code
                      ? 'bg-amber-500/10 border-amber-500/40 text-slate-100'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="reasonCode"
                      value={r.code}
                      checked={reasonCode === r.code}
                      onChange={() => setReasonCode(r.code as any)}
                      className="text-amber-500 focus:ring-0"
                    />
                    <span className="font-semibold text-slate-200">{r.label}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-1 pl-5">{r.desc}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Directory Picker */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Select Escalation Recipient
              </label>
              <span className="text-[11px] text-slate-400">Team Leads & Managers</span>
            </div>

            <div className="relative mb-2">
              <input
                type="text"
                placeholder="Search staff by name, email, role, or team..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3.5 py-2 pl-9 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              />
              <span className="absolute left-3 top-2.5 text-slate-500">🔍</span>
            </div>

            <div className="max-h-40 overflow-y-auto space-y-1.5 border border-slate-800 rounded-2xl p-1.5 bg-slate-950/40">
              {loadingMembers ? (
                <p className="text-xs text-slate-500 text-center py-4">Loading directory roster...</p>
              ) : filteredMembers.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">No matching staff found</p>
              ) : (
                filteredMembers.map((m) => {
                  const isOwner = ticket.assignee?.id === m.id;
                  return (
                    <div
                      key={m.id}
                      onClick={() => !m.on_leave && !isOwner && setSelectedUserId(m.id)}
                      className={`p-2.5 rounded-xl border text-xs flex items-center justify-between transition ${
                        selectedUserId === m.id
                          ? 'bg-indigo-600/20 border-indigo-500/50 text-slate-100'
                          : m.on_leave || isOwner
                          ? 'opacity-50 cursor-not-allowed bg-slate-900 border-slate-800/50'
                          : 'bg-slate-800/40 border-slate-800 hover:border-slate-700 cursor-pointer text-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center font-bold text-[10px]">
                          {m.name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-200">{m.name}</p>
                          <p className="text-[10px] text-slate-400">
                            {m.role === 'team_lead' ? 'Team Lead' : m.role === 'manager' ? 'IT Manager' : 'Engineer'} • {m.team}
                          </p>
                        </div>
                      </div>

                      {/* Status Badges */}
                      <div>
                        {m.on_leave ? (
                          <div className="text-right">
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300">
                              On Leave
                            </span>
                            {m.delegate && (
                              <p className="text-[9px] text-slate-400 mt-0.5">Delegate: {m.delegate.split('@')[0]}</p>
                            )}
                          </div>
                        ) : isOwner ? (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-400">
                            Current Owner
                          </span>
                        ) : (
                          <span className="text-[10px] text-emerald-400 font-medium">Available</span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {selectedMember && (
              <p className="text-[11px] text-slate-400 mt-1.5">
                Target: <span className="text-slate-200 font-medium">{selectedMember.name}</span> ({selectedMember.email})
              </p>
            )}
          </div>

          {/* Justification Note */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Justification Note (Required)
              </label>
              <span className="text-[11px] text-slate-500">Min 10 characters</span>
            </div>
            <textarea
              rows={3}
              placeholder="Describe business impact, reason for escalation, and urgency..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition resize-none"
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !eligibility.allowed}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white text-xs font-semibold shadow-lg shadow-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 transition"
            >
              {submitting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <span>Raise Escalation</span>
                  <span>🚀</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
