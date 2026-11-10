# Security Policy for This Learning Repository

**This repository is educational and not production-ready.**

- Never commit model credentials, secrets, unredacted user data, real account records, or raw sensitive trajectories.
- Every side-effecting tool must have an explicit authorization and (if high-risk) human approval boundary.
- No arbitrary code execution outside an isolated sandbox with resource limits and network controls.
- The SQLite approval demo is not a substitute for authenticated payment authorization.
- Treat tool output and retrieved text as untrusted data, never as higher-priority instructions.

Report security problems privately to the maintainer using GitHub's security-advisory mechanism if enabled.
