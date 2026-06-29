'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  files: File[];
  onRemoveFile: (index: number) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFilesSelected,
  files,
  onRemoveFile,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = Array.from(e.dataTransfer.files);
      onFilesSelected(selected);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = Array.from(e.target.files);
      onFilesSelected(selected);
    }
  };

  const triggerInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-4">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={triggerInput}
        className={cn(
          "border border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300",
          dragActive
            ? "border-indigo-500 bg-indigo-500/5 shadow-indigo-500/10 shadow-lg"
            : "border-neutral-800 bg-neutral-900/10 hover:border-neutral-700 hover:bg-neutral-900/20"
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileInputChange}
          className="hidden"
          accept=".csv,.json,.pdf,.txt"
        />
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center">
            <UploadCloud className="w-6 h-6 text-indigo-400 animate-pulse" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-semibold text-neutral-200">
              Drag & drop source files here
            </p>
            <p className="text-xs text-neutral-500">
              Supports CSV, JSON, PDF, or TXT notes
            </p>
          </div>
        </div>
      </div>

      {files.length > 0 && (
        <div className="border border-neutral-800 rounded-2xl bg-neutral-950/40 p-4 space-y-2">
          <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-2">
            Selected Ingest Targets ({files.length})
          </p>
          <div className="space-y-1.5">
            {files.map((file, idx) => (
              <div
                key={file.name + idx}
                className="flex items-center justify-between p-2 rounded-xl border border-neutral-900 bg-neutral-900/20 hover:border-neutral-800"
              >
                <div className="flex items-center space-x-3">
                  <File className="w-4 h-4 text-neutral-400" />
                  <div className="space-y-0.5">
                    <p className="text-xs font-medium text-neutral-300 truncate max-w-[200px]">
                      {file.name}
                    </p>
                    <p className="text-[10px] text-neutral-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFile(idx);
                  }}
                  className="p-1 rounded-lg hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
export default UploadZone;
