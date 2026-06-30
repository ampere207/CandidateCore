import apiClient from './axios';

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

export interface CanonicalField<T> {
  value: T;
  metadata: FieldMetadata;
  history: FieldMetadata[];
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
export const runPipeline = async (files: File[]): Promise<PipelineRunResponse> => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await apiClient.post<PipelineRunResponse>('/pipeline/run', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Transforms candidate profiles through custom filters and renames.
 */
export const projectCandidate = async (
  candidate: CanonicalCandidate,
  config: ProjectionConfig
): Promise<{ success: boolean; projected_data: Record<string, any> }> => {
  const response = await apiClient.post('/projection', { candidate, config });
  return response.data;
};

/**
 * Appends semantic tag integrations on top of canonical profiles.
 */
export const enrichCandidate = async (candidate: CanonicalCandidate): Promise<CanonicalCandidate> => {
  const response = await apiClient.post<CanonicalCandidate>('/semantic-enrichment', candidate);
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
 * Retrieves a canonical candidate profile by ID.
 */
export const getCandidate = async (id: string): Promise<CanonicalCandidate> => {
  const response = await apiClient.get<CanonicalCandidate>(`/pipeline/candidate/${id}`);
  return response.data;
};
