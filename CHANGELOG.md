# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-10-10

### Added

- Case-insensitive extension filtering for file downloads.
- New command-line argument (`--extensions`) to specify file extensions for filtering.
- Added detailed debug messages for extension handling and file processing.
- Normalization of allowed extensions to lowercase.
- Improved file extension comparison logic to ensure correct processing.

### Fixed

- Fixed an issue where files with valid extensions (like `.zip`) were not being downloaded.
- Correct handling of user-specified file extensions with case insensitivity.
- Improved error handling for missing file names and unsupported media types.

## [1.1.0] - 2024-08-21

### Changed

- The single quote characters are removed from file_name.

### Fixed

- Handling `DocumentAttributeAnimated` and other attributes without `file_name`.
- Error handling.
- Connection retries handling.

## [1.0.0] - 2024-08-21

### Added

- Initial release with basic functionality to list and download files from a Telegram channel.
- Structured JSON output to include the channel name as the root key.
- Initial version of Telegram File Exporter.
- Command-line interface with options for API credentials, channel, mode, and more.
