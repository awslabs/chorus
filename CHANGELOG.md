All notable changes to this project will be documented in this file.

## v0.2.1 (unreleased)

### Breaking Changes
- Removed jsonnet support in favor of YAML for workspace configuration

### Migration Guide
- Use the migration tool to convert existing jsonnet files to YAML:
  ```
  pip install 'chorus[migration]'
  migrate-chorus-jsonnet --dir path/to/your/workspaces
  ```
- All workspace configurations now use .yaml files instead of .jsonnet
- Update any scripts or documentation that reference .jsonnet files

## v0.2.0

- Code refactoring for teams, agent types and workspaces.
