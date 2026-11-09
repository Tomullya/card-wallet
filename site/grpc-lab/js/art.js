// Characters of the Academy of Magical Post, as inline SVG strings (original designs).
// character(name, pose, label) → "<svg …>". Poses change the face and small extras.

const LINE = "#15233B";
const SKIN = "#F2CFAE";
const W = 3; // outline width

function face(cx, cy, pose) {
  const eyes = {
    idle: `<circle cx="${cx - 6}" cy="${cy - 2}" r="2.3" fill="${LINE}"/><circle cx="${cx + 6}" cy="${cy - 2}" r="2.3" fill="${LINE}"/>`,
    ask: `<circle cx="${cx - 6}" cy="${cy - 2}" r="2.6" fill="${LINE}"/><circle cx="${cx + 6}" cy="${cy - 2}" r="2.6" fill="${LINE}"/><path d="M${cx - 10} ${cy - 9} q4 -3 8 0" stroke="${LINE}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    happy: `<path d="M${cx - 9} ${cy - 1} q3 -4 6 0 M${cx + 3} ${cy - 1} q3 -4 6 0" stroke="${LINE}" stroke-width="2.4" fill="none" stroke-linecap="round"/>`,
    panic: `<circle cx="${cx - 6}" cy="${cy - 2}" r="3.6" fill="#fff" stroke="${LINE}" stroke-width="1.6"/><circle cx="${cx + 6}" cy="${cy - 2}" r="3.6" fill="#fff" stroke="${LINE}" stroke-width="1.6"/><circle cx="${cx - 6}" cy="${cy - 2}" r="1.3" fill="${LINE}"/><circle cx="${cx + 6}" cy="${cy - 2}" r="1.3" fill="${LINE}"/>`,
    stern: `<circle cx="${cx - 6}" cy="${cy - 1}" r="2.2" fill="${LINE}"/><circle cx="${cx + 6}" cy="${cy - 1}" r="2.2" fill="${LINE}"/><path d="M${cx - 10} ${cy - 8} l7 3 M${cx + 10} ${cy - 8} l-7 3" stroke="${LINE}" stroke-width="2.4" stroke-linecap="round"/>`,
    sneaky: `<path d="M${cx - 9} ${cy - 2} h6 M${cx + 3} ${cy - 2} h6" stroke="${LINE}" stroke-width="2.6" stroke-linecap="round"/>`,
  }[pose] ?? "";
  const mouth = {
    idle: `<path d="M${cx - 4} ${cy + 7} q4 3 8 0" stroke="${LINE}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    ask: `<ellipse cx="${cx}" cy="${cy + 8}" rx="2.6" ry="3.2" fill="${LINE}"/>`,
    happy: `<path d="M${cx - 6} ${cy + 6} q6 7 12 0 z" fill="${LINE}"/>`,
    panic: `<path d="M${cx - 6} ${cy + 9} q2 -3 4 0 q2 3 4 0 q2 -3 4 0" stroke="${LINE}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    stern: `<path d="M${cx - 5} ${cy + 8} h10" stroke="${LINE}" stroke-width="2.4" stroke-linecap="round"/>`,
    sneaky: `<path d="M${cx - 5} ${cy + 7} q7 3 10 -3" stroke="${LINE}" stroke-width="2.2" fill="none" stroke-linecap="round"/>`,
  }[pose] ?? "";
  return eyes + mouth;
}

function extras(pose, x, y) {
  if (pose === "panic") {
    return `<path d="M${x} ${y} q-5 9 0 13 q5 -4 0 -13z" fill="#7FB3E6" stroke="${LINE}" stroke-width="1.2"/>`;
  }
  if (pose === "happy") {
    return `<path d="M${x} ${y} l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2z" fill="#E0B25C" stroke="${LINE}" stroke-width="1.2"/>`;
  }
  return "";
}

const BODIES = {
  // Mage-Treasurer: plays the Wallet API (the client).
  treasurer: (pose) => `
    <path d="M60 6 C50 26 44 44 36 60 L84 60 C78 42 70 24 60 6 Z" fill="#2F4A75" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <path d="M58 26 l1.6 3.4 3.6.4 -2.7 2.5.8 3.6 -3.3 -1.9 -3.3 1.9.8 -3.6 -2.7 -2.5 3.6 -.4z" fill="#E0B25C"/>
    <circle cx="66" cy="46" r="2" fill="#E0B25C"/>
    <ellipse cx="60" cy="61" rx="32" ry="6.5" fill="#24395E" stroke="${LINE}" stroke-width="${W}"/>
    <path d="M38 104 L82 104 L92 146 L28 146 Z" fill="#C9551C" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <path d="M60 104 v42" stroke="${LINE}" stroke-width="2"/>
    <circle cx="60" cy="80" r="18" fill="${SKIN}" stroke="${LINE}" stroke-width="${W}"/>
    <circle cx="54" cy="78" r="6" fill="none" stroke="${LINE}" stroke-width="1.8"/>
    <circle cx="66" cy="78" r="6" fill="none" stroke="${LINE}" stroke-width="1.8"/>
    <path d="M60 78 h0" stroke="${LINE}"/>
    ${face(60, 80, pose)}
    <path d="M90 116 c10 -2 16 6 12 14 c-4 7 -16 6 -17 -1 z" fill="#E0B25C" stroke="${LINE}" stroke-width="2.4"/>
    <path d="M91 118 q6 -6 10 -1" stroke="${LINE}" stroke-width="2" fill="none"/>
    ${extras(pose, 36, 66)}`,

  // Master-Inspector: plays the Fraud Service.
  inspector: (pose) => `
    <path d="M60 2 C46 24 42 40 32 58 L88 58 C80 38 72 22 60 2 Z" fill="#5B3E8C" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <path d="M66 30 a8 8 0 1 1 -10 -8 a6 6 0 1 0 10 8z" fill="#E0B25C"/>
    <ellipse cx="60" cy="59" rx="34" ry="7" fill="#46306E" stroke="${LINE}" stroke-width="${W}"/>
    <path d="M36 104 L84 104 L94 146 L26 146 Z" fill="#2F4A75" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <circle cx="60" cy="78" r="17" fill="${SKIN}" stroke="${LINE}" stroke-width="${W}"/>
    ${face(60, 76, pose)}
    <path d="M44 86 C42 118 78 118 76 86 C70 96 50 96 44 86 Z" fill="#E8E2D6" stroke="${LINE}" stroke-width="${W}"/>
    <circle cx="20" cy="112" r="13" fill="#BFE0F5" stroke="${LINE}" stroke-width="${W}"/>
    <circle cx="16" cy="108" r="3.5" fill="#fff" opacity=".9"/>
    <path d="M10 126 h20 l-3 6 h-14z" fill="#7A4E2A" stroke="${LINE}" stroke-width="2"/>
    ${extras(pose, 94, 66)}`,

  // Mage-Watcher: plays the monitoring client (may only watch).
  watcher: (pose) => `
    <path d="M60 8 C48 28 44 44 38 60 L82 60 C76 44 72 28 60 8 Z" fill="#2C7A7B" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <circle cx="60" cy="8" r="5" fill="#E0B25C" stroke="${LINE}" stroke-width="2"/>
    <ellipse cx="60" cy="61" rx="30" ry="6" fill="#215E5F" stroke="${LINE}" stroke-width="${W}"/>
    <path d="M40 104 L80 104 L88 146 L32 146 Z" fill="#2C7A7B" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <circle cx="60" cy="80" r="17" fill="${SKIN}" stroke="${LINE}" stroke-width="${W}"/>
    ${face(60, 80, pose)}
    <path d="M78 98 l30 -22" stroke="#B88A3A" stroke-width="9" stroke-linecap="round"/>
    <path d="M78 98 l30 -22" stroke="${LINE}" stroke-width="1.5" stroke-linecap="round" opacity=".5"/>
    <circle cx="109" cy="75" r="5" fill="#BFE0F5" stroke="${LINE}" stroke-width="2"/>
    ${extras(pose, 38, 68)}`,

  // Gnome-Trickster: the attacker and the planted bugs.
  gnome: (pose) => `
    <path d="M30 70 C34 36 56 16 92 18 C76 26 72 44 82 70 Z" fill="#B0302E" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <ellipse cx="56" cy="70" rx="30" ry="6" fill="#8E2523" stroke="${LINE}" stroke-width="${W}"/>
    <path d="M38 112 L74 112 L80 146 L32 146 Z" fill="#3B5D3A" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <circle cx="56" cy="88" r="16" fill="${SKIN}" stroke="${LINE}" stroke-width="${W}"/>
    ${face(56, 86, pose)}
    <ellipse cx="56" cy="92" rx="7" ry="6" fill="#EFA27F" stroke="${LINE}" stroke-width="2"/>
    <path d="M42 98 C42 118 70 118 70 98 C64 106 48 106 42 98 Z" fill="#9C6B42" stroke="${LINE}" stroke-width="2.4"/>
    <circle cx="94" cy="118" r="12" fill="#A8322D" stroke="${LINE}" stroke-width="${W}"/>
    <text x="94" y="123" text-anchor="middle" font-family="Georgia, serif" font-size="14" font-weight="700" fill="#F6F1E6">?</text>
    ${extras(pose, 84, 74)}`,

  // Post owl: one owl = one message.
  owl: (pose) => `
    <path d="M30 60 q-28 -18 -26 12 q14 -8 28 4 z M90 60 q28 -18 26 12 q-14 -8 -28 4 z" fill="#8A6A4A" stroke="${LINE}" stroke-width="${W}" stroke-linejoin="round"/>
    <path d="M38 34 l-6 -16 l16 10 M82 34 l6 -16 l-16 10" fill="#A9845E" stroke="${LINE}" stroke-width="2.4" stroke-linejoin="round"/>
    <ellipse cx="60" cy="72" rx="32" ry="40" fill="#A9845E" stroke="${LINE}" stroke-width="${W}"/>
    <ellipse cx="60" cy="86" rx="20" ry="24" fill="#E6D3B3"/>
    <circle cx="48" cy="58" r="11" fill="#F6F1E6" stroke="${LINE}" stroke-width="2.4"/>
    <circle cx="72" cy="58" r="11" fill="#F6F1E6" stroke="${LINE}" stroke-width="2.4"/>
    <circle cx="${pose === "panic" ? 48 : 50}" cy="58" r="${pose === "panic" ? 3 : 4.5}" fill="${LINE}"/>
    <circle cx="${pose === "panic" ? 72 : 74}" cy="58" r="${pose === "panic" ? 3 : 4.5}" fill="${LINE}"/>
    <path d="M56 68 l4 7 l4 -7 z" fill="#E0B25C" stroke="${LINE}" stroke-width="1.6"/>
    <rect x="42" y="112" width="36" height="16" rx="5" fill="#F6F1E6" stroke="${LINE}" stroke-width="2.4"/>
    <circle cx="60" cy="120" r="5" fill="#A8322D" stroke="${LINE}" stroke-width="1.4"/>
    ${extras(pose, 96, 30)}`,
};

/** SVG markup for a character in a pose; label becomes the accessible name. */
export function character(name, pose = "idle", label = name) {
  const body = BODIES[name];
  if (!body) throw new Error(`unknown character ${name}`);
  return `<svg class="char char--${name}" viewBox="0 0 120 150" role="img" aria-label="${escapeAttr(label)}">${body(pose)}</svg>`;
}

function escapeAttr(text) {
  return String(text).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}
