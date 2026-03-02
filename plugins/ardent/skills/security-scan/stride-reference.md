# STRIDE Reference — Electron + React + TypeScript + Cloudflare Workers

Vulnerability patterns organized by STRIDE category, tailored for this stack.

## S — Spoofing Identity

### Electron IPC
- Renderer process impersonating a different window/webContents via `ipcMain.handle`
- Missing sender validation in IPC handlers (`event.senderFrame`, `event.sender.id`)
- Preload script exposing overly broad APIs via `contextBridge`

### API (Cloudflare Workers)
- Weak session/token validation
- JWT vulnerabilities (none algorithm, weak secrets, missing expiry checks)
- API key exposure in client-side code or logs
- Missing authentication on sensitive endpoints

### Patterns to detect
```typescript
// VULNERABLE — no sender validation
ipcMain.handle('sensitive-action', async (_event, data) => { ... })

// SAFER — validate sender
ipcMain.handle('sensitive-action', async (event, data) => {
  if (event.senderFrame.url !== expectedUrl) throw new Error('unauthorized');
  ...
})
```

## T — Tampering with Data

### SQL Injection (D1)
```typescript
// VULNERABLE
const result = await db.prepare(`SELECT * FROM users WHERE id = ${userId}`).all()

// SAFE
const result = await db.prepare('SELECT * FROM users WHERE id = ?').bind(userId).all()
```

### Command Injection
```typescript
// VULNERABLE
exec(`deno run ${userScript}`)

// SAFER
execFile('deno', ['run', '--', userScript])
```

### XSS
```tsx
// VULNERABLE
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// SAFE — React auto-escapes
<div>{userContent}</div>
```

### Path Traversal
```typescript
// VULNERABLE
const filePath = path.join(uploadsDir, userFilename)

// SAFER
const safeName = path.basename(userFilename)
const filePath = path.join(uploadsDir, safeName)
if (!filePath.startsWith(uploadsDir)) throw new Error('path traversal')
```

### Mass Assignment
```typescript
// VULNERABLE — blindly spreading request body into DB update
await db.prepare('UPDATE users SET ?').bind(req.body).run()

// SAFER — explicit field selection
const { name, email } = req.body
await db.prepare('UPDATE users SET name = ?, email = ?').bind(name, email).run()
```

### Electron-specific
- `nodeIntegration: true` in BrowserWindow (allows renderer to access Node.js APIs)
- `contextIsolation: false` (allows renderer to modify preload globals)
- `webSecurity: false` (disables same-origin policy)
- Loading remote content with elevated privileges
- `shell.openExternal` with unvalidated URLs

```typescript
// VULNERABLE
shell.openExternal(userProvidedUrl)

// SAFER
const parsed = new URL(userProvidedUrl)
if (['https:', 'http:'].includes(parsed.protocol)) {
  shell.openExternal(userProvidedUrl)
}
```

## R — Repudiation

- Missing audit logs for sensitive operations (account changes, data deletion, permission changes)
- Insufficient logging of admin/elevated actions
- No immutable audit trail for compliance-relevant operations

## I — Information Disclosure

### IDOR
```typescript
// VULNERABLE — no ownership check
app.get('/api/documents/:id', async (c) => {
  return c.json(await db.getDocument(c.req.param('id')))
})

// SAFER — verify ownership
app.get('/api/documents/:id', async (c) => {
  const doc = await db.getDocument(c.req.param('id'))
  if (doc.userId !== c.get('userId')) return c.json({ error: 'not found' }, 404)
  return c.json(doc)
})
```

### Secrets exposure
- Hardcoded API keys, passwords, tokens in source code
- Secrets in client-side bundles (Vite exposes `VITE_*` env vars to the browser)
- Sensitive data in error messages or stack traces sent to client
- PII in log output

### Electron-specific
- DevTools enabled in production builds
- `webContents.openDevTools()` without environment check
- Sensitive data in localStorage/sessionStorage accessible to renderer

## D — Denial of Service

- Missing rate limiting on API endpoints
- Unbounded file uploads
- Regex DoS (ReDoS) — catastrophic backtracking in user-controlled regex
- Unbounded database queries (missing LIMIT/pagination)
- Resource exhaustion via IPC flooding

## E — Elevation of Privilege

### API
- Missing authorization checks on endpoints (authn != authz)
- Role/permission bypass via parameter manipulation
- Privilege escalation through mass assignment of role fields

### Electron
- Renderer process gaining main process access
- Bypassing contextBridge restrictions
- Preload script exposing sensitive main-process APIs
- `webContents.executeJavaScript` with untrusted input

### Cloudflare Workers
- Missing middleware for auth/authz on route groups
- Direct D1 access bypassing authorization layer

## CWE Quick Reference

| Vulnerability | CWE |
|---------------|-----|
| SQL Injection | CWE-89 |
| Command Injection | CWE-78 |
| XSS | CWE-79 |
| Path Traversal | CWE-22 |
| IDOR | CWE-639 |
| Missing Authentication | CWE-306 |
| Missing Authorization | CWE-862 |
| Hardcoded Credentials | CWE-798 |
| Sensitive Data Exposure | CWE-200 |
| Mass Assignment | CWE-915 |
| Open Redirect | CWE-601 |
| SSRF | CWE-918 |
| Insecure Deserialization | CWE-502 |
| Improper Input Validation | CWE-20 |
