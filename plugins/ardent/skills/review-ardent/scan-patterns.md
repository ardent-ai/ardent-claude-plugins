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
| Per-consumer structural types | Bespoke structural types that carve out the subset of a service each consumer uses, instead of depending on the real type directly | `type FooDatabase = { memories: { listBy(...): ... } }` — depend on `ElectronDatabase` directly; tests can stub unused methods |

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

## Dead Surface / Indirection Scan

Check new/modified files for unnecessary API surface and indirection:

| Pattern | What to look for | Example |
|---------|-----------------|---------|
| Identity type aliases | Type alias that equals another type with no added fields | `type SaveParams = UpdateParams;` — just use `UpdateParams` |
| Dead public methods | Public methods only called internally or from tests, never by production consumers | `registerSkill()` is public but only `saveSkill()` calls it — make it private |
| Stale barrel exports | Barrel `index.ts` exports types that no consumer imports, or consumers bypass the barrel to import types not in it | `index.ts` exports `FooParams` but the only consumer imports `BarParams` directly from the source file |
| Redundant pre-checks | Check-then-act patterns where the act already handles the check (TOCTOU) | `access(path)` before `copyFile(path)` — copyFile already throws ENOENT |
| Duplicate fields across types | Two types sharing 4+ fields where one could extend or reference the other, or one could be passed directly | `RestoreState` duplicates `backupPath, finalPath, skillId` from `SaveContext` — pass the context instead |
| Positional params from an existing object | Method takes 3+ positional params that are already fields on a params object the caller has | `writeFiles(path, a, b, c)` where `a, b, c` come from `params` — pass `params` |

These compound — a class with 3+ of these patterns has a real indirection problem. Use verification rule #7 (accumulate related smells) to cluster them into a single finding.
