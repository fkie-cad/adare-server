export const sizeList = ['sm', 'md', 'lg'] as const
export type SizeType = (typeof sizeList)[number]

export function isValidSizeType(value: string): value is SizeType {
  return (sizeList as readonly string[]).includes(value)
}

export const sizePixelMapping: Record<SizeType, string> = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-20 h-20',
}

export const sizeFontMapping: Record<SizeType, string> = {
  sm: 'text-xs',
  md: 'text-base',
  lg: 'text-2xl',
}
