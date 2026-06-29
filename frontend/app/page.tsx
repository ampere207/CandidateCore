'use client';

import React, { useState } from 'react';
import Layout from '@/components/layout/Layout';
import UploadZone from '@/components/upload/UploadZone';
import { Card } from '@/components/common/Card';
import { Loading } from '@/components/common/Loading';
import { 
  runPipeline, 
  projectCandidate, 
  enrichCandidate, 
  CanonicalCandidate, 
  PipelineRunResponse,
  ProjectionConfig 
} from '@/lib/api';
import { 
  Layers, 
  Database, 
  Sparkles, 
  Settings, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  FileText,
  Activity
} from 'lucide-react';

export default function PipelinePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<PipelineRunResponse | null>(null);
  const [canonicalCandidate, setCanonicalCandidate] = useState<CanonicalCandidate | null>(null);
  const [enriching, setEnriching] = useState(false);
  const [projecting, setProjecting] = useState(false);
  const [projectedOutput, setProjectedOutput] = useState<Record<string, any> | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'projection'>('profile');

  // Projection controls state
  const [selectedFields, setSelectedFields] = useState<string[]>(['first_name', 'last_name', 'emails', 'skills']);
  const [excludeFields, setExcludeFields] = useState<string[]>(['phones']);
  const [requiredFields, setRequiredFields] = useState<string[]>(['emails']);
  const [renames, setRenames] = useState({
    first_name: 'firstName',
    last_name: 'lastName'
  });

  const handleFilesSelected = (newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleRunPipeline = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setPipelineResult(null);
    setCanonicalCandidate(null);
    setProjectedOutput(null);
    try {
      const response = await runPipeline(files);
      setPipelineResult(response);
      
      if (response.status === 'COMPLETED' && response.candidate_id) {
        // Mock retrieval or construct canonical profile from the run structure
        // Since we are in Phase 1 backend, we mock retrieve candidate
        const mockCandidate: CanonicalCandidate = {
          candidate_id: response.candidate_id,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          first_name: {
            value: "Alex",
            metadata: {
              provenance: {
                source_id: "recruiter_csv",
                source_type: "recruiter_csv",
                extraction_timestamp: new Date().toISOString(),
                raw_value: "alex",
                extractor_version: "1.0.0"
              },
              confidence: {
                score: 0.85,
                confidence_method: "exact_match",
                assessment_details: { match: "csv_column" }
              }
            },
            history: [
              {
                provenance: { source_id: "ats_json", source_type: "ats_json", extraction_timestamp: new Date().toISOString(), raw_value: "Alexander", extractor_version: "1.0.0" },
                confidence: { score: 0.95, confidence_method: "direct_sync", assessment_details: {} }
              }
            ]
          },
          last_name: {
            value: "Rivera",
            metadata: {
              provenance: {
                source_id: "ats_json",
                source_type: "ats_json",
                extraction_timestamp: new Date().toISOString(),
                raw_value: "Rivera",
                extractor_version: "1.0.0"
              },
              confidence: {
                score: 0.95,
                confidence_method: "direct_sync",
                assessment_details: {}
              }
            },
            history: []
          },
          emails: {
            value: ["alex.rivera@example.com"],
            metadata: {
              provenance: {
                source_id: "ats_json",
                source_type: "ats_json",
                extraction_timestamp: new Date().toISOString(),
                raw_value: ["alex.rivera@example.com"],
                extractor_version: "1.0.0"
              },
              confidence: {
                score: 1.0,
                confidence_method: "regex_format_check",
                assessment_details: {}
              }
            },
            history: [
              {
                provenance: { source_id: "recruiter_csv", source_type: "recruiter_csv", extraction_timestamp: new Date().toISOString(), raw_value: "alexr@example.com", extractor_version: "1.0.0" },
                confidence: { score: 0.8, confidence_method: "regex_format_check", assessment_details: {} }
              }
            ]
          },
          phones: {
            value: ["+15550199"],
            metadata: {
              provenance: {
                source_id: "resume_pdf",
                source_type: "resume_pdf",
                extraction_timestamp: new Date().toISOString(),
                raw_value: "555-0199",
                extractor_version: "1.0.0"
              },
              confidence: {
                score: 0.85,
                confidence_method: "phone_cleaner",
                assessment_details: {}
              }
            },
            history: []
          },
          skills: {
            value: ["Python", "Machine Learning", "React", "Node.js"],
            metadata: {
              provenance: {
                source_id: "resume_pdf",
                source_type: "resume_pdf",
                extraction_timestamp: new Date().toISOString(),
                raw_value: ["python3", "Machine Learning"],
                extractor_version: "1.0.0"
              },
              confidence: {
                score: 0.9,
                confidence_method: "synonym_mapper",
                assessment_details: {}
              }
            },
            history: [
              {
                provenance: { source_id: "recruiter_notes", source_type: "recruiter_notes", extraction_timestamp: new Date().toISOString(), raw_value: ["React", "nodejs"], navigator_version: "1.0.0" } as any,
                confidence: { score: 0.7, confidence_method: "unstructured_extractor", assessment_details: {} }
              }
            ]
          },
          metadata: {
            resolved_sources_count: response.processed_sources.length
          }
        };
        setCanonicalCandidate(mockCandidate);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEnrichCandidate = async () => {
    if (!canonicalCandidate) return;
    setEnriching(true);
    try {
      const response = await enrichCandidate(canonicalCandidate);
      setCanonicalCandidate(response);
    } catch (err) {
      console.error(err);
    } finally {
      setEnriching(false);
    }
  };

  const handleProjectCandidate = async () => {
    if (!canonicalCandidate) return;
    setProjecting(true);
    try {
      const config: ProjectionConfig = {
        selected_fields: selectedFields,
        field_mappings: renames,
        exclude_fields: excludeFields,
        required_fields: requiredFields,
        output_format: 'json'
      };
      const response = await projectCandidate(canonicalCandidate, config);
      setProjectedOutput(response.projected_data);
    } catch (err) {
      console.error(err);
    } finally {
      setProjecting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100 bg-gradient-to-r from-neutral-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
            Candidate Ingestion Workspace
          </h1>
          <p className="text-sm text-neutral-400 max-w-2xl">
            Upload multiple recruiter sheets, ATS files, and resume documents. 
            The canonicalization engine resolves identity overlaps and merges fields deterministically.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Panel: Ingestion Control */}
          <div className="lg:col-span-5 space-y-6">
            <Card title="Source Payload Ingest" description="Load source files into the pipeline queue">
              <UploadZone 
                onFilesSelected={handleFilesSelected} 
                files={files} 
                onRemoveFile={handleRemoveFile} 
              />
              <button
                type="button"
                disabled={files.length === 0 || loading}
                onClick={handleRunPipeline}
                className="w-full mt-5 px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-neutral-800 disabled:text-neutral-500 disabled:cursor-not-allowed text-sm font-semibold text-neutral-100 flex items-center justify-center space-x-2 transition duration-200 shadow-lg shadow-indigo-600/20"
              >
                {loading ? (
                  <span>Executing Pipeline Run...</span>
                ) : (
                  <>
                    <Activity className="w-4 h-4" />
                    <span>Run Canonicalization Run</span>
                  </>
                )}
              </button>
            </Card>

            {/* Pipeline Status Reports */}
            {pipelineResult && (
              <Card title="Execution Summary" description={`Job reference: ${pipelineResult.job_id}`}>
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
                    <span className="text-xs text-neutral-400">Job Status</span>
                    <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center space-x-1.5 ${
                      pipelineResult.status === 'COMPLETED' 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {pipelineResult.status === 'COMPLETED' ? (
                        <>
                          <CheckCircle2 className="w-3 h-3 mr-1 inline" />
                          COMPLETED
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-3 h-3 mr-1 inline" />
                          FAILED
                        </>
                      )}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-bold text-neutral-400 uppercase tracking-wide">Ingested Sources</p>
                    <div className="space-y-1">
                      {pipelineResult.processed_sources.map((src, i) => (
                        <div key={src+i} className="flex items-center space-x-2 text-xs text-neutral-300">
                          <FileText className="w-3.5 h-3.5 text-neutral-500" />
                          <span>{src}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {pipelineResult.errors.length > 0 && (
                    <div className="space-y-2 border-t border-neutral-800 pt-3">
                      <p className="text-xs font-bold text-rose-400 uppercase tracking-wide flex items-center">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                        Captured Logs & Errors
                      </p>
                      <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                        {pipelineResult.errors.map((err, idx) => (
                          <div key={idx} className="p-2 rounded-lg bg-rose-950/15 border border-rose-900/35 text-[11px]">
                            <p className="font-semibold text-rose-300">
                              {err.source ? `[${err.source}] ` : ''}{err.error_type}
                            </p>
                            <p className="text-neutral-400 mt-0.5">{err.message}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>

          {/* Right Panel: Canonical Candidate Output & Traceability */}
          <div className="lg:col-span-7">
            {loading ? (
              <Card>
                <Loading />
              </Card>
            ) : canonicalCandidate ? (
              <div className="space-y-6">
                
                {/* Tabs */}
                <div className="flex border-b border-neutral-800 space-x-6">
                  <button
                    onClick={() => setActiveTab('profile')}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                      activeTab === 'profile' 
                        ? 'border-indigo-500 text-indigo-400' 
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Canonical Candidate Profile
                  </button>
                  <button
                    onClick={() => setActiveTab('projection')}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
                      activeTab === 'projection' 
                        ? 'border-indigo-500 text-indigo-400' 
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'
                    }`}
                  >
                    Target Schema Projections
                  </button>
                </div>

                {activeTab === 'profile' ? (
                  <div className="space-y-6">
                    {/* General profile card */}
                    <Card 
                      title={`${canonicalCandidate.first_name?.value} ${canonicalCandidate.last_name?.value}`} 
                      description={`Canonical ID: ${canonicalCandidate.candidate_id}`}
                    >
                      
                      {/* Enrichment actions */}
                      <div className="flex items-center justify-between bg-indigo-950/10 border border-indigo-900/40 rounded-xl p-3 mb-6">
                        <div className="space-y-0.5">
                          <p className="text-xs font-semibold text-indigo-300 flex items-center">
                            <Sparkles className="w-3.5 h-3.5 mr-1" />
                            Semantic Enrichment Engine
                          </p>
                          <p className="text-[10px] text-neutral-400">
                            Apply post-merging semantic inference rules.
                          </p>
                        </div>
                        <button
                          type="button"
                          disabled={enriching || canonicalCandidate.metadata?.semantic_enrichment_applied}
                          onClick={handleEnrichCandidate}
                          className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-950/30 disabled:text-indigo-600 disabled:border disabled:border-indigo-900/50 text-xs font-semibold text-neutral-100 transition duration-200"
                        >
                          {enriching ? 'Enriching...' : canonicalCandidate.metadata?.semantic_enrichment_applied ? 'Enriched' : 'Enrich Profile'}
                        </button>
                      </div>

                      {/* Display profile fields with explainability */}
                      <div className="space-y-5">
                        <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-widest border-b border-neutral-800/60 pb-2">
                          Explainable Canonical Attributes
                        </h4>

                        {[
                          { label: 'First Name', field: canonicalCandidate.first_name },
                          { label: 'Last Name', field: canonicalCandidate.last_name },
                          { label: 'Emails', field: canonicalCandidate.emails },
                          { label: 'Phones', field: canonicalCandidate.phones },
                          { label: 'Location', field: canonicalCandidate.location },
                          { label: 'Skills', field: canonicalCandidate.skills },
                        ].map((row, index) => {
                          if (!row.field) return null;
                          return (
                            <div key={row.label + index} className="space-y-2 group">
                              <div className="flex items-start justify-between">
                                <div>
                                  <span className="text-xs font-semibold text-neutral-400 block mb-1">{row.label}</span>
                                  <span className="text-sm font-medium text-neutral-200">
                                    {Array.isArray(row.field.value) ? row.field.value.join(', ') : row.field.value}
                                  </span>
                                </div>
                                <div className="text-right">
                                  <span className="inline-block text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                    Source: {row.field.metadata.provenance.source_type}
                                  </span>
                                  <span className="block text-[10px] text-neutral-400 mt-1">
                                    Confidence: {(row.field.metadata.confidence.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                              
                              {/* Field history details */}
                              <div className="mt-2 pl-3 border-l border-neutral-800 space-y-1.5 opacity-60 hover:opacity-100 transition-opacity">
                                <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Lineage Trace</p>
                                <div className="space-y-1">
                                  <div className="text-[11px] text-neutral-300">
                                    <span className="text-emerald-400 font-semibold">[WINNER]</span> value:{" "}
                                    <span className="font-mono text-neutral-400">
                                      {JSON.stringify(row.field.metadata.provenance.raw_value || row.field.value)}
                                    </span>{" "}
                                    from <span className="underline">{row.field.metadata.provenance.source_id}</span>
                                  </div>
                                  {row.field.history.map((h, i) => (
                                    <div key={i} className="text-[11px] text-neutral-400">
                                      <span className="text-neutral-500 font-semibold">[OVERRIDDEN]</span> value:{" "}
                                      <span className="font-mono text-neutral-500">
                                        {JSON.stringify(h.provenance.raw_value)}
                                      </span>{" "}
                                      from <span className="underline">{h.provenance.source_id}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          );
                        })}

                        {/* Semantic Metadata Section */}
                        {canonicalCandidate.metadata?.semantic_enrichment_applied && (
                          <div className="mt-4 p-4 rounded-xl border border-indigo-900/30 bg-indigo-950/5 space-y-2">
                            <h5 className="text-xs font-bold text-indigo-400 uppercase tracking-wide">
                              Enriched Profile Insights
                            </h5>
                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <span className="text-neutral-400">Inferred Seniority:</span>
                                <p className="font-semibold text-neutral-200 mt-0.5">
                                  {canonicalCandidate.metadata.inferred_seniority}
                                </p>
                              </div>
                              <div>
                                <span className="text-neutral-400">Enriched Timestamp:</span>
                                <p className="font-semibold text-neutral-200 mt-0.5">
                                  {new Date().toLocaleTimeString()}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                      </div>
                    </Card>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Projection Config panel */}
                    <Card title="Configure Export Projection" description="Apply schema transforms and mappings before outputting to external systems.">
                      <div className="space-y-5">
                        <div>
                          <label className="text-xs font-semibold text-neutral-400 block mb-2">Selected Export Fields (White-list)</label>
                          <div className="flex flex-wrap gap-2">
                            {['first_name', 'last_name', 'emails', 'phones', 'location', 'skills'].map((f) => (
                              <button
                                type="button"
                                key={f}
                                onClick={() => {
                                  setSelectedFields(prev => 
                                    prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                  );
                                }}
                                className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg border transition ${
                                  selectedFields.includes(f)
                                    ? 'bg-indigo-600 border-indigo-500 text-neutral-100'
                                    : 'border-neutral-800 text-neutral-400 hover:border-neutral-700'
                                }`}
                              >
                                {f}
                              </button>
                            ))}
                          </div>
                        </div>

                        <div>
                          <label className="text-xs font-semibold text-neutral-400 block mb-2">Explicit Exclusions</label>
                          <div className="flex flex-wrap gap-2">
                            {['first_name', 'last_name', 'emails', 'phones', 'location', 'skills'].map((f) => (
                              <button
                                type="button"
                                key={f}
                                onClick={() => {
                                  setExcludeFields(prev => 
                                    prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                  );
                                }}
                                className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg border transition ${
                                  excludeFields.includes(f)
                                    ? 'bg-rose-950 border-rose-900 text-rose-300'
                                    : 'border-neutral-800 text-neutral-400 hover:border-neutral-700'
                                }`}
                              >
                                {f}
                              </button>
                            ))}
                          </div>
                        </div>

                        <div>
                          <label className="text-xs font-semibold text-neutral-400 block mb-2">Field Mappings (Rename rules)</label>
                          <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                            <div className="flex items-center space-x-2">
                              <span className="text-neutral-400">first_name</span>
                              <ArrowRight className="w-3.5 h-3.5 text-neutral-600" />
                              <input
                                type="text"
                                value={renames.first_name}
                                onChange={(e) => setRenames(prev => ({ ...prev, first_name: e.target.value }))}
                                className="bg-neutral-900 border border-neutral-800 rounded px-2 py-1 text-neutral-200 outline-none focus:border-indigo-500"
                              />
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-neutral-400">last_name</span>
                              <ArrowRight className="w-3.5 h-3.5 text-neutral-600" />
                              <input
                                type="text"
                                value={renames.last_name}
                                onChange={(e) => setRenames(prev => ({ ...prev, last_name: e.target.value }))}
                                className="bg-neutral-900 border border-neutral-800 rounded px-2 py-1 text-neutral-200 outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={handleProjectCandidate}
                          disabled={projecting}
                          className="w-full mt-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-neutral-800 text-xs font-semibold text-neutral-100 transition duration-200 shadow-md shadow-indigo-600/10"
                        >
                          {projecting ? 'Generating Projection...' : 'Run Export Projection'}
                        </button>
                      </div>
                    </Card>

                    {projectedOutput && (
                      <Card title="Projected Export Payload" description="System flat projection result">
                        <pre className="p-4 bg-neutral-950 border border-neutral-900 rounded-xl overflow-x-auto text-[11px] font-mono text-indigo-300">
                          {JSON.stringify(projectedOutput, null, 2)}
                        </pre>
                      </Card>
                    )}
                  </div>
                )}

              </div>
            ) : (
              <div className="h-96 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                <Database className="w-8 h-8 text-neutral-600 mb-3" />
                <h4 className="text-sm font-semibold text-neutral-400">Awaiting Ingestion Run</h4>
                <p className="text-xs text-neutral-500 max-w-xs mt-1">
                  Upload file payloads and trigger the execution pipeline to visualize canonical fields.
                </p>
              </div>
            )}
          </div>

        </div>

      </div>
    </Layout>
  );
}
