
export const sizeList = ['sm', 'md', 'lg'] as const;
export type SizeType = typeof sizeList[number];
export function isValidSizeType(value: string): value is SizeType {
    return (sizeList as readonly string[]).includes(value);
}
