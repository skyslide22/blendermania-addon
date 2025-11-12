# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Added** for new features. **Changed** for changes in existing functionality. **Deprecated** for soon-to-be removed features. **Removed** for now removed features. **Fixed** for any bug fixes. **Security** in case of vulnerabilities.

## [4.4.0] - 2025-11-12

### Added
- **NICE:** Display of warnings and errors directly in Blender (missing files, parsing errors)
- **NICE:** Import of mesh vertices color when available (e.g., triggerFX transparency, DecoHill alpha)

### Changed
- **NICE:** Compatibility with more items (e.g., TM2020 gates, ConvexPolyhedron surfaces, TM2 solids)

### Fixed
- **NICE:** Some material modifiers not being converted to Blendermania materials
- **NICE:** Import of mesh modeler item materials (previously imported only the first one)
