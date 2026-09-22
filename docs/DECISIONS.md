# Product decisions

## Scope

- Single-user local application.
- Streamlit chat as the primary interface.
- Profile and wardrobe files live outside the Git repository.
- No SQLite dependency in the first version.
- No OAuth, image recognition, cloud storage, or multi-user support.
- No chat history persistence.

## Context strategy

- Always load Profile and wardrobe from disk before a request.
- Send only a compact Profile summary by default.
- Read detailed facial and appearance data only when relevant.
- Send a compact wardrobe representation instead of the full YAML document.
- Use recent messages plus a short summary, never the full conversation.

## Weather and availability

- Weather is entered by the user in natural language.
- The assistant asks for missing weather or occasion when needed.
- Washing and temporary exclusions affect only the active conversation.
- The assistant regenerates recommendations when the user reports unavailable items.

## Data edits

- Chat can propose wardrobe additions, updates, and deletions.
- Chat cannot write files directly.
- The application shows a pending proposal and writes only after explicit confirmation.
- The previous wardrobe file is backed up before every write.
- Profile edits are made through the management page or direct file editing.

## LLM

- First provider: local `codex exec`.
- The current CC Switch / Codex provider and model are reused.
- Calls use an ephemeral session and read-only sandbox.
- The provider is isolated behind a service boundary so an HTTP API provider can be added later.
