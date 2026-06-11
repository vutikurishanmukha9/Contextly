import { ProjectState, ContextKind } from './store';

export function generatePrompt(project: ProjectState): string {
  let prompt = '';

  // 1. System Context (from Project Setup)
  prompt += '# SYSTEM CONTEXT\n';
  if (project.audience) prompt += `Audience: ${project.audience}\n`;
  if (project.techStack) prompt += `Tech Stack: ${project.techStack}\n`;
  if (project.outputStyle) prompt += `Output Style: ${project.outputStyle}\n`;
  prompt += '\n';

  const activeBlocks = project.blocks.filter((b) => b.enabled);

  // Helper to group blocks by kind
  const blocksByKind = (kind: ContextKind) => activeBlocks.filter((b) => b.kind === kind);

  // 2. Task Goal
  const goalBlocks = blocksByKind('Goal');
  if (goalBlocks.length > 0) {
    prompt += '# TASK GOAL\n';
    goalBlocks.forEach((b) => {
      prompt += `${b.content}\n\n`;
    });
  }

  // 3. Background
  const backgroundBlocks = blocksByKind('Background');
  if (backgroundBlocks.length > 0) {
    prompt += '# BACKGROUND\n';
    backgroundBlocks.forEach((b) => {
      prompt += `- ${b.content}\n`;
    });
    prompt += '\n';
  }

  // 4. Constraints
  const constraintsBlocks = blocksByKind('Constraints');
  if (constraintsBlocks.length > 0) {
    prompt += '# CONSTRAINTS\n';
    constraintsBlocks.forEach((b) => {
      prompt += `- ${b.content}\n`;
    });
    prompt += '\n';
  }

  // 5. Examples
  const exampleBlocks = blocksByKind('Examples');
  if (exampleBlocks.length > 0) {
    prompt += '# EXAMPLES\n';
    exampleBlocks.forEach((b) => {
      prompt += `## Example: ${b.title || 'Reference'}\n${b.content}\n\n`;
    });
  }

  // 6. Files
  const fileBlocks = blocksByKind('Files');
  if (fileBlocks.length > 0) {
    prompt += '# FILES & REFERENCE MATERIALS\n';
    fileBlocks.forEach((b) => {
      prompt += `## File: ${b.title || 'Reference'}\n\`\`\`\n${b.content}\n\`\`\`\n\n`;
    });
  }

  return prompt.trim();
}
