import json
from .base import BaseGenerator

class ClaudeGenerator(BaseGenerator):
    """Generates context using strict XML tags optimized for Anthropic Claude models."""

    def generate(self) -> str:
        readme = self._get_readme_content()
        tree = self._generate_tree()
        
        npm_count = len(self.intelligence.dependencies.npm)
        py_count = len(self.intelligence.dependencies.python)

        has_memory = bool(self.intelligence.memory.rules)
        has_patterns = bool(self.intelligence.patterns.patterns)
        
        conventions_xml = ""
        if has_memory or has_patterns:
            conventions_xml = "<team_conventions>\n"
            if has_memory:
                conventions_xml += "<explicit_rules source=\"memory\">\n"
                for rule in self.intelligence.memory.rules:
                    conventions_xml += f"<rule category=\"{rule.category}\">{rule.rule}</rule>\n"
                conventions_xml += "</explicit_rules>\n"
                
            if has_patterns:
                saved_descriptions = {r.rule for r in self.intelligence.memory.rules}
                filtered_patterns = [p for p in self.intelligence.patterns.patterns if p.description not in saved_descriptions]
                if filtered_patterns:
                    conventions_xml += "<inferred_conventions source=\"discovery\">\n"
                    for p in filtered_patterns:
                        conventions_xml += f"<pattern category=\"{p.category}\" name=\"{p.name}\">{p.description}</pattern>\n"
                    conventions_xml += "</inferred_conventions>\n"
            conventions_xml += "</team_conventions>\n"

        xml = f"""<project_context>
<overview>
{readme}
</overview>

{conventions_xml}
<architecture_map>
{tree}
</architecture_map>

<stack_identity>
<primary_language>{self.intelligence.language.primary}</primary_language>
<frontend_framework>{self.intelligence.frameworks.frontend}</frontend_framework>
<backend_tooling>{self.intelligence.frameworks.backend}</backend_tooling>
</stack_identity>

<dependency_weight>
<npm_packages>{npm_count}</npm_packages>
<python_packages>{py_count}</python_packages>
</dependency_weight>
</project_context>
"""
        return xml
