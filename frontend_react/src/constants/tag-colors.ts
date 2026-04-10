// Tailwind CSS color classes for scoped tags
export const scopeColorMap: Record<string, string> = {
  tool: 'bg-blue-800 text-white',
  artifact: 'bg-green-800 text-white',
  goal: 'bg-purple-800 text-white',
}

export const defaultTagColor = 'bg-muted-foreground text-background'

export function getTagColorClass(scope: string | null | undefined): string {
  if (scope && scope in scopeColorMap) {
    return scopeColorMap[scope]
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
