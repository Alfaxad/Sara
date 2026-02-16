'use client';

import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/Card';
import { User, MapPin, Phone, Calendar, Hash } from 'lucide-react';

interface PatientName {
  use?: string;
  family?: string;
  given?: string[];
  prefix?: string[];
  suffix?: string[];
  text?: string;
}

interface PatientAddress {
  use?: string;
  line?: string[];
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

interface PatientTelecom {
  system?: string;
  value?: string;
  use?: string;
}

interface PatientIdentifier {
  system?: string;
  value?: string;
  type?: {
    coding?: Array<{ code?: string; display?: string }>;
    text?: string;
  };
}

interface PatientData {
  resourceType: 'Patient';
  id?: string;
  name?: PatientName[];
  birthDate?: string;
  gender?: string;
  address?: PatientAddress[];
  telecom?: PatientTelecom[];
  identifier?: PatientIdentifier[];
  [key: string]: unknown;
}

export interface PatientCardProps {
  data: PatientData;
  className?: string;
}

function formatName(name?: PatientName): string {
  if (!name) return 'Unknown Patient';
  if (name.text) return name.text;

  const parts: string[] = [];
  if (name.prefix) parts.push(...name.prefix);
  if (name.given) parts.push(...name.given);
  if (name.family) parts.push(name.family);
  if (name.suffix) parts.push(...name.suffix);

  return parts.join(' ') || 'Unknown Patient';
}

function calculateAge(birthDate?: string): string {
  if (!birthDate) return '';

  const birth = new Date(birthDate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }

  return `${age}y`;
}

function formatDate(dateString?: string): string {
  if (!dateString) return '';

  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatAddress(address?: PatientAddress): string {
  if (!address) return '';

  const parts: string[] = [];
  if (address.line) parts.push(...address.line);
  if (address.city) parts.push(address.city);
  if (address.state) parts.push(address.state);
  if (address.postalCode) parts.push(address.postalCode);

  return parts.join(', ');
}

function getPhone(telecoms?: PatientTelecom[]): string | undefined {
  if (!telecoms) return undefined;
  const phone = telecoms.find((t) => t.system === 'phone');
  return phone?.value;
}

function getMRN(identifiers?: PatientIdentifier[]): string | undefined {
  if (!identifiers) return undefined;

  // Look for MRN specifically
  const mrn = identifiers.find((id) => {
    if (id.type?.coding) {
      return id.type.coding.some((c) => c.code === 'MR' || c.code === 'MRN');
    }
    if (id.type?.text) {
      return id.type.text.toLowerCase().includes('mrn') || id.type.text.toLowerCase().includes('medical record');
    }
    return false;
  });

  if (mrn?.value) return mrn.value;

  // Fall back to first identifier
  return identifiers[0]?.value;
}

function formatGender(gender?: string): string {
  if (!gender) return '';

  switch (gender.toLowerCase()) {
    case 'male':
      return 'M';
    case 'female':
      return 'F';
    case 'other':
      return 'O';
    case 'unknown':
      return 'U';
    default:
      return gender.charAt(0).toUpperCase();
  }
}

export function PatientCard({ data, className }: PatientCardProps) {
  const name = formatName(data.name?.[0]);
  const age = calculateAge(data.birthDate);
  const dob = formatDate(data.birthDate);
  const gender = formatGender(data.gender);
  const address = formatAddress(data.address?.[0]);
  const phone = getPhone(data.telecom);
  const mrn = getMRN(data.identifier);

  return (
    <Card variant="surface" className={cn('overflow-hidden', className)}>
      <div className="p-4">
        {/* Header with name and basic info */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-sara-accent-soft flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5 text-sara-accent" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-display text-display-lg text-sara-text-primary truncate">
              {name}
            </h3>
            <div className="flex items-center gap-2 text-body-small text-sara-text-secondary mt-1">
              {age && <span>{age}</span>}
              {age && gender && <span className="text-sara-text-muted">|</span>}
              {gender && <span>{gender}</span>}
              {(age || gender) && dob && <span className="text-sara-text-muted">|</span>}
              {dob && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {dob}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* MRN - Highlighted */}
        {mrn && (
          <div className="mb-4 p-3 bg-sara-accent-soft rounded-sara-sm border border-sara-accent/20">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-sara-accent" />
              <span className="text-caption text-sara-text-secondary uppercase tracking-wider">
                MRN
              </span>
              <span className="text-body font-semibold text-sara-accent ml-auto">
                {mrn}
              </span>
            </div>
          </div>
        )}

        {/* Additional details */}
        <CardContent className="p-0 space-y-2">
          {address && (
            <div className="flex items-start gap-2 text-body-small">
              <MapPin className="w-4 h-4 text-sara-text-muted flex-shrink-0 mt-0.5" />
              <span className="text-sara-text-secondary">{address}</span>
            </div>
          )}
          {phone && (
            <div className="flex items-center gap-2 text-body-small">
              <Phone className="w-4 h-4 text-sara-text-muted flex-shrink-0" />
              <span className="text-sara-text-secondary">{phone}</span>
            </div>
          )}
        </CardContent>
      </div>
    </Card>
  );
}

export default PatientCard;
