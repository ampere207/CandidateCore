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
  getCandidate,
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
  Activity,
  Info,
  ChevronRight,
  Lock,
  RefreshCw,
  Award
} from 'lucide-react';

type PipelineStage = 'idle' | 'ingesting' | 'parsing' | 'validating' | 'normalizing' | 'merging' | 'completed' | 'failed';

export default function PipelinePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [pipelineState, setPipelineState] = useState<PipelineStage>('idle');
  const [pipelineResult, setPipelineResult] = useState<PipelineRunResponse | null>(null);
  const [canonicalCandidate, setCanonicalCandidate] = useState<CanonicalCandidate | null>(null);
  const [enriching, setEnriching] = useState(false);
  const [projecting, setProjecting] = useState(false);
  const [projectedOutput, setProjectedOutput] = useState<Record<string, any> | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'projection'>('profile');
  
  // Explainability drawer selection
  const [selectedFieldKey, setSelectedFieldKey] = useState<string | null>(null);

  // Projection configuration state
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

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const handleRunPipeline = async () => {
    if (files.length === 0) return;
    setPipelineState('ingesting');
    setPipelineResult(null);
    setCanonicalCandidate(null);
    setProjectedOutput(null);
    setSelectedFieldKey(null);

    try {
      // Step-by-step progress visualizer transitions
      await sleep(1000);
      setPipelineState('parsing');
      await sleep(1000);
      setPipelineState('validating');
      await sleep(1000);
      setPipelineState('normalizing');
      await sleep(800);
      setPipelineState('merging');

      const response = await runPipeline(files);
      setPipelineResult(response);
      
      if (response.status === 'COMPLETED' && response.candidate_id) {
        // Fetch the real CanonicalCandidate profile from backend!
        const profile = await getCandidate(response.candidate_id);
        setCanonicalCandidate(profile);
        setPipelineState('completed');
        setSelectedFieldKey('first_name'); // Auto-select first name in lineage drawer
      } else {
        setPipelineState('failed');
      }
    } catch (err: any) {
      console.error(err);
      setPipelineState('failed');
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

  const pipelineStages = [
    { name: 'Payload Ingest', key: 'ingesting' },
    { name: 'Adapter Parse', key: 'parsing' },
    { name: 'Schema Validate', key: 'validating' },
    { name: 'Normalize', key: 'normalizing' },
    { name: 'Field-level Merge', key: 'merging' }
  ];

  const getStageColor = (stageKey: PipelineStage) => {
    const order = ['idle', 'ingesting', 'parsing', 'validating', 'normalizing', 'merging', 'completed'];
    const currentIdx = order.indexOf(pipelineState);
    const targetIdx = order.indexOf(stageKey);

    if (pipelineState === 'failed') return 'border-rose-900 bg-rose-950/10 text-rose-500';
    if (pipelineState === 'completed') return 'border-emerald-500 bg-emerald-500/10 text-emerald-400';
    if (currentIdx > targetIdx) return 'border-indigo-500 bg-indigo-500/10 text-indigo-400';
    if (currentIdx === targetIdx) return 'border-indigo-400 bg-neutral-900 text-indigo-300 animate-pulse';
    return 'border-neutral-800 bg-neutral-950/40 text-neutral-600';
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Title */}
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100 bg-gradient-to-r from-neutral-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
            Talent Ingestion Control Panel
          </h1>
          <p className="text-sm text-neutral-400 max-w-3xl">
            Fully automated canonicalization pipeline that processes resumes, ATS profiles, recruiter spreadsheets, and interview writeups. Identity overlap resolved field-by-field.
          </p>
        </div>

        {/* Horizontal Progress Tracker */}
        {pipelineState !== 'idle' && (
          <div className="border border-neutral-800/80 bg-neutral-950/50 rounded-2xl p-4 shadow-xl backdrop-blur-xl">
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-3">
              Pipeline Execution Trace Status
            </p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {pipelineStages.map((stage) => (
                <div
                  key={stage.key}
                  className={`border rounded-xl p-3 text-xs font-semibold flex items-center justify-between transition-all duration-300 ${getStageColor(stage.key as PipelineStage)}`}
                >
                  <span>{stage.name}</span>
                  {pipelineState === 'completed' || (pipelineState !== 'failed' && ['ingesting', 'parsing', 'validating', 'normalizing', 'merging'].indexOf(pipelineState) > ['ingesting', 'parsing', 'validating', 'normalizing', 'merging'].indexOf(stage.key)) ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : pipelineState === 'failed' ? (
                    <AlertTriangle className="w-4 h-4 text-rose-500" />
                  ) : pipelineState === stage.key ? (
                    <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-neutral-800" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Block: File uploads & Execution Details */}
          <div className="lg:col-span-4 space-y-6">
            <Card title="Source Payload Ingest" description="Upload heterogeneous candidate files to load raw fragments.">
              <UploadZone 
                onFilesSelected={handleFilesSelected} 
                files={files} 
                onRemoveFile={handleRemoveFile} 
              />
              <button
                type="button"
                disabled={files.length === 0 || ['ingesting', 'parsing', 'validating', 'normalizing', 'merging'].includes(pipelineState)}
                onClick={handleRunPipeline}
                className="w-full mt-5 px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-neutral-900 disabled:text-neutral-600 disabled:border disabled:border-neutral-800/60 disabled:cursor-not-allowed text-xs font-semibold text-neutral-100 flex items-center justify-center space-x-2 transition duration-200 shadow-lg shadow-indigo-600/10"
              >
                <Activity className="w-4 h-4" />
                <span>Run Canonicalization Pipeline</span>
              </button>
            </Card>

            {/* Run logs/warnings */}
            {pipelineResult && (
              <Card title="Ingestion Report" description={`Pipeline job ID: ${pipelineResult.job_id}`}>
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-neutral-850 pb-3">
                    <span className="text-xs text-neutral-400">Resolution Status</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                      pipelineResult.status === 'COMPLETED' 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {pipelineResult.status}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wide">Processed Documents</p>
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
                    <div className="space-y-2 border-t border-neutral-850 pt-3">
                      <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-wide flex items-center">
                        <AlertTriangle className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
                        Captured Logs & Warnings
                      </p>
                      <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                        {pipelineResult.errors.map((err, idx) => (
                          <div 
                            key={idx} 
                            className={`p-2 rounded-xl border text-[11px] ${
                              err.critical 
                                ? 'bg-rose-950/10 border-rose-900/40 text-rose-300' 
                                : 'bg-amber-950/10 border-amber-900/30 text-amber-300'
                            }`}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span>{err.field ? `[Field: ${err.field}]` : `[Source: ${err.source}]`}</span>
                              <span>{err.error_type}</span>
                            </div>
                            <p className="text-neutral-400 mt-1 leading-normal">{err.message}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>

          {/* Right Block: Render profile layout + lineage explainability drawer */}
          <div className="lg:col-span-8">
            {['ingesting', 'parsing', 'validating', 'normalizing', 'merging'].includes(pipelineState) ? (
              <Card className="py-12">
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
                    Export Target Projection
                  </button>
                </div>

                {activeTab === 'profile' ? (
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                    
                    {/* Left: General Attributes and List Collections */}
                    <div className="md:col-span-7 space-y-6">
                      
                      {/* Name Summary Block */}
                      <Card className="bg-gradient-to-br from-neutral-900/60 to-neutral-950 border border-neutral-800 shadow-xl">
                        <div className="flex items-start justify-between">
                          <div>
                            <span className="text-[9px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold mb-2 inline-block">
                              Immutable Canonical Record
                            </span>
                            <h2 className="text-2xl font-bold text-neutral-100">
                              {canonicalCandidate.first_name?.value} {canonicalCandidate.last_name?.value}
                            </h2>
                            <p className="text-xs text-neutral-400 mt-1 font-mono">
                              ID: {canonicalCandidate.candidate_id}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="block text-xs font-semibold text-neutral-400">Match completeness</span>
                            <span className="text-xl font-extrabold text-indigo-400">
                              {(canonicalCandidate.metadata?.completeness_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>

                        {/* Enrichment Synopsis section */}
                        <div className="border-t border-neutral-800/80 mt-5 pt-4 space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider flex items-center">
                              <Sparkles className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
                              Semantic Insight Layer
                            </h4>
                            <button
                              type="button"
                              disabled={enriching || canonicalCandidate.metadata?.semantic_enrichment_applied}
                              onClick={handleEnrichCandidate}
                              className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-neutral-900 disabled:text-indigo-600 disabled:border disabled:border-indigo-900/50 text-[10px] font-bold text-neutral-100 transition duration-200"
                            >
                              {enriching ? 'Enriching...' : canonicalCandidate.metadata?.semantic_enrichment_applied ? 'Enriched' : 'Enrich with LLM insights'}
                            </button>
                          </div>

                          {canonicalCandidate.metadata?.semantic_enrichment_applied ? (
                            <div className="space-y-2 text-xs text-neutral-300">
                              <div className="p-3 rounded-xl bg-indigo-950/10 border border-indigo-900/20">
                                <p className="font-semibold text-indigo-300 mb-1">Professional Summary</p>
                                <p className="text-[11px] text-neutral-400 leading-relaxed">
                                  {canonicalCandidate.metadata.semantic_enrichment.professional_summary}
                                </p>
                              </div>
                              <div className="grid grid-cols-2 gap-3 text-[11px]">
                                <div>
                                  <span className="text-neutral-500">Recruiter Synopsis:</span>
                                  <p className="font-medium text-neutral-300 mt-0.5">
                                    "{canonicalCandidate.metadata.semantic_enrichment.recruiter_synopsis}"
                                  </p>
                                </div>
                                <div>
                                  <span className="text-neutral-500">Role Preferences:</span>
                                  <p className="font-medium text-neutral-300 mt-0.5">
                                    {canonicalCandidate.metadata.semantic_enrichment.role_preferences}
                                  </p>
                                </div>
                              </div>
                              <div className="space-y-1 mt-2">
                                <span className="text-neutral-500 text-[10px] block">Inferred Strengths</span>
                                <div className="flex flex-wrap gap-1.5">
                                  {canonicalCandidate.metadata.semantic_enrichment.inferred_strengths.map((str: string, i: number) => (
                                    <span key={i} className="text-[10px] bg-neutral-900 border border-neutral-800 text-neutral-400 px-2 py-0.5 rounded-md">
                                      {str}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <p className="text-[11px] text-neutral-500 leading-normal">
                              LLM-powered semantic profiling is currently disabled. Recruiter observations can be parsed to infer professional summaries, preferences, and strengths.
                            </p>
                          )}
                        </div>
                      </Card>

                      {/* Display Profile Attributes */}
                      <Card title="Canonical Profile Fields" description="Field values resolved via conflict resolution algorithms. Click a field to trace its lineage history.">
                        <div className="space-y-4">
                          {[
                            { label: 'First Name', key: 'first_name', field: canonicalCandidate.first_name },
                            { label: 'Last Name', key: 'last_name', field: canonicalCandidate.last_name },
                            { label: 'Location', key: 'location', field: canonicalCandidate.location },
                            { label: 'Emails', key: 'emails', field: canonicalCandidate.emails },
                            { label: 'Phone Numbers', key: 'phones', field: canonicalCandidate.phones },
                            { label: 'Skills', key: 'skills', field: canonicalCandidate.skills },
                          ].map((item) => {
                            if (!item.field) return null;
                            const isSelected = selectedFieldKey === item.key;
                            return (
                              <div
                                key={item.key}
                                onClick={() => setSelectedFieldKey(item.key)}
                                className={`p-3 rounded-xl border transition cursor-pointer flex items-center justify-between ${
                                  isSelected 
                                    ? 'border-indigo-500 bg-indigo-500/5 shadow-indigo-500/5 shadow-md' 
                                    : 'border-neutral-850 hover:border-neutral-800 hover:bg-neutral-900/20'
                                }`}
                              >
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wide">{item.label}</span>
                                  <p className="text-xs font-semibold text-neutral-200">
                                    {Array.isArray(item.field.value) ? item.field.value.join(', ') : item.field.value}
                                  </p>
                                </div>
                                <div className="flex items-center space-x-3">
                                  <div className="text-right">
                                    <span className="inline-block text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-indigo-950/20 text-indigo-400 border border-indigo-900/30">
                                      {item.field.metadata.provenance.source_type}
                                    </span>
                                    <span className="block text-[10px] text-neutral-400 mt-0.5">
                                      Score: {(item.field.metadata.confidence.score * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <ChevronRight className={`w-4 h-4 transition ${isSelected ? 'text-indigo-400 transform translate-x-0.5' : 'text-neutral-600'}`} />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </Card>

                      {/* Display Education & Experience timelines */}
                      {canonicalCandidate.experience && (
                        <Card title="Deduplicated Work Timeline" description="Aggregated employment histories.">
                          <div className="space-y-3">
                            {canonicalCandidate.experience.value.map((job: any, i: number) => (
                              <div key={i} className="p-3 border border-neutral-850 rounded-xl flex justify-between items-start text-xs">
                                <div className="space-y-1">
                                  <p className="font-bold text-neutral-200">{job.company}</p>
                                  <p className="text-neutral-400">{job.title}</p>
                                </div>
                                <span className="text-neutral-500 font-mono text-[10px]">{job.dates || 'N/A'}</span>
                              </div>
                            ))}
                          </div>
                        </Card>
                      )}

                      {canonicalCandidate.education && (
                        <Card title="Deduplicated Academic Credentials" description="Aggregated education details.">
                          <div className="space-y-3">
                            {canonicalCandidate.education.value.map((edu: any, i: number) => (
                              <div key={i} className="p-3 border border-neutral-850 rounded-xl flex justify-between items-start text-xs">
                                <div className="space-y-1">
                                  <p className="font-bold text-neutral-200">{edu.school}</p>
                                  <p className="text-neutral-400">{edu.degree} {edu.major ? `in ${edu.major}` : ''}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </Card>
                      )}

                    </div>

                    {/* Right: Explainability drawer */}
                    <div className="md:col-span-5 space-y-6 sticky top-24">
                      {selectedFieldKey ? (() => {
                        const fieldMap: Record<string, any> = {
                          first_name: canonicalCandidate.first_name,
                          last_name: canonicalCandidate.last_name,
                          location: canonicalCandidate.location,
                          emails: canonicalCandidate.emails,
                          phones: canonicalCandidate.phones,
                          skills: canonicalCandidate.skills,
                        };
                        const selectedField = fieldMap[selectedFieldKey];
                        if (!selectedField) return null;
                        
                        return (
                          <Card 
                            title="Field Lineage Audit" 
                            description={`Explainability trace for attribute: ${selectedFieldKey}`}
                            className="border border-indigo-500/30 shadow-indigo-950/20 shadow-xl bg-neutral-950"
                          >
                            <div className="space-y-5">
                              {/* Selection Reason */}
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Winner Selection Reason</span>
                                <div className="p-3 rounded-xl bg-indigo-950/15 border border-indigo-900/30 text-xs text-indigo-300 leading-relaxed">
                                  {selectedField.selection_reason || 'Resolved via default config priority rules.'}
                                </div>
                              </div>

                              {/* Target Details */}
                              <div className="grid grid-cols-2 gap-4 text-xs">
                                <div>
                                  <span className="text-neutral-500 block">Winning Source</span>
                                  <span className="font-bold text-neutral-200 mt-0.5 block truncate">
                                    {selectedField.metadata.provenance.source_id}
                                  </span>
                                  <span className="text-[10px] text-neutral-400">
                                    ({selectedField.metadata.provenance.source_type})
                                  </span>
                                </div>
                                <div>
                                  <span className="text-neutral-500 block">Confidence Score</span>
                                  <span className="font-bold text-indigo-400 text-lg mt-0.5 block">
                                    {(selectedField.metadata.confidence.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>

                              {/* Competing inputs trace list */}
                              <div className="space-y-2 border-t border-neutral-850 pt-4">
                                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Competing Inputs Trace</span>
                                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                                  {selectedField.competing_values?.map((comp: any, idx: number) => {
                                    const isWinner = comp.value === selectedField.value || 
                                      (Array.isArray(selectedField.value) && Array.isArray(comp.value) && JSON.stringify(comp.value) === JSON.stringify(selectedField.value));
                                    
                                    return (
                                      <div 
                                        key={idx}
                                        className={`p-2.5 rounded-xl border text-xs space-y-1.5 transition ${
                                          isWinner 
                                            ? 'border-emerald-500/30 bg-emerald-500/5' 
                                            : 'border-neutral-900 bg-neutral-900/20'
                                        }`}
                                      >
                                        <div className="flex items-center justify-between">
                                          <span className="font-mono text-neutral-200 font-bold truncate max-w-[130px]">
                                            {JSON.stringify(comp.value)}
                                          </span>
                                          {isWinner ? (
                                            <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded font-extrabold border border-emerald-500/20 flex items-center">
                                              <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
                                              WINNER
                                            </span>
                                          ) : (
                                            <span className="text-[9px] bg-neutral-900 border border-neutral-850 text-neutral-500 px-1.5 py-0.5 rounded font-bold">
                                              OVERRIDDEN
                                            </span>
                                          )}
                                        </div>

                                        <div className="flex justify-between items-center text-[10px] text-neutral-400 border-t border-neutral-850/50 pt-1.5 mt-1">
                                          <span>Source: {comp.source_type}</span>
                                          <span>Score: {(comp.confidence_score * 100).toFixed(0)}%</span>
                                        </div>

                                        <div className="flex space-x-2 text-[9px] pt-1">
                                          <span className={`px-1.5 py-0.5 rounded ${comp.normalization_success ? 'bg-neutral-900 text-neutral-400 border border-neutral-850' : 'bg-amber-950/20 text-amber-400 border border-amber-900/30'}`}>
                                            Norm: {comp.normalization_success ? 'Success' : 'Fallback'}
                                          </span>
                                          <span className={`px-1.5 py-0.5 rounded ${comp.validation_success ? 'bg-neutral-900 text-neutral-400 border border-neutral-850' : 'bg-rose-950/20 text-rose-400 border border-rose-900/30'}`}>
                                            Valid: {comp.validation_success ? 'Passed' : 'Failed'}
                                          </span>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>

                            </div>
                          </Card>
                        );
                      })() : (
                        <div className="h-64 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                          <Info className="w-6 h-6 text-neutral-600 mb-2" />
                          <h4 className="text-xs font-semibold text-neutral-400">Select Attribute for Lineage</h4>
                          <p className="text-[10px] text-neutral-500 max-w-xs mt-1">
                            Click any canonical field card on the left to verify its extraction lineage, competing scores, and tie-breakers.
                          </p>
                        </div>
                      )}
                    </div>

                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Projection Config panel */}
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                      
                      <div className="md:col-span-6 space-y-6">
                        <Card title="Configure Export Projection" description="Apply custom renaming, mappings, and validation checks before export.">
                          <div className="space-y-5">
                            <div>
                              <label className="text-xs font-bold text-neutral-400 block mb-2">Field Whitelist Selection</label>
                              <div className="flex flex-wrap gap-2">
                                {['first_name', 'last_name', 'emails', 'phones', 'location', 'skills', 'experience', 'education'].map((f) => (
                                  <button
                                    type="button"
                                    key={f}
                                    onClick={() => {
                                      setSelectedFields(prev => 
                                        prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                      );
                                    }}
                                    className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition ${
                                      selectedFields.includes(f)
                                        ? 'bg-indigo-600 border-indigo-500 text-neutral-100'
                                        : 'border-neutral-850 text-neutral-400 hover:border-neutral-800'
                                    }`}
                                  >
                                    {f}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div>
                              <label className="text-xs font-bold text-neutral-400 block mb-2">Omit Fields (Exclusion list)</label>
                              <div className="flex flex-wrap gap-2">
                                {['first_name', 'last_name', 'emails', 'phones', 'location', 'skills', 'experience', 'education'].map((f) => (
                                  <button
                                    type="button"
                                    key={f}
                                    onClick={() => {
                                      setExcludeFields(prev => 
                                        prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                      );
                                    }}
                                    className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition ${
                                      excludeFields.includes(f)
                                        ? 'bg-rose-950 border-rose-900/60 text-rose-300'
                                        : 'border-neutral-850 text-neutral-450 hover:border-neutral-850'
                                    }`}
                                  >
                                    {f}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div>
                              <label className="text-xs font-bold text-neutral-400 block mb-2">Required Constraints</label>
                              <div className="flex flex-wrap gap-2">
                                {['first_name', 'last_name', 'emails', 'phones', 'location', 'skills', 'experience', 'education'].map((f) => (
                                  <button
                                    type="button"
                                    key={f}
                                    onClick={() => {
                                      setRequiredFields(prev => 
                                        prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                      );
                                    }}
                                    className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition ${
                                      requiredFields.includes(f)
                                        ? 'bg-amber-950 border-amber-900 text-amber-300'
                                        : 'border-neutral-850 text-neutral-450 hover:border-neutral-850'
                                    }`}
                                  >
                                    {f}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div>
                              <label className="text-xs font-bold text-neutral-400 block mb-2">Nested Mappings (Rename targets)</label>
                              <div className="space-y-2.5 text-xs font-mono">
                                <div className="flex items-center space-x-3">
                                  <span className="text-neutral-450 w-24">first_name</span>
                                  <ArrowRight className="w-3.5 h-3.5 text-neutral-700" />
                                  <input
                                    type="text"
                                    value={renames.first_name}
                                    onChange={(e) => setRenames(prev => ({ ...prev, first_name: e.target.value }))}
                                    className="bg-neutral-900 border border-neutral-850 rounded-lg px-2.5 py-1 text-neutral-200 outline-none focus:border-indigo-500 flex-1"
                                  />
                                </div>
                                <div className="flex items-center space-x-3">
                                  <span className="text-neutral-450 w-24">last_name</span>
                                  <ArrowRight className="w-3.5 h-3.5 text-neutral-700" />
                                  <input
                                    type="text"
                                    value={renames.last_name}
                                    onChange={(e) => setRenames(prev => ({ ...prev, last_name: e.target.value }))}
                                    className="bg-neutral-900 border border-neutral-850 rounded-lg px-2.5 py-1 text-neutral-200 outline-none focus:border-indigo-500 flex-1"
                                  />
                                </div>
                              </div>
                            </div>

                            <button
                              type="button"
                              onClick={handleProjectCandidate}
                              disabled={projecting}
                              className="w-full mt-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-neutral-900 text-xs font-semibold text-neutral-100 transition duration-200 shadow-md shadow-indigo-600/10"
                            >
                              {projecting ? 'Generating target mappings...' : 'Execute Export Projection'}
                            </button>
                          </div>
                        </Card>
                      </div>

                      <div className="md:col-span-6 space-y-6">
                        {projectedOutput ? (
                          <Card title="Generated Schema Output" description="Projected JSON results.">
                            <pre className="p-4 bg-neutral-950 border border-neutral-900 rounded-2xl overflow-x-auto text-[11px] font-mono text-indigo-300 max-h-[450px]">
                              {JSON.stringify(projectedOutput, null, 2)}
                            </pre>
                          </Card>
                        ) : (
                          <div className="h-96 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                            <Lock className="w-6 h-6 text-neutral-600 mb-2" />
                            <h4 className="text-xs font-semibold text-neutral-400">Awaiting Export Generation</h4>
                            <p className="text-[10px] text-neutral-500 max-w-xs mt-1">
                              Configure renaming keys and whitelist attributes, then click project candidate to inspect export output structures.
                            </p>
                          </div>
                        )}
                      </div>

                    </div>
                  </div>
                )}

              </div>
            ) : (
              <div className="h-96 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                <Database className="w-8 h-8 text-neutral-600 mb-3" />
                <h4 className="text-sm font-semibold text-neutral-400">Awaiting Pipeline Execution</h4>
                <p className="text-xs text-neutral-500 max-w-xs mt-1">
                  Ingest source documents and trigger the pipeline. Merged attributes with full lineage audits will display here.
                </p>
              </div>
            )}
          </div>

        </div>

      </div>
    </Layout>
  );
}
