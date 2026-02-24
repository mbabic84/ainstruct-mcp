## [1.6.5](https://github.com/mbabic84/ainstruct-mcp/compare/v1.6.4...v1.6.5) (2026-02-24)


### Bug Fixes

* add migration for missing expires_at column and pat_tokens table ([2e7bc0a](https://github.com/mbabic84/ainstruct-mcp/commit/2e7bc0a6a0efabcaf4a6bd05c0362c729baa1e1d))

## [1.6.4](https://github.com/mbabic84/ainstruct-mcp/compare/v1.6.3...v1.6.4) (2026-02-24)


### Bug Fixes

* check for user_id column before querying api_keys table ([6c65311](https://github.com/mbabic84/ainstruct-mcp/commit/6c65311fd7bce39801d322a5904911f6a484a647))

## [1.6.3](https://github.com/mbabic84/ainstruct-mcp/compare/v1.6.2...v1.6.3) (2026-02-24)


### Bug Fixes

* defer embedding service init to after doc existence check ([3bc5fdc](https://github.com/mbabic84/ainstruct-mcp/commit/3bc5fdce0d99a1503f556a43b0bd4093f60bef4b))
* handle error string responses in E2E tests ([7fda5fa](https://github.com/mbabic84/ainstruct-mcp/commit/7fda5faacc8d079f7129c3eb411bcc694de6b112))
* handle missing columns in migration and reorganize tests ([ba28bc2](https://github.com/mbabic84/ainstruct-mcp/commit/ba28bc25974086572e7b6cee55ee415586340622))
* resolve mypy type errors for collection lookup and user_profile ([b7b47ae](https://github.com/mbabic84/ainstruct-mcp/commit/b7b47ae7b9e4b2483958fa4e97f1f8e5e8345553))
* resolve PAT token auth and read-only key permission issues ([60f983f](https://github.com/mbabic84/ainstruct-mcp/commit/60f983f5e0b63d28e0c4ef6a501e6388d7eabfb2))
* update e2e test configuration for new test structure ([8eaad00](https://github.com/mbabic84/ainstruct-mcp/commit/8eaad0073d796efedd17adc0629daa9c09fee218))

## [1.6.2](https://github.com/mbabic84/ainstruct-mcp/compare/v1.6.1...v1.6.2) (2026-02-23)


### Bug Fixes

* wire up PAT token tools in MCP server ([725a465](https://github.com/mbabic84/ainstruct-mcp/commit/725a465a1b97dc09426f6c514da9b0b507e7949d))

## [1.6.1](https://github.com/mbabic84/ainstruct-mcp/compare/v1.6.0...v1.6.1) (2026-02-23)


### Bug Fixes

* make migrations idempotent for existing databases ([d8ae5bd](https://github.com/mbabic84/ainstruct-mcp/commit/d8ae5bd6e0b7ccf46dc5fa6f552b5e2e4628ed40))

# [1.6.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.5.0...v1.6.0) (2026-02-23)


### Bug Fixes

* include alembic files in Docker image for migrations ([9d49f97](https://github.com/mbabic84/ainstruct-mcp/commit/9d49f977690ba7d96cfae894a541b99dadd901f2))
* remove PAT code incorrectly merged from main ([6d1e99e](https://github.com/mbabic84/ainstruct-mcp/commit/6d1e99e2923d33fa608b1fd378e3055a3c62f46e))


### Features

* add automatic database migrations on server startup ([7589395](https://github.com/mbabic84/ainstruct-mcp/commit/7589395e9cbac5beafc2aa6fbeb9362d53ffe0aa))

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
