import React from 'react';
import Link from '@docusaurus/Link';
import {
  House,
  Code,
  Package,
  FileCode,
  BookOpen,
  ClockCounterClockwise,
} from '@phosphor-icons/react';

const iconMap = {
  house: House,
  code: Code,
  package: Package,
  'file-code': FileCode,
  'book-open': BookOpen,
  clock: ClockCounterClockwise,
};

export default function NavbarIconLink({
  icon,
  label,
  to,
  className,
}: {
  icon: keyof typeof iconMap;
  label: string;
  to: string;
  className?: string;
}) {
  const IconComponent = iconMap[icon];

  return (
    <Link to={to} className={`navbar__link ${className || ''}`}>
      {IconComponent && (
        <IconComponent size={16} weight="bold" style={{ marginRight: '6px', verticalAlign: 'middle' }} />
      )}
      <span style={{ verticalAlign: 'middle' }}>{label}</span>
    </Link>
  );
}
