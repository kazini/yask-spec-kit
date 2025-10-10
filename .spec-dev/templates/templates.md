# Templates

This directory contains document templates for creating consistent, high-quality specifications. These templates follow the established principles and provide starting points for each phase of the spec-driven development process.

## Available Templates

### Core Document Templates

- **[requirements-template.md](requirements-template.md)** - EARS-formatted requirements document
- **[design-template.md](design-template.md)** - Comprehensive technical design document  
- **[tasks-template.md](tasks-template.md)** - Implementation task breakdown

### Specialized Templates

- **[sub-requirements-template.md](sub-requirements-template.md)** - Template for breaking down complex requirements
- **[sub-design-template.md](sub-design-template.md)** - Template for detailed design components
- **[api-design-template.md](api-design-template.md)** - Template for API-focused designs

## Usage Guidelines

### For AI Agents

1. **Copy templates** to the appropriate specification directory
2. **Customize placeholders** with feature-specific information
3. **Follow the structure** while adapting content to the specific feature
4. **Maintain consistency** across all specifications in a project

### For Developers

1. **Use automation scripts** that automatically apply templates
2. **Customize templates** for project-specific needs
3. **Create new templates** following the established patterns
4. **Version control templates** to track improvements

## Template Structure

All templates follow a consistent structure:

```markdown
# Document Title

## Introduction
[Clear summary and context]

## Main Content Sections
[Structured, scannable content]

## Cross-References
[Links to related documents]

## Notes
[Additional considerations]
```

## Customization

### Project-Specific Templates

You can customize these templates for your project by:

1. **Copying to `.specification/templates/`** in your project
2. **Modifying sections** to match your project needs
3. **Adding project-specific sections** as required
4. **Updating automation scripts** to use custom templates

### Placeholder Conventions

Templates use these placeholder conventions:

- `[FEATURE_NAME]` - Name of the feature being specified
- `[FEATURE_DESCRIPTION]` - Brief description of the feature
- `[PROJECT_NAME]` - Name of the project
- `[COMPONENT_NAME]` - Name of a specific component
- `[ROLE]` - User role in user stories
- `[BENEFIT]` - Benefit or value in user stories

## Quality Standards

All templates maintain these quality standards:

- **Clear structure** with logical section organization
- **Scannable format** with headers and bullet points
- **Actionable content** with specific guidance
- **Cross-reference support** for document relationships
- **Extensible design** for project customization

## Template Maintenance

### Adding New Templates

When adding new templates:

1. **Follow naming convention:** `{purpose}-template.md`
2. **Include in this README** with description
3. **Test with automation scripts** to ensure compatibility
4. **Document customization points** and usage guidelines

### Updating Existing Templates

When updating templates:

1. **Maintain backward compatibility** where possible
2. **Update documentation** to reflect changes
3. **Test with existing specifications** to ensure compatibility
4. **Version control changes** with clear commit messages

---

*These templates are designed to accelerate specification creation while maintaining consistency and quality across your project.*