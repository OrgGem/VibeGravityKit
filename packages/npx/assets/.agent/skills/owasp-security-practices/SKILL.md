---
name: owasp-security-practices
description: "OWASP Top 10 security best practices for web applications. Use when implementing security controls, reviewing code for vulnerabilities, or ensuring OWASP compliance."
user-invocable: true
risk: safe
---

# OWASP Security Practices

Implement OWASP Top 10 security controls in web applications — prevention patterns, secure code examples, and compliance checks.

## When to Use
- Reviewing code for common web vulnerabilities
- Implementing authentication and authorization securely
- Handling user input, file uploads, or database queries
- Security audit before deployment or penetration testing

## OWASP Top 10 (2021) Prevention

### A01: Broken Access Control
```ts
// Always authorize on server — never trust client-side checks
async function getDocument(req: Request, docId: string) {
  const doc = await db.document.findUnique({ where: { id: docId } })
  if (!doc || doc.ownerId !== req.user.id) {
    throw new ForbiddenError()  // Don't reveal existence — return 403 or 404
  }
  return doc
}

// Use allowlist for IDOR protection
const ALLOWED_FIELDS = ['name', 'email', 'bio']
const safeUpdate = pick(userInput, ALLOWED_FIELDS)
```

### A02: Cryptographic Failures
```ts
// Passwords — use bcrypt/argon2, never MD5/SHA1
import bcrypt from 'bcrypt'
const hash = await bcrypt.hash(password, 12)  // min cost factor: 10

// Sensitive data — encrypt at rest
import crypto from 'crypto'
const encrypted = crypto.createCipheriv('aes-256-gcm', key, iv)

// Use HTTPS everywhere — HSTS header
res.setHeader('Strict-Transport-Security', 'max-age=63072000; includeSubDomains')
```

### A03: Injection
```ts
// SQL — always use parameterized queries or ORM
// BAD: db.query(`SELECT * FROM users WHERE email = '${email}'`)
// GOOD:
await db.query('SELECT * FROM users WHERE email = $1', [email])
await prisma.user.findUnique({ where: { email } })

// Command injection — never pass user input to shell
// BAD: exec(`convert ${filename} output.pdf`)
// GOOD: Use library APIs or strict allowlist validation
const safe = /^[a-zA-Z0-9_-]+\.[a-zA-Z]{2,4}$/.test(filename)
```

### A04: Insecure Design
- Threat model before building — identify trust boundaries
- Rate limit all authentication endpoints
- Implement account lockout after N failed attempts
- Never trust client-provided user IDs or roles

### A05: Security Misconfiguration
```ts
// Remove stack traces from production errors
app.use((err, req, res, next) => {
  console.error(err)
  res.status(500).json({ error: 'Internal server error' })  // No err.stack!
})

// Security headers (use helmet.js)
import helmet from 'helmet'
app.use(helmet())
// Sets: X-Content-Type-Options, X-Frame-Options, CSP, etc.
```

### A06: Vulnerable Components
```bash
# Audit dependencies regularly
npm audit
pip-audit
trivy image myapp:latest

# Automate with Dependabot or Renovate
```

### A07: Authentication Failures
```ts
// JWT — verify signature and expiry
import jwt from 'jsonwebtoken'
const payload = jwt.verify(token, process.env.JWT_SECRET!)  // Throws on invalid

// Session — use secure, httpOnly cookies
res.cookie('sessionId', id, {
  httpOnly: true,   // No JS access
  secure: true,     // HTTPS only
  sameSite: 'strict', // CSRF protection
  maxAge: 24 * 60 * 60 * 1000
})
```

### A08: Software and Data Integrity
- Verify checksums for downloaded assets
- Sign deployments and Docker images
- Use Content Security Policy to prevent XSS
- Validate webhook signatures before processing

### A09: Logging & Monitoring Failures
```ts
// Log security events (never log secrets/passwords)
logger.warn({
  event: 'auth.failed',
  ip: req.ip,
  userId: userId,
  reason: 'invalid_password'
  // NEVER: password: req.body.password
})
```

### A10: Server-Side Request Forgery (SSRF)
```ts
// Validate URLs before fetching
function isSafeUrl(url: string): boolean {
  const parsed = new URL(url)
  const blocked = ['localhost', '127.0.0.1', '169.254.169.254', '::1']
  return !blocked.includes(parsed.hostname) && parsed.protocol === 'https:'
}
```

## Quick Security Checklist
- [ ] All inputs validated and sanitized (use Zod/Joi)
- [ ] Parameterized queries everywhere
- [ ] Passwords hashed with bcrypt/argon2
- [ ] JWT secrets rotatable, stored in env vars
- [ ] Rate limiting on auth endpoints
- [ ] Security headers set (helmet)
- [ ] Dependencies audited (`npm audit`)
- [ ] Errors don't expose stack traces in production
- [ ] HTTPS enforced with HSTS
- [ ] CORS configured with explicit allowlist
