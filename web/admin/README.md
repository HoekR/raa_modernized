# RAA editorial admin (`web/admin`)

Separate SvelteKit app for corpus editing (Milestone E). Not the public search UI.

Configure the API key in repo root **`config.local.toml`**:

```toml
[editorial]
enabled = true
api_key = "your-secret"
```

Then:

```bash
cd web/admin && npm install && npm run dev   # http://localhost:5174
```

Log in with the same `api_key` value. Requires API on `:8000`. See [docs/EDITORIAL.md](../../docs/EDITORIAL.md). Team demo checklist: [docs/EDITORIAL_DEMO.md](../../docs/EDITORIAL_DEMO.md).
