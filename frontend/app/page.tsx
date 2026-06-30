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
  CandidateOutput, 
  PipelineRunResponse,
  ProjectionConfig 
} from '@/lib/api';
import { 
  Database, 
  Sparkles, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  FileText,
  Activity,
  Info,
  ChevronRight,
  Lock,
  RefreshCw,
  Copy,
  Check,
  Download,
  FileCode,
  ShieldAlert,
  Sliders,
  Sparkle
} from 'lucide-react';

type PipelineStage = 
  | 'idle' 
  | 'detecting' 
  | 'extracting' 
  | 'validating' 
  | 'normalizing' 
  | 'merging' 
  | 'assessing_confidence' 
  | 'projecting' 
  | 'explaining' 
  | 'completed' 
  | 'failed';

export default function PipelinePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [pipelineState, setPipelineState] = useState<PipelineStage>('idle');
  const [pipelineResult, setPipelineResult] = useState<PipelineRunResponse | null>(null);
  const [canonicalCandidate, setCanonicalCandidate] = useState<CandidateOutput | null>(null);
  const [enriching, setEnriching] = useState(false);
  const [projecting, setProjecting] = useState(false);
  const [projectedOutput, setProjectedOutput] = useState<Record<string, any> | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'ai-insights' | 'projection'>('profile');
  const [enableAIEnrichment, setEnableAIEnrichment] = useState(false);
  
  // Explainability selection state
  const [selectedFieldKey, setSelectedFieldKey] = useState<string | null>(null);

  // Projection state configs
  const [selectedFields, setSelectedFields] = useState<string[]>(['full_name', 'emails', 'skills']);
  const [excludeFields, setExcludeFields] = useState<string[]>(['phones']);
  const [requiredFields, setRequiredFields] = useState<string[]>(['emails']);
  const [renames, setRenames] = useState({
    full_name: 'fullName',
    location: 'loc'
  });

  // UI interaction copy / download states
  const [copiedCanonical, setCopiedCanonical] = useState(false);
  const [copiedProjected, setCopiedProjected] = useState(false);

  const handleFilesSelected = (newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  // Run through all 8 stages sequentially
  const handleRunPipeline = async () => {
    if (files.length === 0) return;
    setPipelineState('detecting');
    setPipelineResult(null);
    setCanonicalCandidate(null);
    setProjectedOutput(null);
    setSelectedFieldKey(null);

    try {
      await sleep(600);
      setPipelineState('extracting');
      await sleep(600);
      setPipelineState('validating');
      await sleep(600);
      setPipelineState('normalizing');
      await sleep(600);
      setPipelineState('merging');
      await sleep(600);
      setPipelineState('assessing_confidence');

      const response = await runPipeline(files, enableAIEnrichment);
      setPipelineResult(response);
      
      if (response.status === 'COMPLETED' && response.candidate_id) {
        setPipelineState('projecting');
        await sleep(600);
        setPipelineState('explaining');
        await sleep(600);

        const profile = await getCandidate(response.candidate_id);
        setCanonicalCandidate(profile);
        setPipelineState('completed');
        setSelectedFieldKey('first_name'); // Auto-select focus attribute
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
      const response = await enrichCandidate(canonicalCandidate.candidate_id);
      setCanonicalCandidate(response);
    } catch (err) {
      console.error(err);
    } finally {
      setEnriching(false);
    }
  };

  const handleProjectCandidate = async () => {
    if (!canonicalCandidate) return;
    
    const preCheckWarnings = getConfigurationWarnings();
    if (preCheckWarnings.length > 0) return;

    setProjecting(true);
    try {
      const config: ProjectionConfig = {
        selected_fields: selectedFields,
        field_mappings: renames,
        exclude_fields: excludeFields,
        required_fields: requiredFields,
        output_format: 'json'
      };
      const response = await projectCandidate(canonicalCandidate.candidate_id, config);
      setProjectedOutput(response);
    } catch (err) {
      console.error(err);
    } finally {
      setProjecting(false);
    }
  };

  const getConfigurationWarnings = (): string[] => {
    const warnings: string[] = [];
    requiredFields.forEach(field => {
      if (excludeFields.includes(field)) {
        warnings.push(`Configuration Conflict: Required field '${field}' is currently excluded. Please remove it from exclusions.`);
      }
      if (selectedFields.length > 0 && !selectedFields.includes(field)) {
        warnings.push(`Inclusion Warning: Required field '${field}' is not in the whitelist selection.`);
      }
    });
    return warnings;
  };

  const triggerDownload = (content: string, filename: string, contentType: string) => {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getCandidateNamePrefix = () => {
    if (!canonicalCandidate) return 'candidate';
    return canonicalCandidate.full_name.toLowerCase().replace(/\s+/g, '_');
  };

  const downloadCanonical = () => {
    if (!canonicalCandidate) return;
    const content = JSON.stringify(canonicalCandidate, null, 2);
    triggerDownload(content, `${getCandidateNamePrefix()}_canonical_profile.json`, 'application/json');
  };

  const downloadProjected = () => {
    if (!projectedOutput) return;
    const content = JSON.stringify(projectedOutput, null, 2);
    triggerDownload(content, `${getCandidateNamePrefix()}_projected_profile.json`, 'application/json');
  };

  const downloadExplainability = () => {
    if (!canonicalCandidate) return;
    const report = {
      candidate_id: canonicalCandidate.candidate_id,
      full_name: canonicalCandidate.full_name,
      overall_confidence: canonicalCandidate.overall_confidence,
      generated_at: canonicalCandidate.metadata?.generated_at,
      provenance: canonicalCandidate.provenance
    };
    triggerDownload(JSON.stringify(report, null, 2), `${getCandidateNamePrefix()}_explainability_report.json`, 'application/json');
  };

  const downloadSemanticSummary = () => {
    if (!canonicalCandidate?.ai_semantic_summary) return;
    const se = canonicalCandidate.ai_semantic_summary;
    const content = `CANONICAL PROFILE SEMANTIC REPORT
=================================
Candidate: ${canonicalCandidate.full_name}
Overall Confidence: ${(canonicalCandidate.overall_confidence * 100).toFixed(0)}%
Generated At: ${canonicalCandidate.metadata?.generated_at}

Professional Summary:
---------------------
${se.professional_summary || 'N/A'}

Core Strengths:
---------------
${se.core_strengths?.map((str: string) => `- ${str}`).join('\n') || 'N/A'}

Recruiter Insights:
-------------------
${se.recruiter_insights?.map((str: string) => `- ${str}`).join('\n') || 'N/A'}
`;
    triggerDownload(content, `${getCandidateNamePrefix()}_semantic_summary.txt`, 'text/plain');
  };

  const copyToClipboard = async (text: string, setCopiedState: (v: boolean) => void) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedState(true);
      setTimeout(() => setCopiedState(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  // Local colored JSON rendering logic
  const renderHighlightedJSON = (jsonObj: any) => {
    const str = JSON.stringify(jsonObj, null, 2);
    return str.split('\n').map((line, idx) => {
      const keyRegex = /^(\s*)"([^"]+)":/;
      const matchKey = line.match(keyRegex);
      if (matchKey) {
        const indent = matchKey[1];
        const key = matchKey[2];
        const rest = line.substring(matchKey[0].length);
        return (
          <div key={idx} className="leading-relaxed select-text">
            <span className="text-neutral-600 font-mono">{indent}</span>
            <span className="text-indigo-400 font-mono font-semibold">"{key}"</span>:
            {renderJSONValue(rest)}
          </div>
        );
      }
      return <div key={idx} className="leading-relaxed text-neutral-300 font-mono select-text">{line}</div>;
    });
  };

  const renderJSONValue = (valStr: string) => {
    const trimmed = valStr.trim();
    if (trimmed.startsWith('"')) {
        return <span className="text-emerald-400 font-mono"> {trimmed}</span>;
    }
    if (trimmed === 'true' || trimmed === 'false') {
        return <span className="text-amber-400 font-semibold font-mono"> {trimmed}</span>;
    }
    if (!isNaN(Number(trimmed.replace(/,$/, '')))) {
        return <span className="text-indigo-300 font-mono"> {trimmed}</span>;
    }
    return <span className="text-neutral-300 font-mono"> {valStr}</span>;
  };

  // Visual status configurations
  const pipelineStages = [
    { name: '1. Source Detection', key: 'detecting' },
    { name: '2. Parsing & Load', key: 'extracting' },
    { name: '3. Constraint Check', key: 'validating' },
    { name: '4. Normalization', key: 'normalizing' },
    { name: '5. Conflict Resolves', key: 'merging' },
    { name: '6. Confidence Calculation', key: 'assessing_confidence' },
    { name: '7. Schema Projection', key: 'projecting' },
    { name: '8. Explainable Lineage', key: 'explaining' }
  ];

  const getStageColor = (stageKey: PipelineStage) => {
    const order = [
      'idle', 'detecting', 'extracting', 'validating', 'normalizing', 
      'merging', 'assessing_confidence', 'projecting', 'explaining', 'completed'
    ];
    const currentIdx = order.indexOf(pipelineState);
    const targetIdx = order.indexOf(stageKey);

    if (pipelineState === 'failed') return 'border-rose-900 bg-rose-950/10 text-rose-500';
    if (pipelineState === 'completed') return 'border-emerald-500 bg-emerald-950/10 text-emerald-400';
    if (currentIdx > targetIdx) return 'border-indigo-500 bg-indigo-950/20 text-indigo-400';
    if (currentIdx === targetIdx) return 'border-indigo-400 bg-indigo-950/30 text-indigo-300 animate-pulse';
    return 'border-neutral-850 bg-neutral-950/40 text-neutral-600';
  };

  const configWarnings = getConfigurationWarnings();

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-8 px-4 sm:px-6">
        
        {/* Title Block */}
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100 bg-gradient-to-r from-neutral-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
            Talent Ingestion Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-neutral-400 max-w-3xl leading-relaxed">
            Deterministic multi-source candidate canonicalization resolver. Ingests resumes, JSON profiles, spreadsheets, and recruiter summaries. Overlapping identities resolved field-by-field.
          </p>
        </div>

        {/* 8-Stage Progress Trace Tracker */}
        {pipelineState !== 'idle' && (
          <div 
            role="status"
            aria-live="polite"
            className="border border-neutral-850 bg-neutral-950/80 rounded-2xl p-5 shadow-2xl backdrop-blur-xl"
          >
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-4">
              Consolidated Pipeline Trace Flow
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-8 gap-3">
              {pipelineStages.map((stage) => {
                const stageIndex = pipelineStages.findIndex(s => s.key === stage.key);
                const currentOrder = [
                  'idle', 'detecting', 'extracting', 'validating', 'normalizing', 
                  'merging', 'assessing_confidence', 'projecting', 'explaining', 'completed'
                ];
                const activeIndex = currentOrder.indexOf(pipelineState);
                const isPassed = activeIndex > stageIndex + 1 || pipelineState === 'completed';
                
                return (
                  <div
                    key={stage.key}
                    className={`border rounded-xl p-3 text-[11px] font-semibold flex flex-col justify-between h-20 transition-all duration-300 select-none ${getStageColor(stage.key as PipelineStage)}`}
                  >
                    <span className="leading-tight">{stage.name}</span>
                    <div className="flex justify-end w-full">
                      {isPassed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : pipelineState === 'failed' ? (
                        <AlertTriangle className="w-4 h-4 text-rose-500" />
                      ) : pipelineState === stage.key ? (
                        <RefreshCw className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                      ) : (
                        <div className="w-2 h-2 rounded-full bg-neutral-800" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Block: upload triggers, actions, logs */}
          <div className="lg:col-span-4 space-y-6">
            <Card title="Ingestion Sources" description="Upload heterogeneous candidate files to run resolution.">
              <UploadZone 
                onFilesSelected={handleFilesSelected} 
                files={files} 
                onRemoveFile={handleRemoveFile} 
              />
              
              <div className="mt-4 p-3 rounded-xl border border-neutral-850 bg-neutral-950/40 space-y-2">
                <label className="flex items-start space-x-3 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={enableAIEnrichment}
                    onChange={(e) => setEnableAIEnrichment(e.target.checked)}
                    className="w-4 h-4 mt-0.5 rounded border-neutral-800 bg-neutral-900 text-indigo-600 focus:ring-indigo-500 focus:outline-none"
                  />
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-neutral-200">Enable AI Semantic Enrichment</span>
                    <p className="text-[10px] text-neutral-450 leading-relaxed font-sans">
                      Generate an AI-powered candidate summary and recruiter insights using Gemini 2.5 Flash. These insights are informational only and never modify canonical candidate data.
                    </p>
                  </div>
                </label>
              </div>

              <button
                type="button"
                disabled={files.length === 0 || ['detecting', 'extracting', 'validating', 'normalizing', 'merging', 'assessing_confidence', 'projecting', 'explaining'].includes(pipelineState)}
                onClick={handleRunPipeline}
                aria-label="Execute candidate canonicalization pipeline"
                className="w-full mt-5 px-4 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none focus:ring-offset-2 focus:ring-offset-neutral-950 disabled:bg-neutral-900 disabled:text-neutral-600 disabled:border disabled:border-neutral-850/60 disabled:cursor-not-allowed text-xs font-bold text-neutral-100 flex items-center justify-center space-x-2 transition-all duration-150 shadow-lg shadow-indigo-600/10"
              >
                <Activity className="w-4 h-4 animate-pulse" />
                <span>Run Ingestion Pipeline</span>
              </button>
            </Card>

            {/* Run logs warning output */}
            {pipelineResult && (
              <Card title="Extraction Report" description={`Trace Job ID: ${pipelineResult.job_id}`}>
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-neutral-850 pb-3">
                    <span className="text-xs text-neutral-450">Execution Status</span>
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md uppercase ${
                      pipelineResult.status === 'COMPLETED' 
                        ? 'bg-emerald-500/15 text-emerald-450 border border-emerald-500/20' 
                        : 'bg-rose-500/15 text-rose-450 border border-rose-500/20'
                    }`}>
                      {pipelineResult.status}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wide">Processed Documents</p>
                    <div className="space-y-1">
                      {pipelineResult.processed_sources.map((src, i) => (
                        <div key={src+i} className="flex items-center space-x-2 text-xs text-neutral-300">
                          <FileText className="w-3.5 h-3.5 text-neutral-555" />
                          <span className="truncate max-w-[200px]">{src}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {pipelineResult.errors.length > 0 && (
                    <div className="space-y-2 border-t border-neutral-850 pt-3">
                      <p className="text-[10px] font-bold text-neutral-450 uppercase tracking-wide flex items-center">
                        <AlertTriangle className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
                        Warnings & Errors
                      </p>
                      <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                        {pipelineResult.errors.map((err, idx) => (
                          <div 
                            key={idx} 
                            className={`p-2.5 rounded-xl border text-[11px] leading-relaxed ${
                              err.critical 
                                ? 'bg-rose-950/15 border-rose-900/30 text-rose-350' 
                                : 'bg-amber-950/15 border-amber-900/30 text-amber-350'
                            }`}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span>{err.field ? `[Field: ${err.field}]` : `[Source: ${err.source}]`}</span>
                              <span className="font-mono text-[9px] uppercase px-1 rounded bg-neutral-900">{err.error_type}</span>
                            </div>
                            <p className="text-neutral-400 mt-1">{err.message}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>

          {/* Right Block: profiles view tabs, download group */}
          <div className="lg:col-span-8">
            {['detecting', 'extracting', 'validating', 'normalizing', 'merging', 'assessing_confidence', 'projecting', 'explaining'].includes(pipelineState) ? (
              <Card className="py-20">
                <Loading />
              </Card>
            ) : canonicalCandidate ? (
              <div className="space-y-6">
                
                {/* Visual tabs controls */}
                <div className="flex border-b border-neutral-850 space-x-6">
                  <button
                    onClick={() => setActiveTab('profile')}
                    className={`pb-3.5 text-xs sm:text-sm font-semibold border-b-2 transition-all focus:outline-none ${
                      activeTab === 'profile' 
                        ? 'border-indigo-500 text-indigo-400' 
                        : 'border-transparent text-neutral-405 hover:text-neutral-200'
                    }`}
                  >
                    Canonical Profile Card
                  </button>
                  <button
                    onClick={() => setActiveTab('ai-insights')}
                    className={`pb-3.5 text-xs sm:text-sm font-semibold border-b-2 transition-all focus:outline-none ${
                      activeTab === 'ai-insights' 
                        ? 'border-indigo-500 text-indigo-400' 
                        : 'border-transparent text-neutral-405 hover:text-neutral-200'
                    }`}
                  >
                    AI Insights
                  </button>
                  <button
                    onClick={() => setActiveTab('projection')}
                    className={`pb-3.5 text-xs sm:text-sm font-semibold border-b-2 transition-all focus:outline-none ${
                      activeTab === 'projection' 
                        ? 'border-indigo-500 text-indigo-400' 
                        : 'border-transparent text-neutral-405 hover:text-neutral-200'
                    }`}
                  >
                    Custom Export Projection
                  </button>
                </div>

                {activeTab === 'profile' ? (
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                    
                    {/* Primary attribute displays */}
                    <div className="md:col-span-7 space-y-6">
                      
                      {/* Candidate identity summary block */}
                      <Card className="bg-gradient-to-br from-neutral-900/40 via-neutral-950/80 to-neutral-950 border border-neutral-850 shadow-2xl relative overflow-hidden">
                        <div className="flex items-start justify-between relative z-10">
                          <div>
                            <span className="text-[9px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold mb-2.5 inline-block">
                              Immutable Master Profile
                            </span>
                            <h2 className="text-2xl font-bold text-neutral-100 tracking-tight">
                              {canonicalCandidate.full_name}
                            </h2>
                            {canonicalCandidate.headline && (
                              <p className="text-xs text-neutral-400 mt-1.5 italic font-sans leading-relaxed">
                                "{canonicalCandidate.headline}"
                              </p>
                            )}
                            <p className="text-[10px] text-neutral-450 mt-1.5 font-mono">
                              Resolved ID: {canonicalCandidate.candidate_id}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="block text-[10px] font-semibold text-neutral-450">Overall Confidence</span>
                            <span className="text-2xl font-extrabold text-indigo-400 tracking-tight">
                              {(canonicalCandidate.overall_confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>

                        {/* Render Candidate Links */}
                        {(canonicalCandidate.links?.linkedin || canonicalCandidate.links?.github || canonicalCandidate.links?.portfolio) && (
                          <div className="border-t border-neutral-850 mt-4 pt-3 flex space-x-4 text-[10px] text-neutral-400 select-none">
                            {canonicalCandidate.links.linkedin && (
                              <a href={canonicalCandidate.links.linkedin} target="_blank" rel="noreferrer" className="hover:text-indigo-400 underline">LinkedIn</a>
                            )}
                            {canonicalCandidate.links.github && (
                              <a href={canonicalCandidate.links.github} target="_blank" rel="noreferrer" className="hover:text-indigo-400 underline">GitHub</a>
                            )}
                            {canonicalCandidate.links.portfolio && (
                              <a href={canonicalCandidate.links.portfolio} target="_blank" rel="noreferrer" className="hover:text-indigo-400 underline">Portfolio</a>
                            )}
                          </div>
                        )}
                      </Card>

                      {/* Exporters and downloads group */}
                      <Card title="Export Candidate Files" description="Export Master Profile structure and reports.">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                          <button
                            type="button"
                            onClick={downloadCanonical}
                            className="p-2.5 rounded-xl border border-neutral-850 hover:border-neutral-800 bg-neutral-950 hover:bg-neutral-900/30 text-[10px] font-bold text-neutral-200 flex flex-col items-center justify-center space-y-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all"
                          >
                            <FileCode className="w-4 h-4 text-indigo-400" />
                            <span>Canonical Profile</span>
                          </button>
                          
                          <button
                            type="button"
                            disabled={!projectedOutput}
                            onClick={downloadProjected}
                            className="p-2.5 rounded-xl border border-neutral-850 hover:border-neutral-800 bg-neutral-950 hover:bg-neutral-900/30 text-[10px] font-bold text-neutral-200 flex flex-col items-center justify-center space-y-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                          >
                            <Sliders className="w-4 h-4 text-indigo-400" />
                            <span>Projected JSON</span>
                          </button>

                          <button
                            type="button"
                            onClick={downloadExplainability}
                            className="p-2.5 rounded-xl border border-neutral-850 hover:border-neutral-800 bg-neutral-950 hover:bg-neutral-900/30 text-[10px] font-bold text-neutral-200 flex flex-col items-center justify-center space-y-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all"
                          >
                            <Info className="w-4 h-4 text-indigo-400" />
                            <span>Lineage Report</span>
                          </button>

                          <button
                            type="button"
                            disabled={!canonicalCandidate.ai_semantic_summary}
                            onClick={downloadSemanticSummary}
                            className="p-2.5 rounded-xl border border-neutral-850 hover:border-neutral-800 bg-neutral-950 hover:bg-neutral-900/30 text-[10px] font-bold text-neutral-200 flex flex-col items-center justify-center space-y-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                          >
                            <Sparkle className="w-4 h-4 text-indigo-400" />
                            <span>Semantic Notes</span>
                          </button>
                        </div>
                      </Card>

                      {/* Display Profile Attributes */}
                      <Card title="Canonical Master Attributes" description="Click any field card to display its source data resolution lineage.">
                        <div className="space-y-3">
                          {[
                            { label: 'Full Name', key: 'full_name', value: canonicalCandidate.full_name },
                            { label: 'Location', key: 'location', value: canonicalCandidate.location ? `${canonicalCandidate.location.city || ''} ${canonicalCandidate.location.region || ''} ${canonicalCandidate.location.country || ''}`.trim().replace(/\s+/g, ', ') : '' },
                            { label: 'Emails', key: 'emails', value: canonicalCandidate.emails?.join(', ') || '' },
                            { label: 'Phone Numbers', key: 'phones', value: canonicalCandidate.phones?.join(', ') || '' },
                          ].map((item) => {
                            if (!item.value) return null;
                            const isSelected = selectedFieldKey === item.key;
                            const fieldProvenance = canonicalCandidate.provenance?.find(p => p.field === item.key);
                            const selectedSource = fieldProvenance ? fieldProvenance.selected_source : 'System';
                            const score = fieldProvenance ? fieldProvenance.confidence : 1.0;
                            
                            return (
                              <button
                                type="button"
                                key={item.key}
                                onClick={() => setSelectedFieldKey(item.key)}
                                className={`w-full text-left p-3 rounded-xl border transition flex items-center justify-between focus:ring-2 focus:ring-indigo-500 focus:outline-none ${
                                  isSelected 
                                    ? 'border-indigo-500 bg-indigo-500/5 shadow-md' 
                                    : 'border-neutral-850 hover:border-neutral-800 hover:bg-neutral-900/20'
                                }`}
                              >
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold text-neutral-550 uppercase tracking-wide">{item.label}</span>
                                  <p className="text-xs font-semibold text-neutral-200">
                                    {item.value}
                                  </p>
                                </div>
                                <div className="flex items-center space-x-3.5">
                                  <div className="text-right">
                                    <span className="inline-block text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-indigo-950/20 text-indigo-400 border border-indigo-900/30">
                                      {selectedSource.replace(/^frag-/, '')}
                                    </span>
                                    <span className="block text-[10px] text-neutral-450 mt-0.5">
                                      Confidence: {(score * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <ChevronRight className={`w-4 h-4 transition ${isSelected ? 'text-indigo-400 transform translate-x-0.5' : 'text-neutral-600'}`} />
                                </div>
                              </button>
                            );
                          })}

                          {/* Render skills separately */}
                          {canonicalCandidate.skills && canonicalCandidate.skills.length > 0 && (
                            <div className="p-3 border border-neutral-850 rounded-xl bg-neutral-950/20 space-y-1.5">
                              <span className="text-[10px] font-bold text-neutral-550 uppercase tracking-wide">Skills Inventory</span>
                              <div className="flex flex-wrap gap-1.5">
                                {canonicalCandidate.skills.map((s, idx) => (
                                  <span 
                                    key={idx} 
                                    className="text-[10px] bg-neutral-900 border border-neutral-850 px-2.5 py-1 rounded-md text-neutral-300 font-semibold flex items-center space-x-1.5 cursor-help" 
                                    title={`Sources: ${s.sources.join(', ')} (Confidence: ${(s.confidence * 100).toFixed(0)}%)`}
                                  >
                                    <span>{s.name}</span>
                                    <span className="text-[8px] text-indigo-400 font-normal">{(s.confidence * 100).toFixed(0)}%</span>
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </Card>

                      {/* Display Education & Experience timelines */}
                      {canonicalCandidate.experience && canonicalCandidate.experience.length > 0 && (
                        <Card title="Deduplicated Work Experience" description="Resolved jobs timelines.">
                          <div className="space-y-3">
                            {canonicalCandidate.experience.map((job: any, i: number) => (
                              <div key={i} className="p-3 border border-neutral-855 rounded-xl flex justify-between items-start text-xs bg-neutral-950/30">
                                <div className="space-y-1">
                                  <p className="font-bold text-neutral-205">{job.company}</p>
                                  <p className="text-neutral-400">{job.title}</p>
                                  {job.summary && <p className="text-[10px] text-neutral-500 mt-1 leading-relaxed font-sans">{job.summary}</p>}
                                </div>
                                <span className="text-neutral-500 font-mono text-[10px]">{job.start} - {job.end || 'Present'}</span>
                              </div>
                            ))}
                          </div>
                        </Card>
                      )}

                      {canonicalCandidate.education && canonicalCandidate.education.length > 0 && (
                        <Card title="Deduplicated Education Records" description="Resolved degree timelines.">
                          <div className="space-y-3">
                            {canonicalCandidate.education.map((edu: any, i: number) => (
                              <div key={i} className="p-3 border border-neutral-855 rounded-xl flex justify-between items-start text-xs bg-neutral-950/30">
                                <div className="space-y-1">
                                  <p className="font-bold text-neutral-205">{edu.institution}</p>
                                  <p className="text-neutral-400">{edu.degree} {edu.field ? `in ${edu.field}` : ''}</p>
                                </div>
                                {edu.end_year && <span className="text-neutral-500 font-mono text-[10px]">Graduated: {edu.end_year}</span>}
                              </div>
                            ))}
                          </div>
                        </Card>
                      )}

                    </div>

                    {/* Right Lineage Drawer card */}
                    <div className="md:col-span-5 space-y-6 sticky top-24">
                      {selectedFieldKey ? (() => {
                        const selectedProvenance = canonicalCandidate.provenance?.find(p => p.field === selectedFieldKey);
                        if (!selectedProvenance) return (
                          <div className="p-4 border border-dashed border-neutral-850 rounded-2xl text-center text-xs text-neutral-500">
                            No explainability trace found for this field.
                          </div>
                        );
                        
                        return (
                          <Card 
                            title="Field Lineage Audit" 
                            description={`Explainability trace for attribute: ${selectedFieldKey}`}
                            className="border border-indigo-500/20 shadow-indigo-950/10 shadow-2xl bg-neutral-950"
                          >
                            <div className="space-y-5">
                              {/* Selection Reason */}
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold text-neutral-550 uppercase tracking-wider block">Winner Selection Reason</span>
                                <div className="p-3 rounded-xl bg-indigo-950/15 border border-indigo-900/20 text-xs text-indigo-300 leading-relaxed font-medium">
                                  {selectedProvenance.reason || 'Resolved via default config priority rules.'}
                                </div>
                              </div>

                              {/* Target Details */}
                              <div className="grid grid-cols-2 gap-4 text-xs">
                                <div>
                                  <span className="text-neutral-550 block">Winning Source</span>
                                  <span className="font-bold text-neutral-200 mt-0.5 block truncate" title={selectedProvenance.selected_source}>
                                    {selectedProvenance.selected_source.replace(/^frag-/, '')}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-neutral-550 block">Confidence Score</span>
                                  <span className="font-bold text-indigo-400 text-lg mt-0.5 block">
                                    {(selectedProvenance.confidence * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>

                              {/* Simplified Trace Callout */}
                              <div className="p-3 rounded-xl bg-neutral-900/30 border border-neutral-850 text-[10px] text-neutral-450 leading-relaxed">
                                <span className="font-bold text-neutral-350 block mb-1">⚖️ Authority Resolution Policy</span>
                                CandidateCore consolidated this value using source-priority consensus. Dynamic audits trace matches directly to the immutable record source.
                              </div>

                            </div>
                          </Card>
                        );
                      })() : (
                        <div className="h-64 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                          <Info className="w-6 h-6 text-neutral-600 mb-2" />
                          <h4 className="text-xs font-semibold text-neutral-400">Select Attribute for Lineage</h4>
                          <p className="text-[10px] text-neutral-550 max-w-xs mt-1 leading-normal">
                            Click any canonical attribute card on the left to inspect its extraction lineage, confidence weights, and tie-breakers.
                          </p>
                        </div>
                      )}
                    </div>

                  </div>
                ) : activeTab === 'ai-insights' ? (
                  <div className="space-y-6">
                    {canonicalCandidate?.ai_semantic_summary ? (() => {
                      const se = canonicalCandidate.ai_semantic_summary;
                      return (
                        <div className="space-y-6">
                          
                          {/* Banner & Disclaimer */}
                          <div className="p-4 rounded-2xl bg-indigo-950/15 border border-indigo-900/30 flex items-start space-x-3">
                            <ShieldAlert className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5 animate-pulse" />
                            <div className="space-y-1">
                              <span className="text-xs font-bold text-indigo-300 uppercase tracking-widest flex items-center">
                                <Sparkles className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
                                AI Generated Insights Layer
                              </span>
                              <p className="text-xs text-neutral-400 leading-relaxed font-sans">
                                These insights are generated by Gemini 2.5 Flash for recruiter assistance and are not part of the canonical candidate profile. Deterministic canonical records remain immutable.
                              </p>
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            
                            {/* Professional Summary */}
                            <Card title="Professional Summary" description="Overview of the candidate's career.">
                              <p className="text-xs text-neutral-300 leading-relaxed font-medium font-sans">
                                {se.professional_summary || "No professional summary generated."}
                              </p>
                            </Card>

                            {/* Recruiter Insights */}
                            <Card title="Recruiter Insights" description="Synthesis suggestions for matching.">
                              <ul className="list-disc pl-4 space-y-1.5 text-xs text-indigo-300 bg-indigo-950/5 border border-indigo-900/10 p-3.5 rounded-xl leading-relaxed italic font-sans">
                                {se.recruiter_insights?.map((ins: string, idx: number) => (
                                  <li key={idx}>"{ins}"</li>
                                )) || <li>No recruiter insights generated.</li>}
                              </ul>
                            </Card>

                            {/* Core Strengths & Recommended Roles */}
                            <Card title="Strengths & Recommended Roles" description="Inferred focus and functions.">
                              <div className="space-y-4">
                                <div className="space-y-2">
                                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">Core Strengths</span>
                                  <div className="flex flex-wrap gap-1.5">
                                    {se.core_strengths?.map((s: string, idx: number) => (
                                      <span key={idx} className="text-[10px] bg-neutral-900 border border-neutral-850 text-neutral-355 px-2.5 py-1 rounded-md font-semibold font-sans">
                                        {s}
                                      </span>
                                    )) || "N/A"}
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <span className="text-[10px] font-bold text-neutral-555 uppercase tracking-wider block">Recommended Roles</span>
                                  <div className="flex flex-wrap gap-1.5">
                                    {se.recommended_roles?.map((r: string, idx: number) => (
                                      <span key={idx} className="text-[10px] bg-indigo-950/20 border border-indigo-900/30 text-indigo-355 px-2.5 py-1 rounded-md font-bold font-sans">
                                        {r}
                                      </span>
                                    )) || "N/A"}
                                  </div>
                                </div>
                              </div>
                            </Card>

                            {/* Technical Highlights */}
                            <Card title="Technical Highlights" description="Milestones and code accomplishments.">
                              <ul className="list-disc pl-4 space-y-1.5 text-xs text-neutral-350 leading-relaxed font-sans">
                                {se.technical_highlights?.map((th: string, idx: number) => (
                                  <li key={idx}>{th}</li>
                                )) || <li>N/A</li>}
                              </ul>
                            </Card>

                            {/* Leadership & Communication Signals */}
                            <Card title="Behavioral & Professional Signals" description="Initiative highlights and collaboration styles.">
                              <div className="space-y-4">
                                <div className="space-y-2">
                                  <span className="text-[10px] font-bold text-neutral-550 uppercase tracking-wider block">Leadership Signals</span>
                                  <ul className="list-disc pl-4 space-y-1.5 text-xs text-neutral-350 leading-relaxed font-sans">
                                    {se.leadership_signals?.map((ls: string, idx: number) => (
                                      <li key={idx}>{ls}</li>
                                    )) || <li>N/A</li>}
                                  </ul>
                                </div>
                                <div className="space-y-2 pt-2 border-t border-neutral-850/50">
                                  <span className="text-[10px] font-bold text-neutral-550 uppercase tracking-wider block">Communication Signals</span>
                                  <ul className="list-disc pl-4 space-y-1.5 text-xs text-neutral-350 leading-relaxed font-sans">
                                    {se.communication_signals?.map((cs: string, idx: number) => (
                                      <li key={idx}>{cs}</li>
                                    )) || <li>N/A</li>}
                                  </ul>
                                </div>
                              </div>
                            </Card>

                            {/* Interview Focus & Potential Concerns */}
                            <Card title="Evaluation Advisories" description="Key discussion topics and gap flags.">
                              <div className="space-y-4">
                                <div className="space-y-2">
                                  <span className="text-[10px] font-bold text-amber-500/80 uppercase tracking-wider block">Interview Focus Areas</span>
                                  <ul className="list-disc pl-4 space-y-1.5 text-xs text-neutral-350 leading-relaxed font-sans">
                                    {se.interview_focus?.map((fa: string, idx: number) => (
                                      <li key={idx}>{fa}</li>
                                    )) || <li>N/A</li>}
                                  </ul>
                                </div>
                                <div className="space-y-2 pt-2 border-t border-neutral-850/50">
                                  <span className="text-[10px] font-bold text-rose-500/80 uppercase tracking-wider block">Potential Concerns</span>
                                  <ul className="list-disc pl-4 space-y-1.5 text-xs text-neutral-350 leading-relaxed font-sans">
                                    {se.potential_concerns?.map((pc: string, idx: number) => (
                                      <li key={idx}>{pc}</li>
                                    )) || <li>N/A</li>}
                                  </ul>
                                </div>
                              </div>
                            </Card>

                          </div>
                        </div>
                      );
                    })() : (
                      <div className="h-96 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                        <Sparkles className="w-8 h-8 text-neutral-600 mb-3" />
                        <h4 className="text-sm font-semibold text-neutral-455">AI Semantic Insights Disabled</h4>
                        <p className="text-xs text-neutral-550 max-w-sm mt-1 leading-relaxed font-sans">
                          To view high-level recruiter insights, check the "Enable AI Semantic Enrichment" option in Ingestion Sources before running the pipeline.
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-6">
                    
                    {/* Side-by-side Configuration Form & Projected Viewer */}
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                      
                      {/* Configuration inputs */}
                      <div className="md:col-span-6 space-y-6">
                        <Card title="Schema Custom Projection" description="Apply custom renaming, mappings, and validation checks before export.">
                          <div className="space-y-5">
                            
                            {/* Render validation warning blocks */}
                            {configWarnings.length > 0 && (
                              <div className="p-3.5 rounded-xl bg-amber-950/10 border border-amber-900/30 text-xs text-amber-300 space-y-1.5">
                                <div className="flex items-center space-x-1.5 font-bold uppercase tracking-wider text-[10px]">
                                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                                  <span>Pre-execution warnings</span>
                                </div>
                                <ul className="list-disc pl-4 space-y-1 leading-relaxed">
                                  {configWarnings.map((warn, i) => (
                                    <li key={i}>{warn}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            <div>
                              <label className="text-xs font-bold text-neutral-455 block mb-2 uppercase">Field Whitelist Selection</label>
                              <div className="flex flex-wrap gap-2">
                                {['full_name', 'emails', 'phones', 'location', 'skills', 'experience', 'education', 'links', 'headline'].map((f) => (
                                  <button
                                    type="button"
                                    key={f}
                                    onClick={() => {
                                      setSelectedFields(prev => 
                                        prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                      );
                                    }}
                                    className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition focus:ring-2 focus:ring-indigo-500 focus:outline-none ${
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
                              <label className="text-xs font-bold text-neutral-455 block mb-2 uppercase">Omit Fields (Exclusion list)</label>
                              <div className="flex flex-wrap gap-2">
                                {['full_name', 'emails', 'phones', 'location', 'skills', 'experience', 'education', 'links', 'headline'].map((f) => (
                                  <button
                                    type="button"
                                    key={f}
                                    onClick={() => {
                                      setExcludeFields(prev => 
                                        prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                      );
                                    }}
                                    className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition focus:ring-2 focus:ring-rose-500 focus:outline-none ${
                                      excludeFields.includes(f)
                                        ? 'bg-rose-955 border-rose-900/60 text-rose-350'
                                        : 'border-neutral-855 text-neutral-405 hover:border-neutral-800'
                                    }`}
                                  >
                                    {f}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div>
                              <label className="text-xs font-bold text-neutral-455 block mb-2 uppercase">Required Validation Constraints</label>
                              <div className="flex flex-wrap gap-2">
                                {['full_name', 'emails', 'phones', 'location', 'skills', 'experience', 'education', 'links', 'headline'].map((f) => (
                                  <button
                                    type="button"
                                    key={f}
                                    onClick={() => {
                                      setRequiredFields(prev => 
                                        prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                                      );
                                    }}
                                    className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg border transition focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                                      requiredFields.includes(f)
                                        ? 'bg-amber-955 border-amber-900/60 text-amber-350'
                                        : 'border-neutral-855 text-neutral-405 hover:border-neutral-800'
                                    }`}
                                  >
                                    {f}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div>
                              <label className="text-xs font-bold text-neutral-455 block mb-2 uppercase">Nested Mappings (Rename Targets)</label>
                              <div className="space-y-2.5 text-xs font-mono">
                                <div className="flex items-center space-x-3">
                                  <span className="text-neutral-455 w-24">full_name</span>
                                  <ArrowRight className="w-3.5 h-3.5 text-neutral-700" />
                                  <input
                                    type="text"
                                    aria-label="Rename map target for full_name"
                                    value={renames.full_name || ''}
                                    onChange={(e) => setRenames(prev => ({ ...prev, full_name: e.target.value }))}
                                    className="bg-neutral-900 border border-neutral-850 rounded-lg px-2.5 py-1.5 text-neutral-200 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 flex-1 font-mono"
                                  />
                                </div>
                                <div className="flex items-center space-x-3">
                                  <span className="text-neutral-455 w-24">location</span>
                                  <ArrowRight className="w-3.5 h-3.5 text-neutral-700" />
                                  <input
                                    type="text"
                                    aria-label="Rename map target for location"
                                    value={renames.location || ''}
                                    onChange={(e) => setRenames(prev => ({ ...prev, location: e.target.value }))}
                                    className="bg-neutral-900 border border-neutral-850 rounded-lg px-2.5 py-1.5 text-neutral-200 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 flex-1 font-mono"
                                  />
                                </div>
                              </div>
                            </div>

                            <button
                              type="button"
                              onClick={handleProjectCandidate}
                              disabled={projecting || configWarnings.length > 0}
                              className="w-full mt-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:bg-neutral-900 disabled:text-neutral-600 disabled:border disabled:border-neutral-850/60 disabled:cursor-not-allowed text-xs font-bold text-neutral-100 transition duration-150 shadow-md shadow-indigo-600/10"
                            >
                              {projecting ? 'Generating target mappings...' : 'Execute Export Projection'}
                            </button>
                          </div>
                        </Card>
                      </div>

                      {/* Syntax Highlighted JSON Previewer with Copy & Download */}
                      <div className="md:col-span-6 space-y-6">
                        {projectedOutput ? (
                          <Card 
                            title="Projected Output Schema" 
                            description="Exported record structure mapped to configured target rules."
                          >
                            <div className="flex items-center justify-between border-b border-neutral-850 pb-3 mb-3.5">
                              <span className="text-xs text-emerald-450 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded flex items-center">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                Output Validated
                              </span>
                              
                              <div className="flex items-center space-x-2">
                                <button
                                  type="button"
                                  onClick={() => copyToClipboard(JSON.stringify(projectedOutput, null, 2), setCopiedProjected)}
                                  className="p-1.5 rounded bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-neutral-250 border border-neutral-850 focus:ring-2 focus:ring-indigo-500 focus:outline-none flex items-center space-x-1"
                                  title="Copy projected JSON output"
                                >
                                  {copiedProjected ? (
                                    <>
                                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                                      <span className="text-[10px] text-emerald-400 font-bold">Copied</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="w-3.5 h-3.5" />
                                      <span className="text-[10px]">Copy</span>
                                    </>
                                  )}
                                </button>
                                
                                <button
                                  type="button"
                                  onClick={downloadProjected}
                                  className="p-1.5 rounded bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-neutral-250 border border-neutral-850 focus:ring-2 focus:ring-indigo-500 focus:outline-none flex items-center space-x-1"
                                  title="Download projected JSON file"
                                >
                                  <Download className="w-3.5 h-3.5" />
                                  <span className="text-[10px]">Download</span>
                                </button>
                              </div>
                            </div>

                            <div className="p-4 bg-neutral-950 border border-neutral-900 rounded-2xl overflow-x-auto text-[11px] max-h-[450px] shadow-inner select-all">
                              {renderHighlightedJSON(projectedOutput)}
                            </div>
                          </Card>
                        ) : (
                          <div className="h-96 border border-dashed border-neutral-800 rounded-2xl flex flex-col items-center justify-center text-center p-6 bg-neutral-950/20">
                            <Lock className="w-6 h-6 text-neutral-600 mb-2" />
                            <h4 className="text-xs font-semibold text-neutral-450">Awaiting Export Generation</h4>
                            <p className="text-[10px] text-neutral-500 max-w-xs mt-1 leading-normal">
                              Configure renaming targets and whitelist options in the left configuration console, then execute projection to inspect structural outputs.
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
                <h4 className="text-sm font-semibold text-neutral-400">Awaiting Ingestion Run</h4>
                <p className="text-xs text-neutral-500 max-w-xs mt-1 leading-relaxed">
                  Ingest source documents and trigger the pipeline. Resolved attributes with audit details will display here.
                </p>
              </div>
            )}
          </div>

        </div>

      </div>
    </Layout>
  );
}
