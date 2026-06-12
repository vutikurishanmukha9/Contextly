import html
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
                    cat = html.escape(rule.category)
                    text = html.escape(rule.rule)
                    conventions_xml += f"<rule category=\"{cat}\">{text}</rule>\n"
                conventions_xml += "</explicit_rules>\n"
                
            if has_patterns:
                saved_descriptions = {r.rule for r in self.intelligence.memory.rules}
                filtered_patterns = [p for p in self.intelligence.patterns.patterns if p.description not in saved_descriptions]
                if filtered_patterns:
                    conventions_xml += "<inferred_conventions source=\"discovery\">\n"
                    for p in filtered_patterns:
                        p_cat = html.escape(p.category)
                        p_name = html.escape(p.name)
                        p_desc = html.escape(p.description)
                        conventions_xml += f"<pattern category=\"{p_cat}\" name=\"{p_name}\">{p_desc}</pattern>\n"
                    conventions_xml += "</inferred_conventions>\n"
            conventions_xml += "</team_conventions>\n"

        readme_esc = html.escape(readme)
        tree_esc = html.escape(tree)
        lang_esc = html.escape(self.intelligence.language.primary)
        front_esc = html.escape(self.intelligence.frameworks.frontend)
        back_esc = html.escape(self.intelligence.frameworks.backend)

        xml = f"""<project_context>
<overview>
{readme_esc}
</overview>

{conventions_xml}
<architecture_map>
{tree_esc}
</architecture_map>

<stack_identity>
<primary_language>{lang_esc}</primary_language>
<frontend_framework>{front_esc}</frontend_framework>
<backend_tooling>{back_esc}</backend_tooling>
</stack_identity>

<dependency_weight>
<npm_packages>{npm_count}</npm_packages>
<python_packages>{py_count}</python_packages>
</dependency_weight>
</project_context>
"""
        return xml
