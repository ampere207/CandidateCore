import apiClient from './axios';

// ==========================================
// LEGACY DOMAIN MODELS (For Compatibility)
// ==========================================
export interface ProvenanceMetadata {
  source_id: string;
  source_type: string;
  extraction_timestamp: string;
  raw_value: any;
  extractor_version: string;
}

export interface ConfidenceMetadata {
  score: number;
  confidence_method: string;
  assessment_details: Record<string, any>;
}

export interface FieldMetadata {
  provenance: ProvenanceMetadata;
  confidence: ConfidenceMetadata;
}

export interface CompetingValue {
  value: any;
  source_id: string;
  source_type: string;
  confidence_score: number;
  normalization_success: boolean;
  validation_success: boolean;
}

export interface CanonicalField<T> {
  value: T;
  metadata: FieldMetadata;
  history: FieldMetadata[];
  competing_values?: CompetingValue[];
  selection_reason?: string;
}

export interface CanonicalCandidate {
  candidate_id: string;
  created_at: string;
  updated_at: string;
  first_name?: CanonicalField<string>;
  last_name?: CanonicalField<string>;
  emails?: CanonicalField<string[]>;
  phones?: CanonicalField<string[]>;
  location?: CanonicalField<string>;
  skills?: CanonicalField<string[]>;
  experience?: CanonicalField<Array<Record<string, any>>>;
  education?: CanonicalField<Array<Record<string, any>>>;
  metadata: Record<string, any>;
}

// ==========================================
// NEW EXTERNAL OUTPUT SCHEMA (CandidateOutput)
// ==========================================
export interface LocationOutput {
  city: string | null;
  region: string | null;
  country: string | null;
}

export interface LinksOutput {
  linkedin: string | null;
  github: string | null;
  portfolio: string | null;
  other: string[];
}

export interface SkillItemOutput {
  name: string;
  confidence: number;
  sources: string[];
}

export interface ExperienceItemOutput {
  company: string;
  title: string;
  start: string;
  end: string | null;
  summary: string | null;
}

export interface EducationItemOutput {
  institution: string;
  degree: string;
  field: string | null;
  end_year: number | null;
}

export interface ProvenanceItemOutput {
  field: string;
  selected_source: string;
  confidence: number;
  reason: string;
}

export interface MetadataOutput {
  generated_at: string;
  pipeline_version: string;
  sources_processed: number;
  ai_enrichment_enabled: boolean;
}

export interface AISemanticSummaryOutput {
  professional_summary: string | null;
  core_strengths: string[];
  recommended_roles: string[];
  technical_highlights: string[];
  leadership_signals: string[];
  communication_signals: string[];
  interview_focus: string[];
  recruiter_insights: string[];
  potential_concerns: string[];
}

export interface CandidateOutput {
  candidate_id: string;
  full_name: string;
  emails: string[];
  phones: string[];
  location: LocationOutput;
  links: LinksOutput;
  headline: string | null;
  years_experience: number | null;
  skills: SkillItemOutput[];
  experience: ExperienceItemOutput[];
  education: EducationItemOutput[];
  provenance: ProvenanceItemOutput[];
  overall_confidence: number;
  metadata: MetadataOutput;
  ai_semantic_summary: AISemanticSummaryOutput | null;
}

export interface PipelineRunResponse {
  job_id: string;
  status: string;
  processed_sources: string[];
  errors: Array<{
    source?: string;
    field?: string;
    error_type: string;
    message: string;
    critical: boolean;
  }>;
  candidate_id?: string;
}

export interface ProjectionConfig {
  selected_fields: string[];
  field_mappings: Record<string, string>;
  exclude_fields: string[];
  required_fields: string[];
  output_format: string;
}

/**
 * Runs the candidate ingestion and canonicalization pipeline.
 */
export const runPipeline = async (files: File[], enableEnrichment: boolean = false): Promise<PipelineRunResponse> => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  formData.append('enable_enrichment', String(enableEnrichment));

  const response = await apiClient.post<PipelineRunResponse>('/pipeline/run', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Transforms candidate profiles through custom filters and renames by ID.
 */
export const projectCandidate = async (
  candidateId: string,
  config: ProjectionConfig
): Promise<{ success: boolean; projected_data: CandidateOutput }> => {
  const response = await apiClient.post<{ success: boolean; projected_data: CandidateOutput }>(
    `/projection/${candidateId}`,
    config
  );
  return response.data;
};

/**
 * Appends semantic tag integrations on top of canonical profiles by ID.
 */
export const enrichCandidate = async (candidateId: string): Promise<CandidateOutput> => {
  const response = await apiClient.post<CandidateOutput>(`/semantic-enrichment/${candidateId}`);
  return response.data;
};

/**
 * Queries FastAPI system status indicators.
 */
export const checkHealth = async (): Promise<{ status: string; timestamp: string; service: string }> => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Retrieves a canonical candidate profile by ID (projected to CandidateOutput).
 */
export const getCandidate = async (id: string): Promise<CandidateOutput> => {
  const response = await apiClient.get<CandidateOutput>(`/pipeline/candidate/${id}`);
  return response.data;
};
