/**
 * OpenJev conductor plugin: Jev as the decision layer for every agent step.
 *
 * - Registers Jev tools (ask/verify/screen/classify/route/trace) that call the
 *   local openjev daemon, which formats every question with the jev-studio core.
 * - Consults Jev automatically on every `agent/pre-step` (once per thinking
 *   step) and writes the decision into the step as a plugin notice.
 * - Every consultation is appended to the daemon trace (proof of coverage).
 */
import type { Context } from '@deepseek-ai/cordis'
import { createUserMessage } from '@deepseek-ai/dsh-llm'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'openjev'
export const inject = ['tools']

const DAEMON = (process.env.OPENJEV_DAEMON_URL ?? 'http://127.0.0.1:8931').replace(/\/+$/u, '')
const AUTO = process.env.OPENJEV_AUTO_CONSULT !== '0'
const INJECT = process.env.OPENJEV_INJECT ?? 'first'

interface JevAnswers {
  [questionId: string]: { type?: string; choice?: string; confidence?: number; noul?: number; probabilities?: Record<string, number> }
}

interface JevResult {
  answers?: JevAnswers
  error?: string
}

async function jev(endpoint: string, body: Record<string, unknown>, source: string): Promise<JevResult> {
  const response = await fetch(`${DAEMON}${endpoint}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ ...body, source }),
  })
  const payload = (await response.json()) as JevResult
  if (!response.ok) throw new Error(payload.error ?? `${endpoint} failed with ${String(response.status)}`)
  return payload
}

function preStepQuestions() {
  return {
    direction: {
      type: 'choice',
      instructions: 'Given the task and the conversation so far, what should the agent do next?',
      criteria: {
        act: 'Directly perform the task or answer now',
        gather: 'Gather more context or evidence first',
        clarify: 'Ask the user a clarifying question first',
        verify: 'Verify an existing claim before proceeding',
      },
    },
    context: {
      type: 'noul',
      instructions: 'Does the conversation already contain everything needed to answer or act correctly?',
    },
  }
}

function lastUserText(messages: readonly unknown[]): string | undefined {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const message = messages[i] as { role?: string; content?: unknown }
    if (message?.role !== 'user') continue
    if (typeof message.content === 'string') return message.content.slice(0, 4000)
    if (Array.isArray(message.content)) {
      const text = message.content
        .map(part => (part as { type?: string; text?: string }).type === 'text' ? (part as { text?: string }).text ?? '' : '')
        .join('\n')
        .trim()
      if (text) return text.slice(0, 4000)
    }
  }
  return undefined
}

function decisionNotice(result: JevResult) {
  const direction = result.answers?.direction ?? {}
  const context = result.answers?.context ?? {}
  const probabilities = direction.probabilities ? JSON.stringify(direction.probabilities) : 'n/a'
  const text = [
    '[OpenJev/Jev decision for this step]',
    `next action: ${direction.choice ?? 'unknown'} (confidence ${direction.confidence ?? 'n/a'})`,
    `probabilities: ${probabilities}`,
    `enough context: ${context.noul ?? 'n/a'}`,
    'Follow this decision; if new evidence contradicts it, call jev_verify and let Jev re-decide.',
  ].join('\n')
  return createUserMessage({
    content: [{ type: 'text' as const, text }],
    source: {
      kind: 'plugin' as const,
      plugin: 'openjev',
      form: 'notice' as const,
      summary: `jev: ${direction.choice ?? 'unknown'}`,
    },
  })
}

function asJson(value: string, label: string): unknown {
  try {
    return JSON.parse(value)
  } catch {
    throw new Error(`${label} must be valid JSON`)
  }
}

function stringOutput(render: (value: unknown) => string) {
  return { schema: { type: 'string' as const }, render: (_args: unknown, value: unknown) => [{ type: 'text' as const, text: render(value) }] }
}

export function apply(ctx: Context) {
  const trace = (label: string) => `agent/pre-step:${label}`
  console.log(`[openjev] plugin loaded (daemon=${DAEMON}, auto-consult=${AUTO ? 'on' : 'off'}, inject=${INJECT})`)

  ctx.tools.register(defineTool({
    name: 'jev_ask',
    description: 'Ask Jev typed questions about any state. questions_json holds {id: {type: "noul"|"choice"|"score", instructions, criteria}}.',
    parameters: {
      state: { type: 'string', required: true, description: 'State text or JSON the questions are about' },
      questions_json: { type: 'string', required: true, description: 'Questions object as JSON' },
    },
    output: stringOutput(value => JSON.stringify(value, null, 2)),
    async execute(args) {
      return await jev('/ask', { state: args.state, questions: asJson(args.questions_json, 'questions_json') }, 'tool:jev_ask')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'jev_verify',
    description: 'Verify claims against evidence. Returns per-claim verdicts (verified/contradicted/unsupported), probabilities, and the supporting evidence id.',
    parameters: {
      claims_json: { type: 'string', required: true, description: 'Claims array as JSON' },
      evidence_json: { type: 'string', required: true, description: 'Evidence array as JSON (strings or {id, text})' },
    },
    output: stringOutput(value => JSON.stringify(value, null, 2)),
    async execute(args) {
      return await jev('/verify', {
        claims: asJson(args.claims_json, 'claims_json'),
        evidence: asJson(args.evidence_json, 'evidence_json'),
      }, 'tool:jev_verify')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'jev_screen',
    description: 'Screen untrusted text before it enters context. Flags prompt injection, boilerplate, and irrelevance; recommends pass/review/block/skip.',
    parameters: {
      text: { type: 'string', required: true, description: 'Text to screen' },
      purpose: { type: 'string', description: 'What the text is needed for' },
    },
    output: stringOutput(value => JSON.stringify(value, null, 2)),
    async execute(args) {
      return await jev('/screen', { text: args.text, purpose: args.purpose }, 'tool:jev_screen')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'jev_classify',
    description: 'Classify text into labels. labels_json is a list of strings or {label, description} objects; multi=true judges each label independently.',
    parameters: {
      text: { type: 'string', required: true, description: 'Text to classify' },
      labels_json: { type: 'string', required: true, description: 'Labels as JSON' },
      multi: { type: 'boolean', description: 'Judge each label independently' },
    },
    output: stringOutput(value => JSON.stringify(value, null, 2)),
    async execute(args) {
      return await jev('/classify', {
        text: args.text,
        labels: asJson(args.labels_json, 'labels_json'),
        multi: args.multi === true,
      }, 'tool:jev_classify')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'jev_route',
    description: 'Pick a handler for a request and fill its closed-set arguments in one call. handlers_json is {name: description} or {name: {description, args}}.',
    parameters: {
      request: { type: 'string', required: true, description: 'The request to route' },
      handlers_json: { type: 'string', required: true, description: 'Handlers object as JSON' },
    },
    output: stringOutput(value => JSON.stringify(value, null, 2)),
    async execute(args) {
      return await jev('/route', {
        request: args.request,
        handlers: asJson(args.handlers_json, 'handlers_json'),
      }, 'tool:jev_route')
    },
  }))

  ctx.tools.register(defineTool({
    name: 'jev_trace',
    description: 'Show recent Jev consultations (endpoint, source, probabilities, latency) from the OpenJev trace log.',
    parameters: {
      limit: { type: 'number', description: 'How many recent entries (default 20)' },
    },
    output: stringOutput(value => JSON.stringify(value, null, 2)),
    async execute(args) {
      const limit = typeof args.limit === 'number' ? Math.trunc(args.limit) : 20
      const response = await fetch(`${DAEMON}/trace?limit=${String(limit)}`)
      return await response.json()
    },
  }))

  if (!AUTO) return

  ctx.on(
    'agent/pre-step',
    async ({ messages: claimed, turn, step, signal }, next) => {
      const decision = await next()
      if (decision.kind === 'reject' || signal.aborted) return decision
      const task = lastUserText(claimed) ?? lastUserText(decision.messages)
      if (task === undefined) return decision
      try {
        const result = await jev('/ask', { state: task, questions: preStepQuestions() }, trace(`turn=${String(turn)} step=${String(step)}`))
        const direction = result.answers?.direction ?? {}
        console.log(`[openjev] jev consult turn=${String(turn)} step=${String(step)} -> ${direction.choice ?? 'unknown'} (confidence ${direction.confidence ?? 'n/a'}) verified via trace`)
        const shouldInject = INJECT === 'always' || (INJECT === 'first' && step === 1) || (direction.confidence ?? 1) < 0.6
        if (!shouldInject) return decision
        return { ...decision, messages: [...decision.messages, decisionNotice(result)] }
      } catch (error) {
        console.error(`[openjev] jev consult failed: ${error instanceof Error ? error.message : String(error)}`)
        return decision
      }
    },
    { prepend: true },
  )
}
