import { ContextBlock } from './store';

// Helper: Tokenize text into lowercase words, removing punctuation
function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter((word) => word.length > 0);
}

// Helper: Get stop words to ignore in similarity calculations
const stopWords = new Set(['the', 'is', 'at', 'which', 'and', 'on', 'in', 'to', 'a', 'of', 'for', 'with', 'it', 'that']);

// Relevance: Word overlap ratio between Goal blocks and other blocks
function calculateRelevance(blocks: ContextBlock[]): number {
  if (blocks.length === 0) return 0;
  
  const activeBlocks = blocks.filter((b) => b.enabled);
  const goalBlocks = activeBlocks.filter((b) => b.kind === 'Goal');
  const otherBlocks = activeBlocks.filter((b) => b.kind !== 'Goal');

  if (goalBlocks.length === 0) return 40; // Severe penalty if no goal
  if (otherBlocks.length === 0) return 100; // Perfect relevance if only goal exists

  const goalWords = new Set(
    goalBlocks.flatMap((b) => tokenize(b.content)).filter((w) => !stopWords.has(w))
  );

  if (goalWords.size === 0) return 50;

  let totalOverlapScore = 0;

  otherBlocks.forEach((block) => {
    const blockWords = tokenize(block.content).filter((w) => !stopWords.has(w));
    if (blockWords.length === 0) return;

    let matchCount = 0;
    blockWords.forEach((w) => {
      if (goalWords.has(w)) matchCount++;
    });

    // We expect at least some overlap. A ratio of 0.1 (10% of words overlap with goal) is considered highly relevant.
    const overlapRatio = matchCount / blockWords.length;
    const blockScore = Math.min(100, (overlapRatio / 0.1) * 100);
    totalOverlapScore += blockScore;
  });

  return Math.round(totalOverlapScore / otherBlocks.length);
}

// Completeness: Evaluates presence of necessary block kinds
function calculateCompleteness(blocks: ContextBlock[]): number {
  const activeBlocks = blocks.filter((b) => b.enabled);
  const kinds = new Set(activeBlocks.map((b) => b.kind));

  let score = 0;
  if (kinds.has('Goal')) score += 40;
  if (kinds.has('Constraints')) score += 30;
  if (kinds.has('Background')) score += 20;
  if (kinds.has('Examples')) score += 10;

  return score;
}

// Redundancy: Jaccard similarity index across all blocks
function calculateRedundancy(blocks: ContextBlock[]): number {
  const activeBlocks = blocks.filter((b) => b.enabled);
  if (activeBlocks.length < 2) return 100; // No redundancy if 0 or 1 block

  let maxSimilarity = 0;

  const tokenizedBlocks = activeBlocks.map((b) => new Set(tokenize(b.content).filter((w) => !stopWords.has(w))));

  for (let i = 0; i < tokenizedBlocks.length; i++) {
    for (let j = i + 1; j < tokenizedBlocks.length; j++) {
      const setA = tokenizedBlocks[i];
      const setB = tokenizedBlocks[j];

      if (setA.size === 0 || setB.size === 0) continue;

      let intersection = 0;
      setA.forEach((word) => {
        if (setB.has(word)) intersection++;
      });

      const union = setA.size + setB.size - intersection;
      const similarity = union === 0 ? 0 : intersection / union;
      if (similarity > maxSimilarity) {
        maxSimilarity = similarity;
      }
    }
  }

  // If max similarity > 0.3 (30% overlap), we penalize heavily. 
  // Redundancy score is INVERSE of similarity (100 is best, meaning 0 similarity).
  const redundancyPenalty = Math.min(100, (maxSimilarity / 0.3) * 100);
  return Math.round(100 - redundancyPenalty);
}

// Clarity: Sentence length and detection of ambiguous pronouns
function calculateClarity(blocks: ContextBlock[]): number {
  const activeBlocks = blocks.filter((b) => b.enabled);
  if (activeBlocks.length === 0) return 0;

  let totalScore = 0;

  activeBlocks.forEach((block) => {
    // 1. Sentence length check
    const sentences = block.content.split(/[.!?]+/).filter((s) => s.trim().length > 0);
    let blockScore = 100;

    if (sentences.length > 0) {
      const wordsPerSentence = sentences.map((s) => tokenize(s).length);
      const avgWordsPerSentence = wordsPerSentence.reduce((a, b) => a + b, 0) / sentences.length;

      // Penalize if average sentence is > 25 words
      if (avgWordsPerSentence > 25) {
        blockScore -= Math.min(40, (avgWordsPerSentence - 25) * 2);
      }
    }

    // 2. Ambiguous pronoun check
    const ambiguousPronouns = ['it', 'that', 'this', 'those', 'these'];
    const words = tokenize(block.content);
    let ambiguousCount = 0;
    
    words.forEach((w) => {
      if (ambiguousPronouns.includes(w)) ambiguousCount++;
    });

    // Penalize if ambiguous pronouns make up > 5% of words
    if (words.length > 0) {
      const ambiguousRatio = ambiguousCount / words.length;
      if (ambiguousRatio > 0.05) {
        blockScore -= Math.min(30, (ambiguousRatio - 0.05) * 100 * 2);
      }
    }

    totalScore += Math.max(0, blockScore);
  });

  return Math.round(totalScore / activeBlocks.length);
}

export interface ContextScores {
  overall: number;
  relevance: number;
  completeness: number;
  redundancy: number;
  clarity: number;
}

export function calculateScores(blocks: ContextBlock[]): ContextScores {
  const relevance = calculateRelevance(blocks);
  const completeness = calculateCompleteness(blocks);
  const redundancy = calculateRedundancy(blocks);
  const clarity = calculateClarity(blocks);

  const overall = Math.round((relevance + completeness + redundancy + clarity) / 4);

  return {
    overall,
    relevance,
    completeness,
    redundancy,
    clarity,
  };
}
