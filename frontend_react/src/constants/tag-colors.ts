// Tags read as machine metadata: mono figures, soft tinted chips. The three
// known scopes carry a distinct brand hue so scope is legible at a glance;
// unscoped tags stay a neutral muted chip. Hues are kept faint (/15 tint) to
// preserve the instrument feel — see brand-accents.ts for the same tokens.
const scopeTagColors: Record<string, string> = {
  tool: 'bg-brand-cyan/15 text-brand-cyan font-mono border border-transparent',
  artifact: 'bg-brand-lime/15 text-brand-lime font-mono border border-transparent',
  goal: 'bg-brand-purple/15 text-brand-purple font-mono border border-transparent',
}
export const defaultTagColor = 'bg-muted text-muted-foreground font-mono border border-transparent'

export function getTagColorClass(scope: string | null | undefined): string {
  if (scope && scope in scopeTagColors) {
    return scopeTagColors[scope]
  }
  return defaultTagColor
}

export function getTagScope(tagName: string): string | null {
  const parts = tagName.split(':')
  if (parts.length === 2) {
    return parts[0]
  }
  return null
}
