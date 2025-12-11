# CHANGELOG.md

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Added** for new features. **Changed** for changes in existing functionality. **Deprecated** for soon-to-be removed features. **Removed** for now removed features. **Fixed** for any bug fixes. **Security** in case of vulnerabilities.

## [Unreleased] - yyyy-mm-dd

## [4.4.1] - 2025-12-11

### Added

- Support for Blender 5.0

### Changed

- Default game is now TM2020
- Allow negative offsets for grid/levitation in item
- More reliable method to open reports in browser

## [4.4.0] - 2025-11-12

### Added

- NICE: Display of warnings and errors directly in Blender (missing files, parsing errors)
- NICE: Import of mesh vertices color when available (e.g., triggerFX transparency, DecoHill alpha)

### Changed
- NICE: Compatibility with more items (e.g., TM2020 gates, ConvexPolyhedron surfaces, TM2 solids)
- Updated to blendermania-dotnet v1.0.0 (gbx.net v2)
- Map export now supports newer trackmania2020 map files

### Fixed

- NICE: Some material modifiers not being converted to Blendermania materials
- NICE: Import of mesh modeler item materials (previously imported only the first one)
- Map export will now return proper error codes and messages
- Potential crashes raised by exporting objects fixed by changing object conversion panel updates from threading to queue (bpy.app.timer)

### Removed

- Item.Gbx file import functionality handled by gbx.net removed, now handled by NICE
