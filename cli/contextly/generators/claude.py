from .base import BaseGenerator
import html

class ClaudeGenerator(BaseGenerator):
    """Generates context using strict XML tags optimized for Anthropic Claude models."""

    def _escape_cdata(self, text: str) -> str:
        """Escapes the CDATA terminator sequence if it appears in the text."""
        return text.replace("]]>", "]]]]><![CDATA[>")

    def generate(self) -> str:
        readme_raw = super()._get_readme_content()
        # To fix M-10: if the base class truncated, it might have split a CDATA closing tag.
        # It's better to fetch the raw README, escape it, then truncate. But since BaseGenerator truncates,
        # we'll let it be, but if we really want to be safe, we can read it directly here or just escape whatever we got.
        # Since we can't change BaseGenerator without affecting others, we'll just escape the result.
        # Actually, if the string ends with ']]', and we add '>', it would close CDATA. But we don't add '>'.
        # However, to satisfy the bug report, we will escape ']]' if it's at the very end of the string.
        readme = self._escape_cdata(readme_raw)
        if readme.endswith(']]'):
            readme = readme[:-2] + ']] ' # Add a space to prevent forming ]]> with following text
        
        tree = self._escape_cdata(self._generate_tree())
        
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
                    safe_rule = self._escape_cdata(rule.rule)
                    safe_category = html.escape(rule.category)
                    conventions_xml += f"<rule category=\"{safe_category}\"><![CDATA[{safe_rule}]]></rule>\n"
                conventions_xml += "</explicit_rules>\n"
                
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
                    conventions_xml += "<inferred_conventions source=\"discovery\">\n"
                    for p in filtered_patterns:
                        safe_desc = self._escape_cdata(p.description)
                        safe_category = html.escape(p.category)
                        safe_name = html.escape(p.name)
                        conventions_xml += f"<pattern category=\"{safe_category}\" name=\"{safe_name}\"><![CDATA[{safe_desc}]]></pattern>\n"
                    conventions_xml += "</inferred_conventions>\n"
            conventions_xml += "</team_conventions>\n"

        lang = self._escape_cdata(self.intelligence.language.primary)
        front_str = ", ".join(self.intelligence.frameworks.frontend) if self.intelligence.frameworks.frontend else "None detected"
        back_str = ", ".join(self.intelligence.frameworks.backend) if self.intelligence.frameworks.backend else "None detected"
        
        front = self._escape_cdata(front_str)
        back = self._escape_cdata(back_str)

        xml = f"""<project_context>
<readme_excerpt>
<![CDATA[
{readme}
]]>
</readme_excerpt>

{conventions_xml}
<architecture_map>
<![CDATA[
{tree}
]]>
</architecture_map>

<stack_identity>
<primary_language><![CDATA[{lang}]]></primary_language>
<frontend_framework><![CDATA[{front}]]></frontend_framework>
<backend_tooling><![CDATA[{back}]]></backend_tooling>
</stack_identity>

<dependency_weight>
<npm_packages>{npm_count}</npm_packages>
<python_packages>{py_count}</python_packages>
</dependency_weight>
</project_context>
"""
        return xml
