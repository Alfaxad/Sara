'use client';

import { cn } from '@/lib/utils';
import { PatientCard } from '@/components/artifacts/PatientCard';
import { LabResultsCard } from '@/components/artifacts/LabResultsCard';
import { MedicationCard } from '@/components/artifacts/MedicationCard';
import { ConditionCard } from '@/components/artifacts/ConditionCard';
import { ProcedureCard } from '@/components/artifacts/ProcedureCard';
import {
  FileText,
  AlertCircle,
  ClipboardList,
  Activity,
  Calendar,
  Hash,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';

interface FhirResourceRendererProps {
  resource: unknown;
  className?: string;
}

// Generic FHIR resource card for unsupported types
function GenericResourceCard({ resource, className }: { resource: Record<string, unknown>; className?: string }) {
  const [showDetails, setShowDetails] = useState(false);
  const resourceType = resource.resourceType as string;
  const id = resource.id as string;
  const status = resource.status as string | undefined;

  // Extract meaningful fields based on resource type
  const getIcon = () => {
    switch (resourceType) {
      case 'ServiceRequest': return <ClipboardList className="w-5 h-5 text-sara-accent" />;
      case 'Encounter': return <Calendar className="w-5 h-5 text-sara-accent" />;
      case 'DiagnosticReport': return <FileText className="w-5 h-5 text-sara-accent" />;
      case 'AllergyIntolerance': return <AlertCircle className="w-5 h-5 text-sara-warning" />;
      case 'Immunization': return <Activity className="w-5 h-5 text-sara-success" />;
      default: return <FileText className="w-5 h-5 text-sara-accent" />;
    }
  };

  const getStatusColor = (s: string) => {
    if (['active', 'completed', 'final', 'registered'].includes(s)) return 'bg-green-500/20 text-green-400';
    if (['cancelled', 'entered-in-error', 'inactive'].includes(s)) return 'bg-red-500/20 text-red-400';
    if (['pending', 'draft', 'on-hold'].includes(s)) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-sara-accent/20 text-sara-accent';
  };

  // Extract common display text
  const getDisplayText = () => {
    // Try code.text, code.coding[0].display, or other common fields
    if (resource.code && typeof resource.code === 'object') {
      const code = resource.code as Record<string, unknown>;
      if (code.text) return code.text as string;
      if (code.coding && Array.isArray(code.coding) && code.coding.length > 0) {
        const coding = code.coding[0] as Record<string, unknown>;
        if (coding.display) return coding.display as string;
      }
    }
    if (resource.text && typeof resource.text === 'object') {
      const text = resource.text as Record<string, unknown>;
      if (text.div) return null; // Don't show HTML
    }
    return null;
  };

  const displayText = getDisplayText();

  return (
    <div className={cn(
      'rounded-sara bg-sara-bg-elevated border border-sara-border overflow-hidden',
      className
    )}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-sara-accent-soft flex items-center justify-center flex-shrink-0">
            {getIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-display text-body font-semibold text-sara-text-primary">
                {resourceType}
              </span>
              {status && (
                <span className={cn('px-2 py-0.5 rounded text-caption font-medium', getStatusColor(status))}>
                  {status}
                </span>
              )}
            </div>
            {displayText && (
              <p className="text-body-small text-sara-text-secondary mt-1 line-clamp-2">
                {displayText}
              </p>
            )}
            {id && (
              <div className="flex items-center gap-1 mt-2 text-caption text-sara-text-muted">
                <Hash className="w-3 h-3" />
                <span className="font-mono">{id}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Show details toggle */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={cn(
          'w-full px-4 py-2 flex items-center gap-2',
          'border-t border-sara-border',
          'text-caption text-sara-text-secondary',
          'hover:bg-sara-bg-subtle transition-colors'
        )}
      >
        {showDetails ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <span>{showDetails ? 'Hide' : 'Show'} raw data</span>
      </button>

      {showDetails && (
        <div className="px-4 pb-4 max-h-64 overflow-auto">
          <pre className="text-caption text-sara-text-muted font-mono whitespace-pre-wrap">
            {JSON.stringify(resource, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// Error card for failed requests
function ErrorCard({ error, className }: { error: Record<string, unknown>; className?: string }) {
  const [showDetails, setShowDetails] = useState(false);
  const errorMessage = (error.error as string) || 'Request failed';
  const statusCode = error.status_code as number | undefined;

  return (
    <div className={cn(
      'rounded-sara bg-sara-error/10 border border-sara-error/30 overflow-hidden',
      className
    )}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-sara-error/20 flex items-center justify-center flex-shrink-0">
            <AlertCircle className="w-5 h-5 text-sara-error" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="font-display text-body font-semibold text-sara-error">
              Request Failed
            </span>
            <p className="text-body-small text-sara-text-secondary mt-1">
              {errorMessage}
            </p>
            {statusCode !== undefined && (
              <span className="text-caption text-sara-text-muted mt-2 block">
                Status code: {statusCode}
              </span>
            )}
          </div>
        </div>
      </div>

      <button
        onClick={() => setShowDetails(!showDetails)}
        className={cn(
          'w-full px-4 py-2 flex items-center gap-2',
          'border-t border-sara-error/30',
          'text-caption text-sara-text-secondary',
          'hover:bg-sara-error/5 transition-colors'
        )}
      >
        {showDetails ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <span>{showDetails ? 'Hide' : 'Show'} details</span>
      </button>

      {showDetails && (
        <div className="px-4 pb-4 max-h-48 overflow-auto">
          <pre className="text-caption text-sara-text-muted font-mono whitespace-pre-wrap">
            {JSON.stringify(error, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// Bundle summary card
function BundleSummaryCard({ bundle, className }: { bundle: Record<string, unknown>; className?: string }) {
  const entries = (bundle.entry as Array<{ resource?: Record<string, unknown> }>) || [];
  const total = bundle.total as number | undefined;

  // Group entries by resource type
  const resourceCounts: Record<string, number> = {};
  entries.forEach(entry => {
    if (entry.resource?.resourceType) {
      const type = entry.resource.resourceType as string;
      resourceCounts[type] = (resourceCounts[type] || 0) + 1;
    }
  });

  if (entries.length === 0) {
    return (
      <div className={cn(
        'rounded-sara bg-sara-bg-elevated border border-sara-border p-4',
        className
      )}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-sara-bg-subtle flex items-center justify-center">
            <FileText className="w-5 h-5 text-sara-text-muted" />
          </div>
          <div>
            <span className="font-display text-body font-semibold text-sara-text-primary">
              Empty Bundle
            </span>
            <p className="text-body-small text-sara-text-muted">
              No resources found
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Bundle header */}
      <div className="flex items-center gap-2 text-caption text-sara-text-muted">
        <span className="font-medium">Bundle</span>
        <span>•</span>
        <span>{total ?? entries.length} {(total ?? entries.length) === 1 ? 'resource' : 'resources'}</span>
        {Object.keys(resourceCounts).length > 0 && (
          <>
            <span>•</span>
            <span>
              {Object.entries(resourceCounts).map(([type, count], idx) => (
                <span key={type}>
                  {idx > 0 && ', '}
                  {count} {type}
                </span>
              ))}
            </span>
          </>
        )}
      </div>

      {/* Render each entry */}
      {entries.slice(0, 10).map((entry, index) => (
        <div key={index}>
          {entry.resource ? (
            <FhirResourceRenderer resource={entry.resource} />
          ) : (
            <GenericResourceCard resource={entry as Record<string, unknown>} />
          )}
        </div>
      ))}

      {entries.length > 10 && (
        <div className="text-body-small text-sara-text-muted text-center py-2">
          ... and {entries.length - 10} more resources
        </div>
      )}
    </div>
  );
}

/**
 * Renders FHIR resources as beautiful semantic cards.
 * Uses specialized card components for known resource types,
 * with a generic card fallback for others.
 */
export function FhirResourceRenderer({ resource, className }: FhirResourceRendererProps) {
  if (!resource || typeof resource !== 'object') {
    return (
      <div className={cn('text-body-small text-sara-text-muted', className)}>
        <pre className="whitespace-pre-wrap">{JSON.stringify(resource, null, 2)}</pre>
      </div>
    );
  }

  const resourceObj = resource as Record<string, unknown>;
  const resourceType = resourceObj.resourceType as string | undefined;
  const isError = resourceObj.error || resourceObj.status_code === 0;

  // Handle error responses with a nice error card
  if (isError) {
    return <ErrorCard error={resourceObj} className={className} />;
  }

  // Render based on resource type
  switch (resourceType) {
    case 'Patient':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <PatientCard data={resourceObj as any} className={className} />;

    case 'Observation':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <LabResultsCard data={resourceObj as any} className={className} />;

    case 'MedicationRequest':
    case 'MedicationStatement':
    case 'Medication':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <MedicationCard data={resourceObj as any} className={className} />;

    case 'Condition':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <ConditionCard data={resourceObj as any} className={className} />;

    case 'Procedure':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <ProcedureCard data={resourceObj as any} className={className} />;

    case 'Bundle':
      return <BundleSummaryCard bundle={resourceObj} className={className} />;

    default:
      // For any other FHIR resource type, use generic card
      return <GenericResourceCard resource={resourceObj} className={className} />;
  }
}

export default FhirResourceRenderer;
