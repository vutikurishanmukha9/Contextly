from .base import BaseGenerator
import xml.etree.ElementTree as ET

class ClaudeGenerator(BaseGenerator):
    """Generates context using strict XML tags optimized for Anthropic Claude models."""

    def generate(self) -> str:
        root = ET.Element("project_context")
        
        readme_excerpt = ET.SubElement(root, "readme_excerpt")
        readme_excerpt.text = super()._get_readme_content()
        
        has_memory = bool(self.intelligence.memory.rules)
        has_patterns = bool(self.intelligence.patterns.patterns)
        
        if has_memory or has_patterns:
            team_conventions = ET.SubElement(root, "team_conventions")
            
            if has_memory:
                explicit_rules = ET.SubElement(team_conventions, "explicit_rules", source="memory")
                for rule in self.intelligence.memory.rules:
                    rule_node = ET.SubElement(explicit_rules, "rule", category=rule.category)
                    rule_node.text = rule.rule
                    
            if has_patterns:
                filtered_patterns = self.intelligence.get_deduplicated_patterns()
                if filtered_patterns:
                    inferred_conventions = ET.SubElement(team_conventions, "inferred_conventions", source="discovery")
                    for p in filtered_patterns:
                        pattern_node = ET.SubElement(inferred_conventions, "pattern", category=p.category, name=p.name)
                        pattern_node.text = p.description

        architecture_map = ET.SubElement(root, "architecture_map")
        architecture_map.text = self._generate_tree()
        
        stack_identity = ET.SubElement(root, "stack_identity")
        ET.SubElement(stack_identity, "primary_language").text = self.intelligence.language.primary
        
        front_str = ", ".join(self.intelligence.frameworks.frontend) if self.intelligence.frameworks.frontend else "None detected"
        ET.SubElement(stack_identity, "frontend_framework").text = front_str
        
        back_str = ", ".join(self.intelligence.frameworks.backend) if self.intelligence.frameworks.backend else "None detected"
        ET.SubElement(stack_identity, "backend_tooling").text = back_str
        
        dependency_weight = ET.SubElement(root, "dependency_weight")
        ET.SubElement(dependency_weight, "npm_packages").text = str(len(self.intelligence.dependencies.npm or []))
        ET.SubElement(dependency_weight, "python_packages").text = str(len(self.intelligence.dependencies.python or []))
        
        if hasattr(ET, "indent"):
            ET.indent(root, space="  ", level=0)
            
        return ET.tostring(root, encoding="unicode")
