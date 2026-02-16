'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Sparkles } from 'lucide-react';
import type { Artifact } from '@/hooks/useChat';
import { PatientCard } from './PatientCard';
import { LabResultsCard } from './LabResultsCard';
import { MedicationCard } from './MedicationCard';
import { ConditionCard } from './ConditionCard';
import { ProcedureCard } from './ProcedureCard';
import { FindingsCard } from './FindingsCard';
import { ActionsCard } from './ActionsCard';
import { SourceViewer } from './SourceViewer';
import { ReasoningPanel } from './ReasoningPanel';
import { FinalAnswerCard } from './FinalAnswerCard';

export interface ArtifactPanelProps {
  artifacts: Artifact[];
  reasoning?: string;
  taskId?: string;
  finalAnswer?: string | null;
  className?: string;
}

interface FHIRResource {
  resourceType: string;
  [key: string]: unknown;
}

function isFHIRResource(data: unknown): data is FHIRResource {
  return (
    typeof data === 'object' &&
    data !== null &&
    'resourceType' in data &&
    typeof (data as FHIRResource).resourceType === 'string'
  );
}

function renderArtifactContent(artifact: Artifact) {
  const data = artifact.data;

  // Check if it's a FHIR resource
  if (isFHIRResource(data)) {
    switch (data.resourceType) {
      case 'Patient':
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return <PatientCard data={data as any} />;
      case 'Observation':
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return <LabResultsCard data={data as any} />;
      case 'MedicationRequest':
      case 'MedicationStatement':
      case 'Medication':
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return <MedicationCard data={data as any} />;
      case 'Condition':
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return <ConditionCard data={data as any} />;
      case 'Procedure':
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return <ProcedureCard data={data as any} />;
      case 'Bundle':
        // Handle Bundle by rendering its entries
        return renderBundle(data);
      default:
        // Unknown FHIR resource type - show source viewer
        return <SourceViewer data={data} title={`FHIR ${data.resourceType}`} />;
    }
  }

  // Check for summary/findings/actions structure
  if (typeof data === 'object' && data !== null) {
    const dataObj = data as Record<string, unknown>;

    if ('findings' in dataObj && Array.isArray(dataObj.findings)) {
      return <FindingsCard findings={dataObj.findings} />;
    }

    if ('actions' in dataObj && Array.isArray(dataObj.actions)) {
      return <ActionsCard actions={dataObj.actions} />;
    }
  }

  // Fallback to source viewer
  return <SourceViewer data={data} title={artifact.type} />;
}

function renderBundle(bundle: FHIRResource) {
  const entries = bundle.entry as Array<{ resource: FHIRResource }> | undefined;

  if (!entries || entries.length === 0) {
    return <SourceViewer data={bundle} title="Empty Bundle" />;
  }

  return (
    <div className="space-y-3">
      {entries.map((entry, index) => {
        if (!entry.resource) return null;
        return (
          <div key={index}>
            {renderArtifactContent({
              id: `bundle-entry-${index}`,
              type: entry.resource.resourceType,
              data: entry.resource,
              timestamp: Date.now(),
            })}
          </div>
        );
      })}
    </div>
  );
}

export function ArtifactPanel({
  artifacts,
  reasoning,
  taskId,
  finalAnswer,
  className
}: ArtifactPanelProps) {
  const [showSource, setShowSource] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

  if (artifacts.length === 0 && !reasoning && !finalAnswer) {
    return null;
  }

  return (
    <div
      className={cn(
        'bg-sara-bg-surface rounded-sara border border-sara-border',
        'animate-sara-fade-in',
        className
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-sara-border">
        <div className="flex items-center gap-2">
          <div className="sara-icon-box">
            <Sparkles className="w-[17px] h-[17px]" />
          </div>
          <h2 className="text-subheading text-sara-text-primary">
            Key Findings
          </h2>
        </div>
      </div>

      {/* Final Answer Card - shown prominently at top */}
      {finalAnswer && taskId && (
        <div className="p-4 border-b border-sara-border">
          <FinalAnswerCard taskId={taskId} answer={finalAnswer} />
        </div>
      )}

      {/* Artifacts Stack */}
      <div className="p-4 space-y-4">
        {artifacts.map((artifact) => (
          <div key={artifact.id} className="animate-sara-slide-up">
            {renderArtifactContent(artifact)}
          </div>
        ))}
      </div>

      {/* Collapsible Sections */}
      <div className="border-t border-sara-border">
        {/* Reasoning Section */}
        {reasoning && (
          <div className="border-b border-sara-border">
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className={cn(
                'w-full px-4 py-3 flex items-center gap-2',
                'text-body-small text-sara-text-secondary',
                'hover:bg-sara-bg-elevated transition-colors duration-150'
              )}
            >
              {showReasoning ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <span>Show Reasoning</span>
            </button>
            {showReasoning && (
              <div className="px-4 pb-4 animate-sara-fade-in">
                <ReasoningPanel reasoning={reasoning} />
              </div>
            )}
          </div>
        )}

        {/* Source Section */}
        {artifacts.length > 0 && (
          <div>
            <button
              onClick={() => setShowSource(!showSource)}
              className={cn(
                'w-full px-4 py-3 flex items-center gap-2',
                'text-body-small text-sara-text-secondary',
                'hover:bg-sara-bg-elevated transition-colors duration-150'
              )}
            >
              {showSource ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <span>View Raw Source</span>
            </button>
            {showSource && (
              <div className="px-4 pb-4 space-y-3 animate-sara-fade-in">
                {artifacts.map((artifact) => (
                  <SourceViewer
                    key={`source-${artifact.id}`}
                    data={artifact.data}
                    title={artifact.type}
                    defaultExpanded
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ArtifactPanel;
