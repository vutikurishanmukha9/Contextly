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
                    conf_str = "High" if r.confidence >= 0.9 else "Medium" if r.confidence >= 0.7 else "Low"
                    conventions_md += f"- [{r.category}] {r.rule} [{conf_str} confidence]\n"
                conventions_md += "\n"
                
            if has_patterns:
                # Deduplicate inferred conventions using exact (category, name) tuple if possible
                saved_tuples = {(r.category, r.name) for r in self.intelligence.memory.rules if r.name}
                # Fallback to rule text if name is absent in older rules
                saved_descriptions = {r.rule for r in self.intelligence.memory.rules if not r.name}
                
                filtered_patterns = []
                for p in self.intelligence.patterns.patterns:
                    if (p.category, p.name) in saved_tuples:
                        continue
                    if p.description in saved_descriptions:
                        continue
                    filtered_patterns.append(p)
                    
                if filtered_patterns:
                    conventions_md += "### Inferred Conventions (Discovery)\n"
                    for p in filtered_patterns:
                        conf_str = "High" if p.confidence >= 0.9 else "Medium" if p.confidence >= 0.7 else "Low"
                        conventions_md += f"- [{p.category}] {p.description} [{conf_str} confidence]\n"
                    conventions_md += "\n"

        import json
        
        stack_identity = {
            "primary_language": self.intelligence.language.primary,
            "frontend_framework": ", ".join(self.intelligence.frameworks.frontend) if self.intelligence.frameworks.frontend else "None detected",
            "backend_tooling": ", ".join(self.intelligence.frameworks.backend) if self.intelligence.frameworks.backend else "None detected"
        }
        stack_identity_json = json.dumps(stack_identity, indent=2)

        markdown = f"""# Project Context Intelligence

## README Excerpt
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
