// Default color palette for scoped tags
// Colors map scope names to Quasar color names
export const scopeColorMap: Record<string, string> = {
  tool: 'blue-9',
  artifact: 'green-9',
  goal: 'purple-9',
};

export const defaultTagColor = 'grey-8';

export function getTagColor(scope: string | null): string {
  if (scope && scope in scopeColorMap) {
    return scopeColorMap[scope];
  }
  return defaultTagColor;
}
