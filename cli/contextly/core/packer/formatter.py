from typing import List
from ..graph.parsers.base import ParsedFileDTO, ExtractedEntity

class KnowledgeFormatter:
    """
    Renders structured Knowledge Graph entities into highly compressed, 
    token-efficient markdown for LLM consumption.
    """
    
    @staticmethod
    def format_file_knowledge(parsed_dto: ParsedFileDTO) -> str:
        """
        Formats a ParsedFileDTO into a compact markdown summary.
        """
        lines = []
        
        # We don't need a file header here, it's handled by the PackerEngine
        # But we do need to list the entities
        
        if not parsed_dto.entities:
            # If we successfully parsed but found no entities, just give basic stats
            lines.append(f"*(No structural entities extracted)*")
            return "\n".join(lines)
            
        for entity in parsed_dto.entities:
            # Entity Header
            lines.append(f"### {entity.kind.value}: `{entity.name}`")
            
            # Purpose / Docstring
            if entity.purpose:
                # Clean up docstring
                cleaned = " ".join(entity.purpose.strip().split())
                lines.append(f"**Purpose**: {cleaned}")
                
            # Class/Schema Fields
            if entity.fields:
                field_strs = []
                for f in entity.fields:
                    f_str = f.name
                    if f.type:
                        f_str += f": {f.type}"
                    field_strs.append(f_str)
                # Group fields tightly to save tokens
                lines.append(f"**Fields**: {', '.join(field_strs)}")
                
            # Methods
            if entity.methods:
                lines.append("**Methods**:")
                for m in entity.methods:
                    input_strs = [f"{i.name}: {i.type or 'any'}" for i in m.inputs]
                    ret_str = f" -> {m.returns}" if m.returns else ""
                    lines.append(f"- `{m.name}({', '.join(input_strs)}){ret_str}`")
                    
            # Function specifics
            if entity.kind == "FUNCTION":
                input_strs = [f"{i.name}: {i.type or 'any'}" for i in entity.inputs]
                ret_str = f" -> {entity.outputs}" if entity.outputs else ""
                lines.append(f"**Signature**: `({', '.join(input_strs)}){ret_str}`")
                
            lines.append("") # spacer
            
        return "\n".join(lines).strip()

    @staticmethod
    def format_metadata_fallback(file_path: str, raw_content: str) -> str:
        """
        Fallback for unknown files. Returns metadata instead of thousands of lines of code.
        """
        line_count = raw_content.count('\n') + 1
        lines = [
            f"*(Content omitted for token efficiency)*",
            f"**Type**: `{file_path.split('.')[-1]}`",
            f"**Line Count**: {line_count}"
        ]
        return "\n".join(lines)
