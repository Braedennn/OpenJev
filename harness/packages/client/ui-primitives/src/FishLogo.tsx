import type { IconProps } from './icons/props.ts'

/** Native viewBox of {@link FISH_LOGO_PATH} (width and height in user units). */
export const FISH_LOGO_VIEWBOX = { width: 24, height: 24 }

/** The OpenJev mark: a judge's "J" with a decision node, exported for consumers that compose their own svg around the same geometry. */
export const FISH_LOGO_PATH = 'M15.6 4.6v8.2a4.6 4.6 0 0 1-9.2 0v-2.2'

/**
 * Render the OpenJev mark.
 * @param props.size - width in px (default 24).
 * @param props.className - extra class for layout placement.
 * @returns the mark svg (aria-hidden; pair with the wordmark for accessibility).
 */
export function FishLogo({ size = 24, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      className={className}
      viewBox={`0 0 ${FISH_LOGO_VIEWBOX.width} ${FISH_LOGO_VIEWBOX.height}`}
      fill="none"
      aria-hidden="true"
    >
      <path d={FISH_LOGO_PATH} stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" fill="none" />
      <circle cx="6.4" cy="6.2" r="1.8" fill="currentColor" />
    </svg>
  )
}
