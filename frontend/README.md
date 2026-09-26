# DUET Control Room — frontend

Interface React + TypeScript do Control Room.

## Configuração local

Por padrão, a interface usa o mesmo host acessado no navegador e a porta `9000`
para a API. Ambientes com proxy reverso ou outra topologia podem configurar:

```text
VITE_DUET_API_URL=https://control-room.exemplo.local/api
VITE_DUET_API_TIMEOUT_MS=60000
```

O timeout aceita valores entre 5 segundos e 5 minutos. O mesmo endereço base é
usado para derivar conexões WebSocket do Studio.

## Verificação

```bash
npm run lint
npm run build
npm run test:components
npm run test:visual
```

## Base técnica

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
