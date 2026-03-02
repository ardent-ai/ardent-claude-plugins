# Mandatory Scan Patterns

## Type Quality Scan

Grep new/modified `.ts`/`.tsx` files for these anti-patterns and flag each occurrence:

| Pattern | What to look for | Example |
|---------|-----------------|---------|
| Indexed access types | `SomeType['prop']` used as a standalone type annotation | `NonNullable<Props['plugins']>` |
| Utility-type extraction | `ReturnType<typeof fn>`, `Parameters<typeof fn>[0]`, `Awaited<ReturnType<...>>` as annotations | `const x: ReturnType<typeof createFoo> = ...` |
| `typeof` in type positions | `typeof variable` or `(typeof array)[number]` as type annotations | `Map<string, (typeof items)[number]>`, `response: { data: typeof records }` |
| `unknown` + cast | Variable typed `unknown` then immediately cast with `as` | `const data: unknown = ...; (data as MyType).foo` |
| Inline anonymous types | `{ foo: string; bar: number }` in function signatures, variable annotations, or generic type params for shapes that deserve a name | `postRelease<{ skillId: string }>()`, `env: { ADMIN_EMAILS?: string }` when a type already exists |
| Weakened discriminated unions | A discriminated union replaced with a flat type using optional fields | `{ status: string; installedVersion?: string }` instead of `InstalledSkill \| CatalogSkill` |

These are persistent problems flagged repeatedly in human review. Every occurrence is a finding — no counterargument needed.

## AI Debt Scan

Check new/modified files for these AI-generated code patterns and flag each occurrence:

| Pattern | What to look for | Example |
|---------|-----------------|---------|
| Restating comments | Comments that echo what the code already says | `// increment counter` above `i++`, `// return the result` above `return result` |
| Docstring bloat | Multi-line docstrings on trivial functions | A 5-line JSDoc on a 2-line getter |
| Generic naming | Domain-agnostic names where domain terms exist | `handleData`, `processItem`, `doOperation` instead of `syncSkillManifest`, `resolveToolCall` |
| Boilerplate error handling | Identical try-catch blocks copied across files | Same toast + log pattern in 5 different handlers |
| Nosy debug logging | Entry/exit logs on every function, full object dumps | `log.debug('entering createTask', { ...allParams })` |
| Bare TODOs | `TODO`/`FIXME`/`HACK` without issue reference or context | `// TODO: fix this later` |

These are common AI-generated slop patterns. Every occurrence is a finding — no counterargument needed.

## Silent Failure Scan

Check new/modified files for error handling anti-patterns:

| Pattern | What to look for | Example |
|---------|-----------------|---------|
| Empty catch blocks | `catch` with no logging, no re-throw, no comment justifying suppression | `catch (e) {}` or `catch {}` with no body |
| Swallowed errors | Catch blocks that log but continue without re-throwing when the caller needs to know | `catch (e) { log.error('failed'); }` then returns default value |
| Broad exception catching | Catching all errors when only specific ones are expected, hiding unrelated failures | `catch (e)` around code that could throw for 5 different reasons |
| Silent fallbacks | Returning default/null on failure without logging or surfacing the error | `return null` in catch with no indication something failed |
| Missing error context | Error logs without enough context to debug (no IDs, no operation name, no input state) | `log.error('failed')` with no attributes |
| Fire-and-forget without catch | Promises with `.catch(() => {})` that discard errors that matter | `.catch(() => {})` on an operation whose failure should be visible |

Silent failures in IPC handlers, async flows, and error boundaries are especially painful in Electron — flag them with high confidence.
