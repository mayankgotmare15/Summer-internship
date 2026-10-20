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
