# Final security audit — GREEN (see docs/security/audit.md)
Env secrets, ORM-only access, validated I/O, CORS-locked, untrusted feed/LLM
handling with adversarial tests, intervention allow-list, no PII. Limitation:
rate limiting delegated to reverse proxy.
