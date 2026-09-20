/**
 * First-run notice for the Jev decision layer: prompts for the Jev API key
 * while none is stored, then dismisses itself once the key is configured.
 */

import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Button } from '@deepseek-ai/dsh-client-ui-primitives'
import type { InjectFace, PropsRuntime } from '@deepseek-ai/dsh-client-ui-slots'
import { JEV_CREDENTIAL_REF } from './JevKeyCard.tsx'
import type { ModelsOperations } from './operations.ts'
import type { ModelsKey } from './locales.ts'
import { OnboardingModal } from './OnboardingModal.tsx'
import styles from './DeepSeekOnboardingDialog.module.css'
import modelStyles from './ModelsSection.module.css'

/** Injected dependencies of {@link JevOnboardingDialog}. */
export interface JevOnboardingInjected {
  /** Credential read/write operations. */
  operations: ModelsOperations
  /** Section copy. */
  t: (key: ModelsKey) => string
}

/** Props of {@link JevOnboardingDialog}. */
export type JevOnboardingDialogProps =
  PropsRuntime<'settings.onboarding'> & InjectFace<JevOnboardingInjected>

/**
 * Prompt for the Jev API key while the credential reference is empty.
 * @param props - onboarding owner state and Models operations.
 * @returns the onboarding modal, or null once no intervention is needed.
 */
export function JevOnboardingDialog(props: JevOnboardingDialogProps): ReactNode {
  const { complete, operations, t } = props
  const [configured, setConfigured] = useState<boolean | undefined>(undefined)
  const [draft, setDraft] = useState('')
  const [failure, setFailure] = useState<string | undefined>(undefined)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let live = true
    void operations.describeCredential(JEV_CREDENTIAL_REF).then((info) => {
      if (live) setConfigured(info?.configured === true)
    })
    return () => { live = false }
  }, [operations])

  useEffect(() => {
    if (configured === true) complete()
  }, [complete, configured])

  if (configured !== false) return null

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
    setFailure(undefined)
    setConfigured(true)
  }

  return (
    <OnboardingModal title={t('jevOnboardingTitle')}>
      <p className={styles.description}>{t('jevOnboardingBody')}</p>
      <div className={styles.editor}>
        <div className={modelStyles.field}>
          <span className={modelStyles.fieldLabel}>{t('keyInput')}</span>
          <input
            className={modelStyles.input}
            type="password"
            autoFocus
            value={draft}
            placeholder={t('jevKeyPlaceholder')}
            disabled={busy}
            onChange={(event) => { setDraft(event.target.value) }}
          />
        </div>
        {failure === undefined ? null : <p role="alert" className={modelStyles.error}>{failure}</p>}
        <div className={modelStyles.field}>
          <Button disabled={busy} onClick={() => { void save() }}>
            {t('jevOnboardingSave')}
          </Button>
          <Button variant="outline" disabled={busy} onClick={() => { complete() }}>
            {t('jevOnboardingLater')}
          </Button>
        </div>
      </div>
    </OnboardingModal>
  )
}
