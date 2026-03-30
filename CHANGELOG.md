# Changelog

## [1.1.0] - 2026-03-30

### Fixed
- Plugin structure: moved references/ into skills/infostyle/ (correct relative paths when installed via marketplace)
- Removed duplicate root SKILL.md (single source: skills/infostyle/SKILL.md)
- eval/score.py: stop-word check now scoped to "Отредактированный текст" section only (was checking entire response)
- eval/score.py: added missing brevity cases (30, 32) to BREVITY_CASES; removed case 47 (chatbot = medium, not brevity)
- eval/run.md: fixed case count (56, not 10) and removed hardcoded absolute path
- Aligned naming: marketplace = infostyle-skill, plugin = infostyle

### Added
- English trigger keywords in SKILL.md description for better auto-discovery
- ${CLAUDE_SKILL_DIR} for reference file paths (portable across installs)
- Short-text threshold: texts < 10 words skip context questions
- Fallback install instructions in README
- CHANGELOG.md
- GitHub topics for discoverability
- Badges in README (MIT, Claude Code Compatible)

## [1.0.0] - 2026-03-30

### Added
- Initial release
- 7-step editing workflow based on Ilyakhov's methodology
- 5 reference files: stop-words, text-types, scoring, manipulation-patterns, examples
- 56 test cases with mechanical scoring (eval/)
- Plugin manifest and marketplace support
