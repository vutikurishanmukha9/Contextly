from .base import BaseGenerator

class ChatGPTGenerator(BaseGenerator):
    """Generates context using standard Markdown and JSON arrays optimized for OpenAI models."""

    def generate(self) -> str:
        readme = self._get_readme_content()
        tree = self._generate_tree()
        
        npm_count = len(self.intelligence.dependencies.npm)
        py_count = len(self.intelligence.dependencies.python)

        has_memory = bool(self.intelligence.memory.rules)
        has_patterns = bool(self.intelligence.patterns.patterns)
        
        conventions_md = ""
        if has_memory or has_patterns:
            conventions_md = "## Team Conventions\n\n"
            if has_memory:
                conventions_md += "### Explicit Rules (Memory)\n"
                for r in self.intelligence.memory.rules:
                    conventions_md += f"- [{r.category}] {r.rule} [{r.confidence} confidence]\n"
                conventions_md += "\n"
                
            if has_patterns:
                saved_descriptions = {r.rule for r in self.intelligence.memory.rules}
                filtered_patterns = [p for p in self.intelligence.patterns.patterns if p.description not in saved_descriptions]
                if filtered_patterns:
                    conventions_md += "### Inferred Conventions (Discovery)\n"
                    for p in filtered_patterns:
                        conventions_md += f"- [{p.category}] {p.description} [{p.confidence} confidence]\n"
                    conventions_md += "\n"

        import json
        
        stack_identity = {
            "primary_language": self.intelligence.language.primary,
            "frontend_framework": ", ".join(self.intelligence.frameworks.frontend) if self.intelligence.frameworks.frontend else "None detected",
            "backend_tooling": ", ".join(self.intelligence.frameworks.backend) if self.intelligence.frameworks.backend else "None detected"
        }
        stack_identity_json = json.dumps(stack_identity, indent=2)

        markdown = f"""# Project Context Intelligence

## Overview
{readme}

{conventions_md}
## Architecture Map
````text
{tree}
````

## Stack Identity
```json
{stack_identity_json}
```

## Dependency Weight
- **NPM Packages**: {npm_count}
- **Python Packages**: {py_count}
"""
        return markdown
