# DUET CORE frontend

- Preserve FastAPI endpoints, payloads, RBAC and operational semantics. Backend changes require a documented, minimal, backward-compatible justification.
- The product is self-hosted. Do not add mandatory cloud services, analytics, CDNs or multitenancy assumptions.
- Keep UI copy in Brazilian Portuguese and preserve business terms. Never infer a final RPA state from request acceptance alone.
- Reuse semantic tokens from `frontend/src/styles/tokens.css`; support light, dark and system themes, keyboard focus, reduced motion and 320 px reflow.
- Keep server state inside domain hooks/services and interface state inside components. Render API/log content as untrusted text.
- Run `npm run lint`, `npm run build` and, with Vite running locally, `npm run test:visual` for shared-shell or responsive changes.
- Use `Button`/`IconButton`, `TextField`, `PremiumSelect`, semantic tokens and `useDialogFocus` for new or migrated interactive UI. Domain-specific controls may compose these primitives; do not create parallel generic button, field, select or modal behavior.
- Keep `/component-lab` development-only and free of operational data/actions. Run `npm run test:components` after changing shared controls, focus, themes or motion.
- Track route coverage, evidence and remaining validation in `docs/frontend-reconstruction.md`. A successful build is not proof of full product reconstruction or backend integration.
