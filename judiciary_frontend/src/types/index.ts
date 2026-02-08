/* ---- Types for the Judiciary System ---- */

export interface Case {
  id: string;
  case_number: string;
  title: string;
  court: string;
  bench?: string;
  case_type?: string;
  year?: number;
  status?: string;
  appellants?: string[];
  respondents?: string[];
  judge_names?: string[];
  summary?: string;
  full_text?: string;
  judgment_text?: string;
  headnotes?: string;
  judgment_date?: string;
  filing_date?: string;
  cited_cases?: string[];
  cited_statutes?: string[];
  cited_articles?: string[];
  locations?: string[];
  categories?: string[];
  tags?: string[];
  source_url?: string;
  pdf_url?: string;
  source?: string;
  scraped_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CaseCard {
  id: string;
  case_number: string;
  title: string;
  court: string;
  case_type?: string;
  year?: number;
  status?: string;
  judge_names?: string[];
  summary?: string;
  judgment_date?: string;
  source?: string;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface User {
  id: string;
  auth_id?: string;
  first_name: string;
  last_name?: string;
  gender?: string;
  phone_number?: string;
  cnic_number?: string;
  organization?: string;
  country?: string;
  province?: string;
  city?: string;
  address?: string;
  subscription?: string;
  saved_cases?: string[];
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  message: string;
  token: string;
  user: User;
}

export interface ScrapeJob {
  id: string;
  source: string;
  status: string;
  total_pages: number;
  pages_scraped: number;
  cases_found: number;
  cases_new: number;
  cases_updated: number;
  errors_count: number;
  config: Record<string, unknown>;
  logs: ScrapeLog[];
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface ScrapeLog {
  timestamp: string;
  message: string;
  level: string;
}

export interface DashboardStats {
  total_cases: number;
  recent_cases_30d: number;
  total_courts: number;
  scraper: {
    total_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    latest_job: ScrapeJob | null;
  };
  cases_by_source: { source: string; count: number }[];
}

export interface SearchFilters {
  courts: string[];
  case_types: string[];
  statuses: string[];
  year_range: { min: number | null; max: number | null };
  judges: { name: string; count: number }[];
  sources: string[];
}

export interface CourtAnalytics {
  name: string;
  total_cases: number;
  decided: number;
  pending: number;
  adjourned: number;
  disposed: number;
  enacted: number;
  unknown: number;
}

export interface TimelineData {
  month: string;
  count: number;
}

/* ---- AI / Chat Types ---- */

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  language: string;
  citations: string[];
  timestamp?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  context_type: string;
  context_case_id?: string;
  messages: ChatMessage[];
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  context_type: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AIResponse {
  session_id: string;
  response: string;
  language: string;
  citations: string[];
  suggestions: string[];
}

export interface CaseAnalysis {
  analysis: string;
  key_facts: {
    parties_count: number;
    statutes_cited: number;
    cases_cited: number;
    judges: number;
  };
}

export interface SimilarCase {
  id: string;
  case_number: string;
  title: string;
  court: string;
  year?: number;
  similarity: number;
}

/* ---- Document Types ---- */

export interface ExtractedEntity {
  entity_type: string;
  value: string;
  confidence: number;
}

export interface LegalDocument {
  id: string;
  user_id: string;
  case_id?: string;
  original_filename: string;
  file_size: number;
  mime_type?: string;
  doc_type: string;
  summary: string;
  language: string;
  status: string;
  entities: ExtractedEntity[];
  has_text: boolean;
  extracted_text?: string;
  created_at: string;
  updated_at: string;
}

/* ---- Extraction Types ---- */

export interface ExtractionResult {
  case_numbers: string[];
  statutes: string[];
  courts: string[];
  judges: string[];
  dates: string[];
  persons: string[];
  organizations: string[];
  locations: string[];
  monetary_values: string[];
  all_entities: ExtractedEntity[];
}

/* ---- Translation Types ---- */

export interface TranslationResult {
  original_text: string;
  translated_text: string;
  source_lang: string;
  target_lang: string;
  terms_translated: { original: string; translated: string }[];
  is_partial: boolean;
  note: string;
}

export interface GlossaryTerm {
  english: string;
  urdu: string;
}

/* ---- Lawyer Types ---- */

export interface Lawyer {
  id: string;
  name: string;
  title?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  province?: string;
  bar_council?: string;
  license_number?: string;
  court?: string;
  experience_years?: number;
  specializations: string[];
  languages?: string[];
  bio?: string;
  avg_rating: number;
  total_reviews: number;
  is_verified: boolean;
  created_at: string;
}

export interface LawyerCard {
  id: string;
  name: string;
  title?: string;
  city?: string;
  court?: string;
  experience_years?: number;
  specializations: string[];
  avg_rating: number;
  total_reviews: number;
  is_verified: boolean;
}

/* ---- Template Types ---- */

export interface LegalTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  language: string;
  content: string;
  placeholders: string[];
  court_type?: string;
  jurisdiction?: string;
  usage_count: number;
  is_active: boolean;
  created_at: string;
}

export interface TemplateCard {
  id: string;
  name: string;
  description?: string;
  category: string;
  language: string;
  court_type?: string;
  usage_count: number;
}

export interface TemplateCategory {
  value: string;
  label: string;
}

/* ---- Notification Types ---- */

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: string;
  case_id?: string;
  case_number?: string;
  reminder_date?: string;
  is_recurring: boolean;
  is_read: boolean;
  created_at: string;
}
