import type { IconProps } from './icons/props.ts'

/** Display options for the OpenJev brand wordmark. */
export interface BrandWordmarkProps extends IconProps {
  /** Whether to include the leading mark; defaults to true. */
  includeMark?: boolean | undefined
}

/**
 * Render the full OpenJev wordmark.
 * @param props.size - height in px (default 24; width follows the selected artwork).
 * @param props.className - extra class for layout placement.
 * @param props.includeMark - whether to include the leading mark.
 * @returns the wordmark svg (aria-hidden decorative brand art).
 */
export function BrandWordmark({ size = 24, className, includeMark = true }: BrandWordmarkProps) {
  const width = includeMark ? 152 : 124
  return (
    <svg
      width={(size * width) / 24}
      height={size}
      className={className}
      viewBox={includeMark ? '0 0 152 24' : '28 0 124 24'}
      fill="none"
      aria-hidden="true"
    >
      {includeMark && (
        <>
          <path d="M19.2 5v8.8a4.6 4.6 0 0 1-9.2 0v-2.2" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" fill="none" />
          <circle cx="10" cy="6.6" r="1.8" fill="currentColor" />
        </>
      )}
      <text
        x="30"
        y="17.5"
        fill="currentColor"
        fontFamily="inherit"
        fontSize="17"
        fontWeight="700"
        letterSpacing="-0.2"
      >
        OpenJev
      </text>
    </svg>
  )
}
