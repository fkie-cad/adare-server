// Tags read as machine metadata: one restrained muted chip, mono figures, and a
// faint teal edge to mark scoped tags. Scope is carried by the "scope:" prefix in
// the label, not by a saturated hue per scope.
const scopedTagColor = 'bg-muted text-foreground font-mono border border-border'
export const defaultTagColor = 'bg-muted text-muted-foreground font-mono border border-transparent'

const scopedScopes = new Set(['tool', 'artifact', 'goal'])

export function getTagColorClass(scope: string | null | undefined): string {
  if (scope && scopedScopes.has(scope)) {
    return scopedTagColor
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
