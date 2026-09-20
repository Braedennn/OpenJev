/**
 * Jev (TypeSafe) decision-layer credential card: stores the Jev API key in
 * the harness credential document under a fixed reference, which the local
 * Jev bridge reads at startup. This keeps the key out of the repository and
 * out of hand-edited env files.
 */

import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { ModelsOperations } from './operations.ts'
import type { ModelsKey } from './locales.ts'
import styles from './ModelsSection.module.css'

/** Credential reference the Jev bridge reads from `.credentials.yaml`. */
export const JEV_CREDENTIAL_REF = 'openjev'

/** Props of {@link JevKeyCard}. */
export interface JevKeyCardProps {
  /** The page's Host operations (credential read/write). */
  operations: ModelsOperations
  /** Section copy. */
  t: (key: ModelsKey) => string
  /** Disable writes (read-only settings provider). */
  readOnly: boolean
  /** Called after a successful write or removal. */
  onChanged: () => void
}

/**
 * Render the Jev credential row.
 * @param props - see {@link JevKeyCardProps}.
 * @returns the card element.
 */
export function JevKeyCard({ operations, t, readOnly, onChanged }: JevKeyCardProps): ReactNode {
  const [draft, setDraft] = useState('')
  const [configured, setConfigured] = useState<boolean | undefined>(undefined)
  const [failure, setFailure] = useState<string | undefined>(undefined)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let live = true
    void operations.describeCredential(JEV_CREDENTIAL_REF).then((info) => {
      if (live) setConfigured(info?.configured === true)
    })
    return () => { live = false }
  }, [operations])

  const save = async (): Promise<void> => {
    const value = draft.trim()
    if (value.length === 0) {
      setFailure(t('jevKeyRequired'))
      return
    }
    setBusy(true)
    const refused = await operations.storeCredential(JEV_CREDENTIAL_REF, value)
    setBusy(false)
    if (refused !== undefined) {
      setFailure(refused)
      return
    }
    setDraft('')
    setConfigured(true)
    setFailure(undefined)
    onChanged()
  }

  const remove = async (): Promise<void> => {
    setBusy(true)
    const refused = await operations.removeCredential(JEV_CREDENTIAL_REF)
    setBusy(false)
    if (refused !== undefined) {
      setFailure(refused)
      return
    }
    setConfigured(false)
    setFailure(undefined)
    onChanged()
  }

  return (
    <li className={styles['rowCard']}>
      <div className={styles['rowHead']}>
        <span className={styles['rowIdentity']}>
          <span className={styles['rowName']}>{t('jevTitle')}</span>
          {configured === true
            ? (
              <span
                className={`${styles['credentialDot']} ${styles['credentialDotConfigured']}`}
                role="img"
                aria-label={t('jevConfigured')}
                title={t('jevConfigured')}
              />
            )
            : configured === false
              ? (
                <span
                  className={`${styles['credentialDot']} ${styles['credentialDotMissing']}`}
                  role="img"
                  aria-label={t('jevMissing')}
                  title={t('jevMissing')}
                />
              )
              : null}
        </span>
        {configured === true && (
          <span className={styles['rowActions']}>
            <button
              type="button"
              className={styles['dangerButton']}
              disabled={busy || readOnly}
              onClick={() => { void remove() }}
            >
              {t('jevRemove')}
            </button>
          </span>
        )}
      </div>
      <p className={styles['intro']}>{t('jevIntro')}</p>
      <div className={styles['field']}>
        <span className={styles['fieldLabel']}>{t('keyInput')}</span>
        <input
          className={styles['input']}
          type="password"
          value={draft}
          placeholder={t('jevKeyPlaceholder')}
          disabled={busy || readOnly}
          onChange={(event) => { setDraft(event.target.value) }}
        />
      </div>
      <div className={styles['rowActions']}>
        <button
          type="button"
          className={styles['secondaryButton']}
          disabled={busy || readOnly}
          onClick={() => { void save() }}
        >
          {busy ? t('jevSaving') : t('jevSave')}
        </button>
      </div>
      {failure === undefined ? null : <p role="alert" className={styles['error']}>{failure}</p>}
    </li>
  )
}
