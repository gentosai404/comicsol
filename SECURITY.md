# Security Policy

## Supported versions

The latest published prerelease or stable release receives security fixes. Older release candidates may be superseded without backports.

## Reporting a vulnerability

Do not open a public issue for a vulnerability, leaked credential, unsafe archive behavior, path-containment bypass, arbitrary file write, or dependency compromise.

Use GitHub's private vulnerability reporting for `wenn-id/comic-sol-lab` when available. If that interface is unavailable, contact the repository owner privately through the contact method shown on the owner's GitHub profile and include:

- affected version or commit;
- reproduction steps and impact;
- operating system and installation method;
- whether credentials or private project data may have been exposed;
- any proposed mitigation.

Do not include live secrets. Revoke exposed credentials before reporting and replace values with `[REDACTED]`.

## Scope

Security-sensitive areas include project path containment, archive extraction, transactional configuration writes, provider metadata sanitization, release checksums, bundled runtimes, MCP output-root isolation, and generated artifact validation.

Comic Sol does not bundle image-provider credentials or send data by itself. When an agent invokes an external image capability, that provider's privacy and retention policy applies.
