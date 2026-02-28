## [3.11.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.11.0...v3.11.1) (2026-02-28)


### Bug Fixes

* **web-ui:** add automatic token refresh and auto-detect API hostname ([4a965f9](https://github.com/mbabic84/ainstruct-mcp/commit/4a965f9014035209345768ae8b6a3a584b675962))

# [3.11.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.10.1...v3.11.0) (2026-02-28)


### Features

* improve login page with centered form, validation and remember me checkbox ([0747e42](https://github.com/mbabic84/ainstruct-mcp/commit/0747e428ee869f0f5cf5ebd3b53122870bd81c3c))

## [3.10.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.10.0...v3.10.1) (2026-02-28)


### Bug Fixes

* resolve tokens page CAT dropdown issues and api response field ([c642397](https://github.com/mbabic84/ainstruct-mcp/commit/c6423975a79b81ed1b20be10ee533d10be647cf3))

# [3.10.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.9.0...v3.10.0) (2026-02-27)


### Features

* add web-ui dashboard service ([1cb9ce9](https://github.com/mbabic84/ainstruct-mcp/commit/1cb9ce9341928cff3c7538e793f41921df8fbef5))

# [3.9.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.8.1...v3.9.0) (2026-02-27)


### Bug Fixes

* add blank line between import sections in mcp_server/__init__.py ([ef23ebb](https://github.com/mbabic84/ainstruct-mcp/commit/ef23ebb87383f9db112b3d7982521d93ac4c97e7))


### Features

* enable stateless mode for streamable-http transport ([a9df1e0](https://github.com/mbabic84/ainstruct-mcp/commit/a9df1e039301b3e02b957a124d588b178123a155))

## [3.8.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.8.0...v3.8.1) (2026-02-27)


### Bug Fixes

* allow promote user regardless of existing admins ([2699ea7](https://github.com/mbabic84/ainstruct-mcp/commit/2699ea78a8d98d88f771b1bbb4e593b89ac46b75))

# [3.8.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.7.0...v3.8.0) (2026-02-27)


### Features

* remove MCP tools with REST equivalents ([c642c64](https://github.com/mbabic84/ainstruct-mcp/commit/c642c64726c2df0d072bcdb1ae56563a9ad92668))

# [3.7.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.6.0...v3.7.0) (2026-02-27)


### Bug Fixes

* add /health endpoint and fix docker production runtime ([86fe92d](https://github.com/mbabic84/ainstruct-mcp/commit/86fe92d4c7883e720c41f87db7dbc5f0dc7cfcff))
* add deploy/ to gitignore and add PRODUCTION.md ([a67c82c](https://github.com/mbabic84/ainstruct-mcp/commit/a67c82ca71f50351dcb7c7395476fa8d59fac91c))


### Features

* add promote user to admin endpoint ([75c9e92](https://github.com/mbabic84/ainstruct-mcp/commit/75c9e92dbdc45d4f8503b0bd4727c4a0a69ff81d))

## [3.6.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.6.0...v3.6.1) (2026-02-27)


### Bug Fixes

* add /health endpoint and fix docker production runtime ([86fe92d](https://github.com/mbabic84/ainstruct-mcp/commit/86fe92d4c7883e720c41f87db7dbc5f0dc7cfcff))
* add deploy/ to gitignore and add PRODUCTION.md ([a67c82c](https://github.com/mbabic84/ainstruct-mcp/commit/a67c82ca71f50351dcb7c7395476fa8d59fac91c))

## [3.6.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.6.0...v3.6.1) (2026-02-26)


### Bug Fixes

* add /health endpoint and fix docker production runtime ([eec3004](https://github.com/mbabic84/ainstruct-mcp/commit/eec300463120ea59eebb196223ef610859cbfa69))

# [3.6.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.5.0...v3.6.0) (2026-02-26)


### Features

* add PORT env var support for MCP server ([d8f426e](https://github.com/mbabic84/ainstruct-mcp/commit/d8f426e4f677b5b10b558d43ce6a19f38fca406f))

# [3.5.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.4.1...v3.5.0) (2026-02-26)


### Bug Fixes

* complete PostgreSQL migration and fix scope handling ([595100a](https://github.com/mbabic84/ainstruct-mcp/commit/595100abcbbc2813f72811fc0be66c44ada3ff94))


### Features

* migrate from SQLite to PostgreSQL with async support ([ea5532b](https://github.com/mbabic84/ainstruct-mcp/commit/ea5532b4da9c6ce5de59ec3a64559d86c873fab3))

## [3.4.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.4.0...v3.4.1) (2026-02-26)


### Bug Fixes

* ensure data directory has correct permissions in Docker images ([48b55c6](https://github.com/mbabic84/ainstruct-mcp/commit/48b55c68c24bb5d541645daeb18e79ac341949ac))
* remove user_id from CollectionResponse models ([d05e943](https://github.com/mbabic84/ainstruct-mcp/commit/d05e9439ac127ee6c28bd30b81dc53bcc563b8f6))
* resolve linting issues in REST API routes ([c767395](https://github.com/mbabic84/ainstruct-mcp/commit/c767395520fbe07cc8a3e113970408a8f094996b))
* resolve mypy type errors in REST API and models ([bfc3874](https://github.com/mbabic84/ainstruct-mcp/commit/bfc38746557eb375cd443dcb8f5ad1eaacb93ea7))
* restore E2E test dependencies in docker-compose ([8f4727e](https://github.com/mbabic84/ainstruct-mcp/commit/8f4727e164a500e6a84fcdfcd12767942dd35633))

# [3.4.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.3.0...v3.4.0) (2026-02-25)


### Features

* implement REST API with JWT authentication ([9eb98d7](https://github.com/mbabic84/ainstruct-mcp/commit/9eb98d72f784d8414909660c769ac3ab9ce42bc4))

# [3.3.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.2.2...v3.3.0) (2026-02-25)


### Bug Fixes

* admin delete test - mock delete not get_by_id ([93134aa](https://github.com/mbabic84/ainstruct-mcp/commit/93134aa1373f6f3287ee55527bb1d33ebce165ad))
* remaining test failures ([c680e9f](https://github.com/mbabic84/ainstruct-mcp/commit/c680e9fe80d458d70bd9ff403a85e8948f6f30ab))
* remove production URL fallback from e2e tests ([5568a8a](https://github.com/mbabic84/ainstruct-mcp/commit/5568a8a46b56502177798dd5a924b199017a1103))
* remove rollback assertions from error handling tests ([b8aae5e](https://github.com/mbabic84/ainstruct-mcp/commit/b8aae5e066e85f603477b5cf6a0c525b0a529622))
* restore TRANSPORT default, keep SERVER_URL required ([b9bf2b2](https://github.com/mbabic84/ainstruct-mcp/commit/b9bf2b2496b13bb8a7183487d241bc7e7720bfaf))
* update collection validation and document error handling tests ([d4dc985](https://github.com/mbabic84/ainstruct-mcp/commit/d4dc985c055ee452bc6489c8aef30f99f6efef8c))
* update document error handling tests for async mocks ([da84196](https://github.com/mbabic84/ainstruct-mcp/commit/da841968955090c28ee30ca4cbc6e15ec71c6d3e))
* update document error handling tests for rollback behavior ([168675e](https://github.com/mbabic84/ainstruct-mcp/commit/168675e14784a51b05133a6b59e8973a1bbc1b84))
* update e2e admin tests and collection validation tests ([4dccbcf](https://github.com/mbabic84/ainstruct-mcp/commit/4dccbcf12adc5ca9fb3106fc1f5f08d959ad6a06))
* update unit tests for JWT auth changes and mock improvements ([e2fe6bd](https://github.com/mbabic84/ainstruct-mcp/commit/e2fe6bd42cf555960a44689553a0a973c6a31cef))


### Features

* add move_document tool and fix JWT auth for document tools ([652d328](https://github.com/mbabic84/ainstruct-mcp/commit/652d3280ae161c9dece0d9bdfa0138f4697e9c01))

## [3.2.2](https://github.com/mbabic84/ainstruct-mcp/compare/v3.2.1...v3.2.2) (2026-02-24)


### Bug Fixes

* add cascade delete to ORM relationships ([b21a0ee](https://github.com/mbabic84/ainstruct-mcp/commit/b21a0ee3bf84cda52a642ebbc142cede20097e2a))

## [3.2.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.2.0...v3.2.1) (2026-02-24)


### Bug Fixes

* secure search_users_tool and fail closed for unknown tools ([967ee37](https://github.com/mbabic84/ainstruct-mcp/commit/967ee371a78432a26686bc1e1cce0479a586e132))

# [3.2.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.1.1...v3.2.0) (2026-02-24)


### Features

* add search_users admin tool ([86bfe27](https://github.com/mbabic84/ainstruct-mcp/commit/86bfe277fdd9ddc68ba2f3eec4a29d079aebd3bf))

## [3.1.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.1.0...v3.1.1) (2026-02-24)


### Bug Fixes

* add auth header fallback and tool filtering tests ([b2825dc](https://github.com/mbabic84/ainstruct-mcp/commit/b2825dc8350a43fc96e77b97e2427cfa1383e3f5))

# [3.1.0](https://github.com/mbabic84/ainstruct-mcp/compare/v3.0.1...v3.1.0) (2026-02-24)


### Features

* add PAT multi-collection document access ([fbbfe8b](https://github.com/mbabic84/ainstruct-mcp/commit/fbbfe8b621a6c286e16334160910d285dafe5218))

## [3.0.1](https://github.com/mbabic84/ainstruct-mcp/compare/v3.0.0...v3.0.1) (2026-02-24)


### Bug Fixes

* migrate from SSE to streamable-http transport ([1c4622f](https://github.com/mbabic84/ainstruct-mcp/commit/1c4622f89f426bf54c7d98588d71629a49b57fbd))

# [3.0.0](https://github.com/mbabic84/ainstruct-mcp/compare/v2.0.0...v3.0.0) (2026-02-24)


### Features

* remove promote_to_admin_tool and add service admin tool filtering ([bb37e2e](https://github.com/mbabic84/ainstruct-mcp/commit/bb37e2e52183a236bd0d81e8a74bfd5b0b705717))


### BREAKING CHANGES

* promote_to_admin_tool no longer exists. First admin must be
created by using ADMIN_API_KEY as Bearer token and calling update_user_tool
with is_superuser: true.

# [2.0.0](https://github.com/mbabic84/ainstruct-mcp/compare/v1.6.5...v2.0.0) (2026-02-24)


### Features

* add permission-based tool filtering ([664803d](https://github.com/mbabic84/ainstruct-mcp/commit/664803d2e2ac94a63211313847db4b090ef4e51f))


### BREAKING CHANGES

* list_tools without auth now returns only 4 public tools
instead of all tools. Clients must authenticate to see protected tools.

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
