import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ContextKind = 'Goal' | 'Background' | 'Constraints' | 'Examples' | 'Files';

export interface ContextBlock {
  id: string;
  kind: ContextKind;
  title: string;
  content: string;
  tokenCount: number;
  enabled: boolean;
}

export interface ProjectState {
  id: string;
  name: string;
  audience: string;
  techStack: string;
  outputStyle: string;
  blocks: ContextBlock[];
}

export interface AppState {
  projects: Record<string, ProjectState>;
  activeProjectId: string | null;

  // Actions
  createProject: (data: Omit<ProjectState, 'id' | 'blocks'>) => void;
  setActiveProject: (id: string) => void;
  updateProject: (id: string, data: Partial<ProjectState>) => void;

  // Block Actions
  addBlock: (projectId: string, block: Omit<ContextBlock, 'id' | 'tokenCount'>) => void;
  updateBlock: (projectId: string, blockId: string, data: Partial<ContextBlock>) => void;
  deleteBlock: (projectId: string, blockId: string) => void;
  moveBlock: (projectId: string, blockId: string, direction: 'up' | 'down') => void;
}

const generateId = () => Math.random().toString(36).substring(2, 9);
const calculateTokens = (text: string) => Math.ceil(text.length / 4);

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      projects: {},
      activeProjectId: null,

      createProject: (data) =>
        set((state) => {
          const id = generateId();
          return {
            projects: {
              ...state.projects,
              [id]: {
                ...data,
                id,
                blocks: [],
              },
            },
            activeProjectId: id,
          };
        }),

      setActiveProject: (id) => set({ activeProjectId: id }),

      updateProject: (id, data) =>
        set((state) => {
          const project = state.projects[id];
          if (!project) return state;
          return {
            projects: {
              ...state.projects,
              [id]: { ...project, ...data },
            },
          };
        }),

      addBlock: (projectId, blockData) =>
        set((state) => {
          const project = state.projects[projectId];
          if (!project) return state;

          const newBlock: ContextBlock = {
            ...blockData,
            id: generateId(),
            tokenCount: calculateTokens(blockData.content || blockData.title),
          };

          return {
            projects: {
              ...state.projects,
              [projectId]: {
                ...project,
                blocks: [...project.blocks, newBlock],
              },
            },
          };
        }),

      updateBlock: (projectId, blockId, data) =>
        set((state) => {
          const project = state.projects[projectId];
          if (!project) return state;

          const blocks = project.blocks.map((block) => {
            if (block.id !== blockId) return block;
            const updatedBlock = { ...block, ...data };
            if (data.content !== undefined || data.title !== undefined) {
              updatedBlock.tokenCount = calculateTokens(updatedBlock.content || updatedBlock.title);
            }
            return updatedBlock;
          });

          return {
            projects: {
              ...state.projects,
              [projectId]: { ...project, blocks },
            },
          };
        }),

      deleteBlock: (projectId, blockId) =>
        set((state) => {
          const project = state.projects[projectId];
          if (!project) return state;

          return {
            projects: {
              ...state.projects,
              [projectId]: {
                ...project,
                blocks: project.blocks.filter((b) => b.id !== blockId),
              },
            },
          };
        }),

      moveBlock: (projectId, blockId, direction) =>
        set((state) => {
          const project = state.projects[projectId];
          if (!project) return state;

          const index = project.blocks.findIndex((b) => b.id === blockId);
          if (index === -1) return state;
          if (direction === 'up' && index === 0) return state;
          if (direction === 'down' && index === project.blocks.length - 1) return state;

          const newBlocks = [...project.blocks];
          const swapIndex = direction === 'up' ? index - 1 : index + 1;
          [newBlocks[index], newBlocks[swapIndex]] = [newBlocks[swapIndex], newBlocks[index]];

          return {
            projects: {
              ...state.projects,
              [projectId]: { ...project, blocks: newBlocks },
            },
          };
        }),
    }),
    {
      name: 'context-ly-storage',
    }
  )
);
