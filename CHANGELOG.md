# [1.5.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.4.0...v1.5.0) (2026-02-23)


### Bug Fixes

* update error message in tests to include PAT authentication ([8a50af6](https://github.com/mbabic84/ainstruct-mcp/commit/8a50af6f346a905ce7f9aceb333e52b4e588c2a2))


### Features

* add Personal Access Tokens (PAT) for long-lived auth ([83c0d46](https://github.com/mbabic84/ainstruct-mcp/commit/83c0d46e439155a3c42ca4681cb0ad7652f6cc83))

# [1.4.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.3.0...v1.4.0) (2026-02-23)


### Features

* migrate to Alpine base image for SQLite 3.51.2 security fix ([7692bcd](https://github.com/mbabic84/ainstruct-mcp/commit/7692bcd8f9a788f95aec10c8417f5d0422261161))

# [1.3.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.2.0...v1.3.0) (2026-02-23)


### Bug Fixes

* auth middleware bugs and add test infrastructure ([8300b90](https://github.com/mbabic84/ainstruct-mcp/commit/8300b90784cfb5eb2ca5ead76854bc4c5d6ac2b9))
* correct semantic-release sed pattern and pyproject.toml ([1c7d2dd](https://github.com/mbabic84/ainstruct-mcp/commit/1c7d2dd07c1b24b56b3af18a67b8b4dc079e7cec))
* exclude integration tests from unit test container ([d3863b9](https://github.com/mbabic84/ainstruct-mcp/commit/d3863b9e53371993539ac00fcc9d8f6d0642c969))
* remove trailing whitespace in auth middleware ([cf0cf17](https://github.com/mbabic84/ainstruct-mcp/commit/cf0cf17081c9bbda6960d07448d4479503aa2654))
* use Python script for robust version updates in semantic-release ([4a80269](https://github.com/mbabic84/ainstruct-mcp/commit/4a80269c7b39803748c6046f9dee1a4068e7c114))
* use separate test service without volume mount for integration tests ([a29524e](https://github.com/mbabic84/ainstruct-mcp/commit/a29524e57c004e63e48b7db04ef4dd7afa8e84a2))


### Features

* **ci:** add integration tests job to test workflow ([1893aba](https://github.com/mbabic84/ainstruct-mcp/commit/1893aba5e847bd4a431fba0261cb30fad6caf950))

# [1.2.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.1.0...v1.2.0) (2026-02-22)


### Bug Fixes

* create data directory in Docker and fix missing mock in test ([6f3433c](https://github.com/mbabic84/ainstruct-mcp/commit/6f3433cfdcc3559fdbbc3b41c8305fd460531054))
* use Docker for consistent testing and fix type errors ([f5bcab4](https://github.com/mbabic84/ainstruct-mcp/commit/f5bcab403d453e86fbaa8ce44a82893581cc0b9e))


### Features

* add user authentication, API keys, and collections ([7a7898c](https://github.com/mbabic84/ainstruct-mcp/commit/7a7898cd8aa8259e4e4af1436e6f03a6e26a3e1e))

# [1.1.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.0.0...v1.1.0) (2026-02-22)


### Bug Fixes

* correct ruff target-version and mypy python_version ([4385e6d](https://github.com/mbabic84/ainstruct-mcp/commit/4385e6d5a56931c9a6aa918df02de9f7a3e8bba2))
* use version_toml for precise pyproject.toml version replacement ([aab70bd](https://github.com/mbabic84/ainstruct-mcp/commit/aab70bdd3669d0d02c1f5270685cc72ec212a85d))


### Features

* add update_document tool for modifying stored documents ([3c34b97](https://github.com/mbabic84/ainstruct-mcp/commit/3c34b97f164e48bcfcbc0436184aebe0d8271bc3))

# 1.0.0 (2026-02-21)


### Bug Fixes

* enable test workflow as reusable and fix release trigger ([4525e81](https://github.com/mbabic84/ainstruct-mcp/commit/4525e813de7b8ffde0ecdf7aec98804b7dbc08bc))
* install semantic-release plugins globally ([5cfbb1c](https://github.com/mbabic84/ainstruct-mcp/commit/5cfbb1c238bd13a804fe0799641f0cfecafdfdda))
* proper SQLAlchemy 2.0 type annotations and mypy config ([beef4a7](https://github.com/mbabic84/ainstruct-mcp/commit/beef4a7d61cf7c76370383f3c5e44a01a4d05335))
* resolve linting errors and fix workflow ([6da26d2](https://github.com/mbabic84/ainstruct-mcp/commit/6da26d2f34ed7ba5a55fa5e83f4d362919a9ecb6))
* update GitHub Actions workflow to Python 3.14 ([217fe22](https://github.com/mbabic84/ainstruct-mcp/commit/217fe2210e82cc2341869ab4d1029fc5831bcfc5))


### Features

* implement semantic-release for automated versioning and docker publishing ([c519d84](https://github.com/mbabic84/ainstruct-mcp/commit/c519d84ad7a951d09d56393e5b6ec32c02572c94))
* upgrade to Python 3.14 and latest dependencies ([2c11601](https://github.com/mbabic84/ainstruct-mcp/commit/2c11601893d32f78f57c21ae8d257002601d79b9))
