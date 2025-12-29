# Security

## 2025 Secure-by-Default Standards

- ✅ Compiled with Nuitka (machine code, not bytecode)
- ✅ No hardcoded secrets (`.env` configuration)
- ✅ Input validation (allowlist approach)
- ✅ Secure subprocess calls (no shell injection)
- ✅ AES-256 encryption at rest
- ✅ Hardened error handling

## Configuration

Never commit `.env`:

```bash
cp env.example .env
# Edit .env with your secrets
```

## Reporting Issues

Email: security@yourcompany.com
