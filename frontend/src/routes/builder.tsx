import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app/AppShell";
import { FileText, Target, Shield, BookOpen, Paperclip, GripVertical, Plus, Sparkles, ArrowUp, ArrowDown, Trash2, Check, Copy } from "lucide-react";
import { useStore, ContextKind, ContextBlock } from "@/lib/store";
import { calculateScores } from "@/lib/scoring";
import { generatePrompt } from "@/lib/prompt-generator";
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export const Route = createFileRoute("/builder")({
  head: () => ({ meta: [{ title: "Context Builder — Context-Ly" }] }),
  component: Builder,
});

function Builder() {
  const { activeProjectId, projects } = useStore();
  const project = activeProjectId ? projects[activeProjectId] : null;

  return (
    <AppShell
      title="Context Builder"
      subtitle={project ? `Project: ${project.name}` : "Compose goals, constraints, examples and files into a living context pack."}
      actions={
        <>
          <button className="rounded-pill border border-border bg-surface px-4 py-2 text-[13px] font-medium hover:bg-muted">Save draft</button>
          <button className="rounded-pill bg-foreground px-4 py-2 text-[13px] font-medium text-background hover:opacity-90">Generate prompt</button>
        </>
      }
    >
      <SetupModal />
      <div className="grid gap-5 lg:grid-cols-[260px_1fr_320px]">
        <Sources />
        <Canvas />
        <Optimizer />
      </div>
    </AppShell>
  );
}

function SetupModal() {
  const { activeProjectId, createProject } = useStore();
  const [open, setOpen] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [audience, setAudience] = useState("");
  const [techStack, setTechStack] = useState("");
  const [outputStyle, setOutputStyle] = useState("");

  useEffect(() => {
    if (!activeProjectId) {
      setOpen(true);
    } else {
      setOpen(false);
    }
  }, [activeProjectId]);

  const handleSave = () => {
    if (!name.trim()) return;
    createProject({
      name,
      audience,
      techStack,
      outputStyle,
    });
  };

  return (
    <Dialog open={open} onOpenChange={(val) => {
      // Prevent closing if no active project
      if (activeProjectId) setOpen(val);
    }}>
      <DialogContent className="sm:max-w-[425px]" onInteractOutside={(e) => {
        if (!activeProjectId) e.preventDefault();
      }}>
        <DialogHeader>
          <DialogTitle>Setup New Project</DialogTitle>
          <DialogDescription>
            Define the permanent context for this session. This shapes the foundation of your prompts.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Project Name <span className="text-destructive">*</span></Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Auth Refactor" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="audience">Target Role / Audience</Label>
            <Input id="audience" value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="e.g. Senior Backend Engineer" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="stack">Tech Stack</Label>
            <Input id="stack" value={techStack} onChange={(e) => setTechStack(e.target.value)} placeholder="e.g. Node 20, Express, PostgreSQL" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="style">Output Style</Label>
            <Input id="style" value={outputStyle} onChange={(e) => setOutputStyle(e.target.value)} placeholder="e.g. Concise, code-only, no pleasantries" />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSave} disabled={!name.trim()}>Create Project</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const sourcesConfig = [
  { kind: "Goal" as ContextKind, icon: Target, desc: "What does success look like?" },
  { kind: "Background" as ContextKind, icon: BookOpen, desc: "What does the model need to know?" },
  { kind: "Constraints" as ContextKind, icon: Shield, desc: "Boundaries, tone, format." },
  { kind: "Examples" as ContextKind, icon: FileText, desc: "Few-shot, gold standard, anti-examples." },
  { kind: "Files" as ContextKind, icon: Paperclip, desc: "PDFs, docs, code, transcripts." },
];

function Sources() {
  const { activeProjectId, addBlock } = useStore();

  const handleAdd = (kind: ContextKind) => {
    if (!activeProjectId) return;
    addBlock(activeProjectId, {
      kind,
      title: `New ${kind}`,
      content: "",
      enabled: true,
    });
  };

  return (
    <div className="surface-card p-4 h-fit">
      <div className="px-1 pb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Input sources</div>
      <div className="space-y-1.5">
        {sourcesConfig.map((s) => {
          const Icon = s.icon;
          return (
            <button key={s.kind} onClick={() => handleAdd(s.kind)} className="flex w-full items-start gap-3 rounded-md p-2.5 text-left hover:bg-muted transition-colors">
              <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted border border-border">
                <Icon className="h-4 w-4" />
              </span>
              <span>
                <span className="block text-[13.5px] font-medium">{s.kind}</span>
                <span className="block text-[12px] text-muted-foreground">{s.desc}</span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Canvas() {
  const { activeProjectId, projects, updateBlock, deleteBlock, moveBlock } = useStore();
  const project = activeProjectId ? projects[activeProjectId] : null;

  if (!project) return <div className="surface-card p-5"><div className="text-muted-foreground text-sm">Please set up a project first.</div></div>;

  const totalTokens = project.blocks.reduce((acc, b) => acc + (b.enabled ? b.tokenCount : 0), 0);

  return (
    <div className="surface-card p-5 min-h-[500px]">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-display text-[16px] font-semibold">Live context canvas</div>
          <div className="text-[12.5px] text-muted-foreground">Edit your context blocks below.</div>
        </div>
        <div className="text-mono text-[12px] text-muted-foreground">{totalTokens} tokens</div>
      </div>
      <div className="mt-5 space-y-3">
        {project.blocks.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground border border-dashed rounded-xl border-border">
            No context blocks yet. Click a source on the left to add one.
          </div>
        ) : (
          project.blocks.map((b, i) => (
            <BlockEditor 
              key={b.id} 
              block={b} 
              projectId={project.id} 
              isFirst={i === 0} 
              isLast={i === project.blocks.length - 1} 
              updateBlock={updateBlock}
              deleteBlock={deleteBlock}
              moveBlock={moveBlock}
            />
          ))
        )}
      </div>
    </div>
  );
}

function BlockEditor({ 
  block, projectId, isFirst, isLast, updateBlock, deleteBlock, moveBlock 
}: { 
  block: ContextBlock, projectId: string, isFirst: boolean, isLast: boolean,
  updateBlock: any, deleteBlock: any, moveBlock: any 
}) {
  const tones: Record<ContextKind, string> = {
    Goal: "bg-lavender/50 border-lavender",
    Background: "bg-sky/50 border-sky",
    Constraints: "bg-peach/50 border-peach",
    Examples: "bg-mint/50 border-mint",
    Files: "bg-cream/50 border-cream"
  };

  return (
    <div className={`group flex flex-col gap-2 rounded-xl border ${tones[block.kind]} p-4 transition-all focus-within:ring-2 focus-within:ring-primary/20 ${!block.enabled ? 'opacity-50 grayscale' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="rounded-pill bg-background/80 px-2.5 py-0.5 text-[11px] font-semibold shadow-sm">{block.kind}</span>
          <span className="text-mono text-[11px] text-foreground/60">{block.tokenCount} tok</span>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => updateBlock(projectId, block.id, { enabled: !block.enabled })} className="p-1 hover:bg-background/50 rounded text-muted-foreground" title="Toggle block">
            <Check className={`h-4 w-4 ${block.enabled ? 'text-success' : ''}`} />
          </button>
          <button onClick={() => moveBlock(projectId, block.id, 'up')} disabled={isFirst} className="p-1 hover:bg-background/50 rounded text-muted-foreground disabled:opacity-30">
            <ArrowUp className="h-4 w-4" />
          </button>
          <button onClick={() => moveBlock(projectId, block.id, 'down')} disabled={isLast} className="p-1 hover:bg-background/50 rounded text-muted-foreground disabled:opacity-30">
            <ArrowDown className="h-4 w-4" />
          </button>
          <button onClick={() => deleteBlock(projectId, block.id)} className="p-1 hover:bg-background/50 rounded text-destructive/70 hover:text-destructive">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="mt-1 flex flex-col gap-2">
        <input 
          value={block.title} 
          onChange={(e) => updateBlock(projectId, block.id, { title: e.target.value })}
          className="bg-transparent font-medium text-[14px] outline-none placeholder:text-muted-foreground/50"
          placeholder={`${block.kind} Title...`}
        />
        <Textarea 
          value={block.content}
          onChange={(e) => updateBlock(projectId, block.id, { content: e.target.value })}
          className="min-h-[80px] bg-background/50 border-transparent text-[13px] resize-y"
          placeholder={`Enter detailed ${block.kind.toLowerCase()} content here...`}
        />
      </div>
    </div>
  );
}

function Optimizer() {
  const { activeProjectId, projects } = useStore();
  const project = activeProjectId ? projects[activeProjectId] : null;
  const [copied, setCopied] = useState(false);

  if (!project) return null;

  const scores = calculateScores(project.blocks);
  const prompt = generatePrompt(project);

  const handleCopy = () => {
    navigator.clipboard.writeText(prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-5">
      <div className="surface-card p-5">
        <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">Context score</div>
        <div className="text-display mt-2 text-[40px] font-semibold">{scores.overall}</div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-muted">
          <div className="h-full score-gradient transition-all duration-500" style={{ width: `${scores.overall}%` }} />
        </div>
        <div className="mt-4 space-y-2">
          {[
            ["Relevance", scores.relevance],
            ["Completeness", scores.completeness],
            ["Redundancy", scores.redundancy],
            ["Clarity", scores.clarity]
          ].map(([k,v]) => (
            <div key={k as string} className="flex items-center justify-between text-[12.5px]">
              <span className="text-muted-foreground">{k}</span>
              <span className="text-mono">{v as number}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="surface-card p-5 flex flex-col max-h-[400px]">
        <div className="flex items-center justify-between pb-3">
          <div className="text-[12px] font-medium uppercase tracking-wider text-muted-foreground">Generated prompt</div>
          <button onClick={handleCopy} className="text-muted-foreground hover:text-foreground flex items-center gap-1 text-[11px] font-medium">
            {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
        <pre className="text-mono flex-1 overflow-auto rounded-md bg-muted/60 p-3 text-[11.5px] leading-relaxed whitespace-pre-wrap">{prompt || "Add blocks to generate prompt."}</pre>
      </div>
    </div>
  );
}
