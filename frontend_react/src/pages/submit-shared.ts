import { AxiosError } from 'axios'

export interface CurrentFile {
  label: string
  url: string
}

/** Machine-readable submit/ingest error codes (mirror of the server's SubmitErrorCode). */
export const SubmitCode = {
  ALREADY_PUBLISHED: 'ALREADY_PUBLISHED',
  OPEN_DUPLICATE: 'OPEN_DUPLICATE',
  CONTENT_DUPLICATE: 'CONTENT_DUPLICATE',
  INVALID_CONTENT: 'INVALID_CONTENT',
  MISSING_FILES: 'MISSING_FILES',
  UNKNOWN_DEPENDENCY: 'UNKNOWN_DEPENDENCY',
  NOT_FOUND: 'NOT_FOUND',
  INVALID_STATE: 'INVALID_STATE',
  UPSTREAM_UNAVAILABLE: 'UPSTREAM_UNAVAILABLE',
  PARSE_ERROR: 'PARSE_ERROR',
} as const
export type SubmitCode = (typeof SubmitCode)[keyof typeof SubmitCode]

export interface SubmitFailure {
  message: string
  code?: SubmitCode
  pr_number?: number
}

/** Pull the server-provided ``{error, code, pr_number}`` out of an axios error, with a fallback. */
export function extractSubmitFailure(error: unknown, fallback: string): SubmitFailure {
  if (error instanceof AxiosError) {
    const data = error.response?.data as
      | { error?: string; code?: SubmitCode; pr_number?: number }
      | undefined
    if (data?.error) return { message: data.error, code: data.code, pr_number: data.pr_number }
    return { message: error.message || fallback }
  }
  if (error instanceof Error) return { message: error.message || fallback }
  return { message: fallback }
}

/** Backwards-compatible message-only extractor. */
export function extractSubmitError(error: unknown, fallback: string): string {
  return extractSubmitFailure(error, fallback).message
}
