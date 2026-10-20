export interface ScoredCategory {
  category: string;
  score: number;
}

export interface TeamRef {
  code: string;
  name: string;
}

export interface PredictionOut {
  category: string;
  category_confidence: number;
  top_categories: ScoredCategory[];
  priority: string;
  priority_confidence: number;
  priority_source: 'model' | 'rule' | 'agent';
  decision: 'auto_route' | 'human_review';
  review_reason?: 'low_confidence' | 'multi_issue' | 'miscellaneous' | 'model_unavailable' | null;
  routed_team: TeamRef;
  threshold: number;
  model_version: string;
  priority_model_version: string;
  prediction_id: string;
  latency_ms: number;
  top_keywords: string[];
}

export interface FeedbackIn {
  prediction_id?: string;
  ticket_id?: string;
  kind: 'agent_correction' | 'wrong_team_escalation' | 'requester_not_quite' | 'priority_correction';
  predicted_category?: string;
  corrected_category?: string;
  predicted_priority?: string;
  corrected_priority?: string;
  notes?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: 'requester' | 'agent' | 'engineer' | 'team_lead' | 'manager' | 'admin';
  department?: string;
  is_demo: boolean;
  access_token?: string;
}

export interface MemberRef {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface TicketCreatedOut {
  id: string;
  ticket_uuid: string;
  status: string;
  category: string;
  priority: string;
  decision: 'auto_route' | 'human_review';
  assignee?: MemberRef | null;
  team: TeamRef;
  first_response_due?: string | null;
  resolution_due?: string | null;
  awaiting_approval_from?: MemberRef | null;
  review_promise_by?: string | null;
  can_escalate: boolean;
}

export interface MessageOut {
  id: string;
  author_name?: string | null;
  kind: string;
  body: string;
  created_at: string;
}

export interface EscalationEligibility {
  allowed: boolean;
  used_last_24h: number;
  max_per_24h: number;
  next_allowed_at?: string | null;
  blocked_reason?: string | null;
}

export interface TicketDetailOut {
  id: string;
  ticket_uuid: string;
  subject: string;
  description: string;
  category: string;
  priority: string;
  priority_source: string;
  status: string;
  decision: string;
  review_reason?: string | null;
  team: TeamRef;
  assignee?: MemberRef | null;
  is_escalated: boolean;
  escalation_level: string;
  first_response_due?: string | null;
  resolution_due?: string | null;
  first_responded_at?: string | null;
  clock_state?: string | null;
  messages: MessageOut[];
  can_escalate: boolean;
  escalation_eligibility: EscalationEligibility;
  created_at: string;
}

export interface DirectoryMember {
  id: string;
  name: string;
  email: string;
  role: string;
  team: string;
  skills: string[];
  on_leave: boolean;
  leave_note?: string | null;
  delegate?: string | null;
}

export interface EscalateIn {
  target_user_id: string;
  reason_code: 'no_response' | 'wrong_team' | 'business_critical' | 'deadline_at_risk' | 'other';
  note: string;
}
