# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-08-21

### Changed

- The singe quote characters are removed from file_name

### Fixed

- Handling DocumentAttributeAnimated and other attributes without file_name
- Error handling
- Connection retries handling

## [1.0.0] - 2024-08-21

### Added

- Initial release with basic functionality to list and download files from a Telegram channel.
- Structured JSON output to include the channel name as the root key.
- Initial version of Telegram File Exporter.
- Command-line interface with options for API credentials, channel, mode, and more.
