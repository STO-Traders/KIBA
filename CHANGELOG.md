# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial context injection pipeline for workspace snapshot, git status, and `CLAUDE.md`
- Tests covering the new context system integration

### Changed
- Skill frontmatter parsing now supports inline list syntax such as `arguments: [path]`
- README and contributor docs now prefer `uv`-based setup instructions
- Documentation now distinguishes provider-level streaming interfaces from the current turn-based CLI output

## [1.2.1] - 2026-06-16

### Added
- `McpAuthTool` + token store: bearer and OAuth2 client-credentials auth for remote (http/sse) MCP servers; the manager injects `Authorization` headers on connect
- `/doctor` command: environment, dependency, provider/API-key, MCP, hooks, and tool-count diagnostics
- `/resume` command: list and reload previous sessions
- Model-aware token + USD cost tracking (`pricing.py`, `CostTracker.record_usage`, upgraded `/cost`); prices overridable via `~/.kiba/pricing.json`

### Fixed
- REPL launch crash: `provider_class` was referenced before assignment, crashing `kiba`/`kiba --stream` on startup with `NameError`
- Windows installer: replaced a non-ASCII em-dash that corrupted `install.ps1` under PowerShell's ANSI codepage; one-liner now refreshes PATH so `kiba` works in the same window
- macOS/Linux installer: ensure `~/.local/bin` is on PATH for new shells
- Crash on non-integer `KIBA_MAX_RETRIES` / `KIBA_MAX_TOKENS` (failed at import); now fall back to defaults
- Crash on corrupt/incomplete session files; `Session.load` now returns `None` gracefully
- `glm` provider now honors a configured `base_url` instead of always using the default endpoint
- `/doctor` / `/resume` now route and render correctly (status tags and metadata no longer swallowed by Rich markup; `/resume <id>` actually loads)
- `/load` re-points the active conversation; session IDs use microsecond precision to avoid same-second collisions
- `TaskGet` no longer `KeyError`s on background-subagent tasks; blank input is ignored instead of erroring

## [0.1.0] - 2026-04-01

### Added

#### Core Features
- Multi-provider support for Anthropic, OpenAI, and GLM (Zhipu AI)
- Interactive REPL with prompt-toolkit integration
- Rich interactive terminal output
- Session persistence and management
- Configuration management with basic API key obfuscation

#### CLI Commands
- `kiba` - Start the interactive REPL
- `kiba login` - Interactive API key configuration
- `kiba config` - View current configuration
- `kiba --version` - Show version information

#### Provider Implementations
- **Anthropic Provider**: Claude integration with chat + streaming interfaces
- **OpenAI Provider**: GPT integration with chat + streaming interfaces
- **GLM Provider**: GLM integration with chat + streaming interfaces

#### REPL Features
- Command history with persistent storage
- Auto-suggestions from history
- Slash commands: `/help`, `/exit`, `/clear`, `/save`, `/load`, `/multiline`
- Skill slash commands backed by `SKILL.md`
- Syntax highlighting with Rich library
- Tab completion and multi-line input support

#### Configuration System
- JSON-based configuration storage
- Base64-encoded API keys for basic obfuscation
- Provider-specific settings (API key, base URL, default model)
- Session auto-save option

#### Session Management
- Unique session ID generation
- Conversation history tracking
- Session save/load functionality
- Conversation clear operation

#### Code Quality
- Type hints for all public functions
- Abstract base class for provider implementations
- Data classes for structured data (ChatMessage, ChatResponse)
- Error handling and validation

#### Testing
- Unit tests for core components
- Integration tests for providers
- End-to-end tests for REPL functionality
- Test coverage for configuration management

### Technical Details

#### Architecture
- Modular provider system with base abstraction
- Conversation management with message history
- Configuration management layer
- REPL engine with prompt-toolkit

#### Dependencies
- `anthropic>=0.18.0` - Anthropic SDK
- `openai>=1.0.0` - OpenAI SDK
- `zhipuai>=2.0.0` - Zhipu AI SDK
- `prompt-toolkit>=3.0.0` - Interactive REPL
- `rich>=13.0.0` - Terminal formatting
- `python-dotenv>=1.0.0` - Environment variables

#### File Structure
```
src/
├── providers/          # LLM provider implementations
│   ├── base.py        # Abstract base class
│   ├── anthropic_provider.py
│   ├── openai_provider.py
│   └── glm_provider.py
├── repl/              # Interactive REPL
│   └── core.py
├── agent/             # Session management
│   ├── session.py
│   └── conversation.py
├── config.py          # Configuration management
└── cli.py             # CLI commands
```

### Known Limitations

- Context building is still in early MVP form and needs deeper project summarization
- Permission enforcement exists as a framework but is not fully integrated everywhere
- `/resume`, `/compact`, and `/doctor` are not implemented yet
- The current CLI uses turn-based output even though providers expose streaming interfaces

### Migration Notes

This is the initial MVP release. No migration needed.

### Future Roadmap

- [ ] Context enrichment and project-memory improvements
- [ ] Full permission integration
- [ ] `/resume`, `/compact`, `/doctor`
- [ ] Token usage and cost tracking
- [ ] MCP and plugin-system enhancements

---

## Release Notes

### v0.1.0 - MVP Release

This is the first public release of KIBA, an agentic AI coding platform for the terminal. This MVP includes:

- Full multi-provider support
- Interactive REPL
- Session management
- Configuration system
- Tool system and agent loop foundations
- Type-safe implementation

The focus was on building a solid foundation with clean architecture, comprehensive testing, and good developer experience. All core features are working and tested.

---

[1.2.1]: https://github.com/STO-Traders/KIBA/releases/tag/v1.2.1
[0.1.0]: https://github.com/STO-Traders/KIBA/releases/tag/v0.1.0
