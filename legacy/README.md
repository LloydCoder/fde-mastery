# Legacy curriculum boundary

The `month-1-cybersecurity` through `month-6-revops` directories are preserved as historical curriculum and compatibility material. They are not platform dependencies.

## Rules

1. New platform code lives under `fde_platform/`, `domains/`, and future `apps/` / infrastructure boundaries.
2. Production code must not import `month-*` curriculum modules.
3. Compatibility adapters may reference legacy behavior only behind an explicit adapter boundary.
4. New capabilities must not be implemented by modifying a month directory unless the change is specifically a curriculum maintenance task.
5. The architecture tests enforce the no-direct-import rule.

This boundary lets the repository retain its learning history while preventing legacy structure from becoming an architectural dependency.
