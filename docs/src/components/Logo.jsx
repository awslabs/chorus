function LogomarkPaths() {
  return (
    <g fill="none" strokeLinejoin="round" strokeWidth={3}>
      {/* Central node */}
      <circle cx="18" cy="18" r="7" stroke="#38BDF8" fill="#0F172A" />
      
      {/* Connecting lines to satellite nodes */}
      <line x1="18" y1="18" x2="8" y2="8" stroke="#38BDF8" />
      <line x1="18" y1="18" x2="28" y2="8" stroke="#38BDF8" />
      <line x1="18" y1="18" x2="28" y2="28" stroke="#38BDF8" />
      <line x1="18" y1="18" x2="8" y2="28" stroke="#38BDF8" />
      
      {/* Satellite nodes */}
      <circle cx="8" cy="8" r="3" stroke="#38BDF8" fill="#0F172A" />
      <circle cx="28" cy="8" r="3" stroke="#38BDF8" fill="#0F172A" />
      <circle cx="28" cy="28" r="3" stroke="#38BDF8" fill="#0F172A" />
      <circle cx="8" cy="28" r="3" stroke="#38BDF8" fill="#0F172A" />
    </g>
  )
}

export function Logomark(props) {
  return (
    <svg aria-hidden="true" viewBox="0 0 36 36" fill="none" {...props}>
      <LogomarkPaths />
    </svg>
  )
}

export function Logo(props) {
  return (
    <svg aria-hidden="true" viewBox="0 0 120 36" fill="none" {...props}>
      <text
        x="0"
        y="24"
        fontFamily="sans-serif"
        fontSize="24"
        fontWeight="bold"
        fill="currentColor"
      >
        Chorus
      </text>
    </svg>
  )
}
