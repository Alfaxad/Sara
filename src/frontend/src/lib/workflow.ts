export interface WorkflowStep {
  id: string;
  action: string;
  description: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  timestamp?: number;
}

/**
 * Parse a raw FHIR action into a human-readable description
 */
export function parseActionToDescription(action: string): string {
  // GET requests
  if (action.startsWith('GET')) {
    if (action.includes('/Patient')) {
      if (action.includes('name=') || action.includes('identifier=')) {
        return 'Searching patient records';
      }
      return 'Retrieving patient information';
    }
    if (action.includes('/Observation')) {
      if (action.includes('code=MG') || action.includes('code=magnesium')) {
        return 'Checking magnesium levels';
      }
      if (action.includes('code=K') || action.includes('code=potassium')) {
        return 'Checking potassium levels';
      }
      if (action.includes('code=GLU') || action.includes('code=glucose')) {
        return 'Retrieving blood glucose readings';
      }
      if (action.includes('code=A1C') || action.includes('code=HbA1C')) {
        return 'Checking HbA1C levels';
      }
      if (action.includes('code=BP') || action.includes('blood-pressure')) {
        return 'Retrieving blood pressure readings';
      }
      return 'Retrieving lab results';
    }
    if (action.includes('/MedicationRequest')) {
      return 'Checking medication orders';
    }
    if (action.includes('/ServiceRequest')) {
      return 'Checking service requests';
    }
    if (action.includes('/Condition')) {
      return 'Retrieving patient conditions';
    }
    if (action.includes('/Procedure')) {
      return 'Retrieving procedure history';
    }
    return 'Querying medical records';
  }

  // POST requests
  if (action.startsWith('POST')) {
    if (action.includes('/Observation')) {
      return 'Recording measurement';
    }
    if (action.includes('/MedicationRequest')) {
      return 'Ordering medication';
    }
    if (action.includes('/ServiceRequest')) {
      return 'Creating referral';
    }
    if (action.includes('/DiagnosticReport')) {
      return 'Creating diagnostic report';
    }
    return 'Creating medical record';
  }

  // FINISH
  if (action.startsWith('FINISH')) {
    return 'Completing task';
  }

  // Default
  return 'Processing request';
}

/**
 * Extract the endpoint from a raw action string
 */
export function extractEndpoint(action: string): string {
  // Match GET /endpoint or POST /endpoint patterns
  const match = action.match(/(GET|POST)\s+([^\s?]+)/);
  return match ? match[2] : action;
}

/**
 * Generate a unique step ID
 */
export function generateStepId(): string {
  return `step-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}
