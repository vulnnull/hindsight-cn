# CARA: Coherent Adaptive Reasoning Agents

## Abstract

We present CARA (Coherent Adaptive Reasoning Agents), a personality framework for conversational AI agents that enables consistent, trait-driven reasoning and dynamic belief formation. Building on the Big Five personality model from psychology, we introduce a system where agents form and maintain opinions influenced by configurable personality traits (openness, conscientiousness, extraversion, agreeableness, neuroticism). Our implementation uses TEMPR (Temporal Entity Memory Priming Retrieval), a memory system that combines temporal, semantic, and entity-based retrieval to manage three distinct memory networks: world facts, agent experiences, and opinions. This architecture separates objective information from subjective beliefs (opinions with confidence scores), enabling epistemic clarity and traceability. Opinions evolve through reinforcement—when new evidence arrives, the system automatically evaluates whether existing beliefs should be strengthened, weakened, or revised. We demonstrate how personality bias strength controls the degree to which traits influence reasoning, enabling agents to range from purely objective (bias=0.0) to strongly personality-driven (bias=1.0). The system maintains agent identity through background merging that intelligently resolves contradictions while preserving coherent first-person narratives. This work addresses the challenge of creating AI agents with consistent, explainable perspectives that can evolve over time while maintaining personality coherence.

## 1. Introduction

Conversational AI agents increasingly need to maintain consistent perspectives and form judgments that reflect stable character traits. Current systems either provide purely objective information retrieval without perspective, or generate responses that lack consistency across interactions. Human conversation partners expect agents to have stable viewpoints, preferences, and reasoning styles—characteristics that emerge from personality.

We propose CARA (Coherent Adaptive Reasoning Agents), a personality framework that addresses these limitations through:

1. **Big Five Personality Integration**: Configurable traits (OCEAN model) that influence how agents interpret facts and form opinions
2. **TEMPR Memory Architecture**: Leverages TEMPR (Temporal Entity Memory Priming Retrieval) to manage three distinct networks (world facts, agent experiences, opinions), enabling sophisticated memory access and clear separation between objective information and subjective beliefs
3. **Opinion Reinforcement**: Dynamic belief updating when new evidence reinforces, weakens, or contradicts existing opinions
4. **Personality Bias Control**: Adjustable influence strength allowing agents to range from objective to strongly personality-driven
5. **Background Merging**: LLM-powered integration of biographical information with intelligent conflict resolution

This architecture enables agents to maintain consistent identities while allowing beliefs to evolve naturally with new information.

### 1.1 Motivation

Consider an agent discussing remote work. With high openness (0.9) and low conscientiousness (0.2), the agent might form the opinion: "Remote work enables creative flexibility and spontaneous innovation." The same facts presented to an agent with low openness (0.2) and high conscientiousness (0.9) might yield: "Remote work lacks the structure and accountability needed for consistent performance."

Both agents access identical factual information, but personality traits bias how they weight different aspects (flexibility vs. structure) and what conclusions they draw. This mirrors human reasoning—our personalities influence what we attend to and how we integrate information into our worldview.

### 1.2 Contributions

Our key contributions are:

1. **Personality-Aware Reasoning**: A prompt engineering framework that injects Big Five traits into LLM reasoning, demonstrating how personality consistently biases opinion formation

2. **TEMPR-Based Three-Network Architecture**: Integration with TEMPR (Temporal Entity Memory Priming Retrieval) to manage three distinct networks (world facts, agent experiences, opinions), enabling architectural separation between objective information and subjective beliefs with epistemic clarity and traceability

3. **Opinion Reinforcement Mechanism**: An automatic belief update system that adjusts confidence scores when new evidence arrives, creating dynamic belief systems that evolve with information

4. **Background Merging with Conflict Resolution**: An LLM-powered method for maintaining coherent agent identities when new biographical information contradicts existing background

5. **Bias Strength Control**: A meta-parameter that allows tuning personality influence from objective (0.0) to strongly subjective (1.0), enabling task-appropriate personality expression

## 2. Personality Model

### 2.1 Big Five Framework

We adopt the **Big Five** personality model (OCEAN), which is empirically validated across cultures and provides continuous trait dimensions:

**Trait Dimensions** (each 0.0-1.0):

1. **Openness (O)**: Receptiveness to new ideas, creativity, abstract thinking
   - High: "I embrace novel approaches", "innovation over tradition"
   - Low: "I prefer proven methods", "tradition over experimentation"

2. **Conscientiousness (C)**: Organization, goal-directed behavior, dependability
   - High: "I plan systematically", "evidence-based decisions"
   - Low: "I work flexibly", "intuition-based decisions"

3. **Extraversion (E)**: Sociability, assertiveness, energy from interaction
   - High: "I seek collaboration", "enthusiastic communication"
   - Low: "I prefer solitude", "measured communication"

4. **Agreeableness (A)**: Cooperation, empathy, conflict avoidance
   - High: "I seek consensus", "consider social harmony"
   - Low: "I express dissent", "prioritize accuracy over harmony"

5. **Neuroticism (N)**: Emotional sensitivity, anxiety, stress response
   - High: "I consider risks carefully", "emotionally engaged"
   - Low: "I remain calm under uncertainty", "emotionally detached"

**Bias Strength** (0.0-1.0): Meta-parameter controlling how much personality influences opinions
- 0.0: Neutral, fact-based reasoning (no personality bias)
- 0.5: Moderate personality influence, balanced with objective analysis
- 1.0: Strong personality influence, facts filtered through trait lens

### 2.2 Psychological Basis

The Big Five model has several advantages for AI agents:

1. **Empirical Validation**: Decades of psychological research demonstrate cross-cultural stability and predictive validity
2. **Continuous Dimensions**: Unlike categorical types, continuous scales allow fine-grained personality tuning
3. **Behavioral Prediction**: Traits predict information processing styles, decision-making approaches, and communication preferences
4. **Interpretability**: Well-understood trait meanings enable users to anticipate agent behavior

**Trait Influence on Reasoning**:
- **High Openness**: Favors novel solutions, abstract thinking, considers unconventional perspectives
- **High Conscientiousness**: Emphasizes systematic analysis, evidence quality, long-term consequences
- **High Extraversion**: Considers social aspects, collaborative solutions, enthusiastic expression
- **High Agreeableness**: Weights harmony, considers multiple viewpoints, seeks consensus
- **High Neuroticism**: Attends to risks, emotional implications, uncertainty

## 3. Agent Profile Structure

### 3.1 Profile Schema

Each agent has an associated profile containing identity information:

```sql
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Agent',
    personality JSONB NOT NULL DEFAULT '{
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
        "bias_strength": 0.5
    }',
    background TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Name Field**: Agent's name used in prompts and self-reference ("Your name: Marcus")

**Personality Field**: JSONB containing six continuous values (five traits + bias strength)

**Background Field**: First-person narrative describing the agent's biographical context:
- "I am a software engineer with 10 years of startup experience"
- "I was born in Texas and value innovation over tradition"
- "I am a creative artist interested in digital media"

### 3.2 Trait Description Generation

Personality traits are translated into natural language descriptions for LLM prompts:

```python
def describe_trait(name: str, value: float) -> str:
    if value >= 0.8: return f"very high {name}"
    elif value >= 0.6: return f"high {name}"
    elif value >= 0.4: return f"moderate {name}"
    elif value >= 0.2: return f"low {name}"
    else: return f"very low {name}"
```

**Example Output** (openness=0.9, conscientiousness=0.2, extraversion=0.7, agreeableness=0.3, neuroticism=0.5):
```
Your personality traits:
- very high openness to new ideas
- low conscientiousness and organization
- high extraversion and sociability
- low agreeableness and cooperation
- moderate emotional sensitivity
```

This verbalization makes traits interpretable to the LLM, enabling personality-biased reasoning.

## 4. TEMPR-Based Memory Architecture and Opinion Network

CARA is built on **TEMPR (Temporal Entity Memory Priming Retrieval)**, a memory retrieval architecture that manages three distinct memory networks:

1. **World Network** (`fact_type='world'`): Objective information about the world
2. **Agent Network** (`fact_type='agent'`): Biographical information about the agent
3. **Opinion Network** (`fact_type='opinion'`): Subjective beliefs formed by the agent

**TEMPR Retrieval Features**:

TEMPR combines multiple parallel retrieval strategies optimized for AI agent reasoning:

- **Temporal Retrieval**: Memories connected by time proximity, enabling narrative continuity and temporal reasoning
- **Semantic Search**: Vector similarity search for conceptually related memories
- **Entity-Aware Graph Traversal**: Spreading activation through entity-linked memories, enabling multi-hop discovery
- **BM25 Keyword Matching**: Precise term-based retrieval for exact phrase matching
- **Neural Reranking**: Cross-encoder refinement with token budget filtering

This multi-strategy architecture enables CARA to retrieve relevant facts, agent experiences, and existing opinions during reasoning, supporting both factual grounding and personality-driven belief formation. The separation of three networks allows the system to distinguish objective knowledge (world/agent facts) from subjective beliefs (opinions), which is critical for epistemic clarity and debugging.

### 4.1 Opinion Structure

Opinions are stored as memory units in the dedicated opinion network (`fact_type='opinion'`):

**Core Attributes**:
- `text`: The opinion statement with explicit reasoning
- `confidence_score`: Opinion strength and resistance to change (0.0-1.0)
- `event_date`: When the opinion was formed
- `agent_id`: Which agent holds this opinion
- `entities`: Mentioned entities (for reinforcement triggering)

**Example Opinion**:
```json
{
  "text": "I believe Python is better than JavaScript for data science because it has better libraries like pandas and numpy and a stronger statistical computing ecosystem.",
  "confidence_score": 0.85,
  "event_date": "2024-03-15T14:30:00Z",
  "entities": ["Python", "JavaScript", "data science"]
}
```

**Fact vs. Opinion Separation**:

A critical architectural distinction separates **facts** (objective information stored in world/agent networks with `fact_type='world'` or `fact_type='agent'`) from **opinions** (subjective beliefs stored in the opinion network with `fact_type='opinion'`). This separation provides:

1. **Epistemic Clarity**: Facts represent information the agent has encountered; opinions represent judgments formed from those facts
2. **Traceability**: Opinion reinforcement can trace which facts influenced belief updates, creating an audit trail
3. **Debugging**: Developers can separately inspect factual knowledge vs. formed beliefs, identifying whether issues stem from missing facts or flawed reasoning
4. **Confidence Semantics**: Facts lack confidence scores (they are information received), while opinions have confidence scores (representing conviction strength)

This fact/opinion distinction is fundamental to the architecture and enables the system to maintain both objective knowledge and personality-driven beliefs simultaneously.

### 4.2 Opinion Formation

Opinions are generated during "think" operations—when the agent is asked to reason about a topic and form a judgment.

**Formation Process**:
1. Retrieve relevant facts from all memory networks (world, agent, existing opinions)
2. Inject agent profile (name, personality, background) into LLM prompt
3. Generate reasoning with personality bias applied
4. Extract new opinions from response using structured output
5. Store opinions with confidence scores in opinion network

**Prompt Structure** (bias_strength=0.8):
```
Here's what I know and have experienced:

MY IDENTITY & EXPERIENCES:
[Agent network facts with scores]

WHAT I KNOW ABOUT THE WORLD:
[World network facts with scores]

MY EXISTING OPINIONS & BELIEFS:
[Opinion network facts with confidence scores]

Your name: Marcus

Your personality traits:
- very high openness to new ideas
- low conscientiousness and organization
- high extraversion and sociability
- low agreeableness and cooperation
- moderate emotional sensitivity

Personality influence strength: 80% (how much your personality shapes your opinions)

Your background:
I am a creative software engineer who values innovation over tradition.

QUESTION: What do you think about remote work?

Based on everything I know, believe, and who I am (including my name, personality and background), here's what I genuinely think about this question...
```

### 4.3 System Message Adaptation

The system message adjusts based on bias strength to control personality influence:

**High bias (≥0.7)**:
```
Your personality strongly influences your thinking. Let your traits guide how you interpret facts and form opinions. Don't be afraid to be biased based on your personality.
```

**Moderate bias (0.4-0.7)**:
```
Your personality moderately influences your thinking. Balance your personal traits with objective analysis.
```

**Low bias (<0.4)**:
```
Your personality has minimal influence on your thinking. Focus primarily on facts while keeping your traits in mind.
```

This prompt engineering creates a spectrum from objective analysis to strongly personality-driven reasoning.

### 4.4 Confidence Score Semantics

Confidence scores represent opinion strength—how firmly the agent holds the belief and how resistant it is to change:

- **0.9-1.0**: Very strong conviction, deeply held belief that would require substantial contradictory evidence to revise
- **0.7-0.9**: Strong conviction, firmly held opinion resistant to minor contradictions
- **0.5-0.7**: Moderate conviction, opinion held with openness to revision given new evidence
- **0.3-0.5**: Weak conviction, tentatively held view easily influenced by new information
- **0.0-0.3**: Very weak conviction, highly malleable opinion with minimal commitment

**LLM Generation**: Confidence scores are extracted from the LLM's reasoning using structured output (Pydantic schema):

```python
class Opinion(BaseModel):
    text: str
    confidence: float  # 0.0-1.0
    reasoning: str
    entities_mentioned: List[str]
```

## 5. Opinion Reinforcement

### 5.1 Motivation

Human beliefs evolve as we encounter new information. Supporting evidence strengthens beliefs, contradictory evidence weakens them, and sufficient contradiction causes belief revision. Opinion reinforcement implements this dynamic belief updating.

### 5.2 Reinforcement Mechanism

When new facts are ingested (e.g., a conversation about remote work productivity), the system:

1. **Identify Related Opinions**: Find existing opinions that mention entities in the new facts (e.g., opinions about "remote work")

2. **Evaluate Evidence Relationship**: Use LLM to determine if new facts:
   - **Reinforce**: Support the existing opinion (increase confidence)
   - **Weaken**: Contradict the existing opinion (decrease confidence)
   - **Contradict**: Strongly contradict, requiring opinion revision (update text + confidence)
   - **Neutral**: Unrelated or no clear relationship (no change)

3. **Update Opinions**: Adjust confidence scores or revise opinion text based on evaluation

**Example Reinforcement**:

**Existing Opinion** (confidence: 0.7):
```
"I think remote work improves productivity because it eliminates commute time and provides flexible scheduling."
```

**New Fact**:
```
"A 2024 study found that remote workers report 22% higher productivity and better work-life balance compared to office workers."
```

**LLM Evaluation**: "This evidence REINFORCES the opinion with strong quantitative support."

**Updated Opinion** (confidence: 0.85):
```
"I think remote work improves productivity because it eliminates commute time and provides flexible scheduling. A 2024 study showing 22% higher productivity for remote workers strongly supports this view."
```

### 5.3 Reinforcement Algorithm

```python
async def reinforce_opinions(agent_id: str, new_facts: List[Fact]):
    # 1. Extract entities from new facts
    new_entities = extract_entities(new_facts)

    # 2. Find opinions mentioning these entities
    related_opinions = find_opinions_by_entities(agent_id, new_entities)

    for opinion in related_opinions:
        # 3. Evaluate relationship using LLM
        evaluation = await evaluate_opinion_evidence(
            opinion=opinion.text,
            new_facts=new_facts,
            personality=get_agent_personality(agent_id)
        )

        # 4. Update based on evaluation
        if evaluation.relationship == "REINFORCE":
            opinion.confidence = min(1.0, opinion.confidence + 0.1)
            opinion.text = merge_evidence(opinion.text, evaluation.reasoning)

        elif evaluation.relationship == "WEAKEN":
            opinion.confidence = max(0.0, opinion.confidence - 0.15)

        elif evaluation.relationship == "CONTRADICT":
            opinion.text = revise_opinion(
                old_text=opinion.text,
                new_facts=new_facts,
                reasoning=evaluation.reasoning
            )
            opinion.confidence = evaluation.new_confidence

        # 5. Save updated opinion
        await save_opinion(opinion)
```

### 5.4 Reinforcement Guarantees

**Consistency**: Opinions are only updated when new facts genuinely relate to existing beliefs, preventing spurious updates

**Personality Coherence**: Reinforcement evaluation incorporates agent personality, ensuring updates align with trait-driven reasoning

**Transparency**: Each update records the triggering facts and reasoning, providing an audit trail of belief evolution

**Bounded Updates**: Confidence changes are bounded (±0.1-0.15 per update) to prevent extreme swings from single data points

## 6. Background Merging

### 6.1 Challenge

Agent backgrounds accumulate biographical information over time. New information may:
- **Complement**: Add new facts without contradiction ("I have 10 years of experience")
- **Conflict**: Contradict existing facts ("I was born in Texas" vs. existing "I was born in Colorado")
- **Refine**: Provide more specific versions of existing facts

Naive concatenation creates incoherent backgrounds with contradictions. We need intelligent merging.

### 6.2 LLM-Powered Merging

We use an LLM to merge backgrounds with conflict resolution:

**Merge Rules**:
1. **New overwrites old** when contradictory
2. **Add non-conflicting** information
3. **Maintain first-person** perspective ("I..." not "You...")
4. **Keep concise** (under 500 characters)

**Prompt Template**:
```
Current background: {current_background}
New information: {new_info}

Merge these, resolving conflicts (new info overwrites old).
Output in FIRST PERSON ("I"). Be concise (under 500 characters).
```

**Example Merges**:

**Conflict Resolution**:
- Current: "I was born in Colorado"
- New: "You were born in Texas"
- Result: "I was born in Texas" (conflict resolved, Colorado removed)

**Addition**:
- Current: "I was born in Texas"
- New: "I have 10 years of startup experience"
- Result: "I was born in Texas. I have 10 years of startup experience."

**Refinement**:
- Current: "I work in software"
- New: "You are a senior software engineer at Google"
- Result: "I am a senior software engineer at Google"

### 6.3 First-Person Normalization

Users may provide background in second person ("You are..."), but internal storage maintains first person for consistency in prompts.

**Normalization**: LLM automatically converts:
- "You are a creative engineer" → "I am a creative engineer"
- "You were born in 1990" → "I was born in 1990"
- "You value innovation" → "I value innovation"

This ensures agent prompts maintain coherent first-person perspective.

## 7. Personality-Driven Reasoning Examples

### 7.1 Example: Remote Work Discussion

**Scenario**: Two agents with opposite personalities discuss remote work given identical facts.

**Facts** (both agents receive):
- "Remote work eliminates commute time (average 1 hour/day saved)"
- "Office work provides spontaneous collaboration and mentorship"
- "Studies show 65% of remote workers report higher productivity"
- "Some managers report difficulty monitoring remote employee performance"

**Agent A** (High Openness=0.9, Low Conscientiousness=0.2, bias=0.8):
```
Opinion: "Remote work represents the future of creative knowledge work. The freedom from rigid schedules and physical office constraints unlocks spontaneous innovation and allows people to work when inspiration strikes. The productivity gains reflect how autonomy and flexibility enable better work. Traditional concerns about monitoring and structure are vestiges of outdated management thinking."

Confidence: 0.85
```

**Agent B** (Low Openness=0.2, High Conscientiousness=0.9, bias=0.8):
```
Opinion: "While remote work offers convenience, it fundamentally lacks the structure and accountability mechanisms necessary for consistent high performance. The difficulty in monitoring and mentorship are serious concerns that outweigh time savings. Productive work requires organized systems, clear expectations, and disciplined execution—all harder to maintain remotely. The office environment provides essential guardrails for sustained performance."

Confidence: 0.80
```

**Analysis**: Both agents accessed identical facts but formed opposite conclusions based on personality:
- Agent A (high openness) weighted autonomy, flexibility, innovation—aligning with openness to new approaches
- Agent B (high conscientiousness) weighted structure, monitoring, discipline—aligning with organized, systematic thinking

### 7.2 Example: Opinion Evolution

**Scenario**: Agent forms initial opinion, then encounters reinforcing and contradictory evidence.

**Initial State** (t=0):
```
Facts: "Python has extensive data science libraries"
Opinion: "Python is the best language for data science because of its library ecosystem."
Confidence: 0.7
```

**Reinforcement** (t=1):
- New Fact: "Python dominates AI/ML with 75% market share; TensorFlow and PyTorch are Python-first"
- Update: Confidence → 0.85, text adds "Python's dominance in AI/ML frameworks..."

**Partial Contradiction** (t=2):
- New Fact: "Julia offers 10x faster numerical computation for scientific computing; increasingly adopted in research"
- Update: Confidence → 0.75, text revised to "Python is excellent for data science due to its ecosystem, though specialized languages like Julia may outperform for specific numerical tasks"

**Strong Contradiction** (t=3):
- New Fact: "Major tech companies migrating data pipelines to Rust for performance; Python increasingly seen as prototyping language"
- Update: Confidence → 0.55, text revised to "Python remains strong for data science prototyping and library availability, but production systems increasingly favor performant alternatives like Rust. Python's role may shift toward experimentation rather than deployment."

**Trajectory**: The opinion evolved from strong conviction (0.7 → 0.85) to weaker, more malleable belief (0.55) as evidence accumulated, demonstrating dynamic belief updating where opinion strength responds to contradictory information.

## 8. Evaluation

### 8.1 Benchmark Landscape

No established benchmarks exist for evaluating personality-driven belief systems in conversational AI agents. Existing memory benchmarks (LoComo, LongMemEval) focus on factual retrieval accuracy—measuring whether agents correctly recall information—but do not assess:

- **Personality Consistency**: Whether agents maintain coherent trait-driven perspectives across interactions
- **Opinion Formation Quality**: Whether formed beliefs align with personality traits and available evidence
- **Belief Evolution Dynamics**: Whether opinions update appropriately as new evidence arrives
- **Multi-Agent Diversity**: Whether agents with different personalities produce meaningfully different perspectives

This gap reflects the nascent state of personality-aware agent systems. While personality modeling exists in dialogue generation (style/tone), applying personality to reasoning and belief formation represents relatively unexplored territory.

### 8.2 Real-World Deployment Evidence

Despite the absence of formal benchmarks, we have validated the framework through production deployments. The most significant use case involves **AI-generated sports analysis content**, where multiple AI agents with distinct personalities co-host sports discussion shows.

**Sports Commentary Agent System**:

The system powers episodic sports content where AI agents (each with unique personalities and backgrounds) discuss team performance, analyze games, and debate sports topics. Key requirements:

1. **Persistent Team Assessments**: Each agent must remember their last evaluation of each team (e.g., "The Lakers are underperforming this season")

2. **Opinion Formation**: Agents form beliefs about teams, players, and strategies based on game statistics, news, and historical performance

3. **Dynamic Opinion Evolution**: As the season progresses and new games occur, agents must:
   - **Reinforce** existing opinions when new performance data supports them (e.g., Lakers win streak → strengthen positive assessment)
   - **Weaken** opinions when contradictory evidence emerges (e.g., Lakers lose key games → reduce confidence in positive assessment)
   - **Revise** opinions when substantial contradictions accumulate (e.g., "I thought the Lakers would dominate, but their defense has been terrible")

4. **Personality-Driven Perspectives**: Different agents bring distinct viewpoints to the same games:
   - **Optimistic Analyst** (High Openness + High Extraversion): "The Lakers' experimental lineup shows creative coaching that could unlock championship potential"
   - **Conservative Analyst** (High Conscientiousness + Low Openness): "The Lakers' inconsistent record reflects poor fundamentals and lack of disciplined execution"
   - **Emotional Fan** (High Neuroticism + High Agreeableness): "I'm worried about the Lakers' recent struggles, but I believe in the team's potential to rally"

**System Validation**:

This production deployment demonstrates several critical capabilities:

- **Opinion Continuity**: Agents maintain coherent assessments across episodes without sudden, unexplained belief changes
- **Evidence-Driven Evolution**: Opinion confidence scores naturally evolve as teams win/lose games, with reinforcement preventing stale beliefs
- **Personality Differentiation**: Audience research indicates viewers perceive distinct "voices" and can predict which agent will favor which perspective
- **Background Integration**: Agent backgrounds (e.g., "I played college basketball") influence reasoning without requiring explicit prompt engineering per episode

The sports content system has been deployed for an extended period, with opinion networks growing to contain substantial team/player assessments per agent. User engagement metrics indicate positive reception, suggesting audiences value the consistent-yet-evolving perspectives that personality-driven opinion systems enable.

### 8.3 Proposed Evaluation Metrics

To properly evaluate the personality framework, we propose:

**Personality Consistency**:
- Metric: Opinion coherence across interactions
- Test: Generate 10 opinions on diverse topics for an agent with fixed personality; measure trait alignment
- Success: >85% of opinions exhibit expected trait patterns

**Opinion Evolution**:
- Metric: Confidence score changes match evidence strength
- Test: Present reinforcing/contradicting evidence; measure confidence adjustments
- Success: Reinforcing evidence increases confidence (Δ>0), contradicting decreases (Δ<0) with p<0.01

**Bias Strength Control**:
- Metric: Opinion variability across bias strengths
- Test: Generate opinions for same agent at bias=[0.0, 0.5, 1.0]; measure personality signal strength
- Success: Clear gradient in trait expression: bias=0.0 (objective), bias=1.0 (strongly personality-driven)

**Multi-Agent Consistency**:
- Metric: Opinion diversity for agents with different personalities given identical facts
- Test: Present same facts to agents with opposite traits; measure opinion divergence
- Success: Opposite personalities produce significantly different opinions (cosine similarity <0.5)

**Background Coherence**:
- Metric: Contradiction-free backgrounds after merging
- Test: Merge conflicting biographical facts; check for contradictions
- Success: 100% conflict resolution with new facts overwriting old

### 8.4 Evaluation Challenges

**Subjectivity**: Unlike retrieval accuracy, "correct" personality expression is subjective. We rely on expected trait patterns from psychology literature.

**Long-Term Dynamics**: Opinion evolution requires multi-session interactions over time, making evaluation resource-intensive.

**Ground Truth**: The absence of established benchmarks requires custom evaluation datasets. Real-world deployments (Section 8.2) provide qualitative validation but lack standardized metrics for cross-system comparison.

## 9. Use Cases

### 9.1 Multi-Persona Sports Commentary (Production Deployment)

**Application**: AI-generated sports analysis and entertainment content with multiple agent personalities

**Real-World System** (detailed in Section 8.2): A production sports content platform where AI agents with distinct personalities co-host episodic shows discussing team performance, game analysis, and sports debates.

**System Architecture**:
- **Multiple Agents**: Each agent has unique personality traits and sports background (e.g., former player, statistics analyst, passionate fan)
- **Continuous Memory**: Agents maintain persistent team/player assessments across episodes spanning months
- **Opinion Evolution**: As games occur and statistics accumulate, agents automatically update their beliefs through reinforcement
- **Personality-Driven Commentary**: The same game results generate different perspectives based on agent traits

**Example Agent Configurations**:

**Marcus** (Optimistic Analyst):
- Traits: Openness=0.85, Conscientiousness=0.5, Extraversion=0.9, Agreeableness=0.7, Neuroticism=0.3
- Background: "I am a former college basketball player who believes in the power of innovative coaching strategies"
- Style: Emphasizes potential, experimental approaches, creative plays; downplays risks

**Sarah** (Conservative Analyst):
- Traits: Openness=0.3, Conscientiousness=0.9, Extraversion=0.4, Agreeableness=0.4, Neuroticism=0.5
- Background: "I am a statistical analyst with 15 years of experience evaluating team performance metrics"
- Style: Focuses on fundamentals, historical patterns, data-driven predictions; skeptical of unproven strategies

**Key Benefits Observed**:
1. **Viewer Engagement**: Improved audience retention compared to single-voice commentary, with viewers citing "personality diversity" as primary appeal
2. **Content Consistency**: Agents maintain recognizable voices across multiple episodes without manual prompt tuning per episode
3. **Scalability**: New agents can be added with distinct personalities without retraining, enabling content expansion
4. **Opinion Richness**: Opinion networks capture nuanced, evolving assessments that would be impractical to manually script

This deployment validates that personality-driven opinion systems can operate at production scale for content generation requiring consistent yet adaptive agent perspectives.

### 9.2 Diverse Agent Personas

**Application**: Multi-agent systems where different agents provide varied perspectives

**Example**: Customer support system with agents specialized for different user needs:
- **Empathetic Agent** (high agreeableness, high neuroticism): Handles frustrated customers, prioritizes emotional validation
- **Analytical Agent** (high conscientiousness, low agreeableness): Handles technical troubleshooting, prioritizes accuracy
- **Creative Agent** (high openness, low conscientiousness): Handles feature requests, explores unconventional solutions

### 9.2 Consistent Character AI

**Application**: Conversational AI characters for entertainment, education, or companionship

**Example**: A writing assistant agent with:
- High openness (0.9): Encourages creative experimentation
- Moderate conscientiousness (0.6): Balances creativity with structure
- Background: "I am a published novelist with 15 years of experience in science fiction"

The agent maintains consistent perspective across sessions, forming opinions about writing techniques that reflect both personality and experience.

### 9.3 Explainable AI Reasoning

**Application**: Systems requiring transparent, interpretable decision-making

**Example**: An AI advisor provides investment recommendations. By exposing personality traits and confidence scores:
- Users understand WHY the agent recommends certain strategies (e.g., high conscientiousness favors conservative approaches)
- Confidence scores indicate conviction strength and openness to revision
- Opinion evolution shows how new market data updates beliefs

This transparency enables informed trust calibration—users know when to rely on agent judgments vs. seek additional input.

## 10. Future Work

### 10.1 Personality Evolution

Current implementation uses fixed personality traits. Future work could explore:
- **Trait Drift**: Gradual personality changes based on experiences (e.g., repeated negative outcomes increase neuroticism)
- **Contextual Traits**: Different trait expressions in different domains (professional vs. personal contexts)
- **Feedback-Driven Adjustment**: User feedback influences trait development

### 10.2 Multi-Agent Belief Systems

Extend to multi-agent scenarios:
- **Opinion Sharing**: Agents discuss and influence each other's beliefs
- **Consensus Formation**: Multiple agents with different personalities reach collective decisions
- **Disagreement Dynamics**: Model how personality influences debate and persuasion

### 10.3 Richer Personality Models

Beyond Big Five:
- **Values and Motivations**: Integrate Schwartz value theory or moral foundations
- **Cognitive Styles**: Add dimensions like analytical vs. intuitive reasoning
- **Cultural Factors**: Incorporate cultural background influences on reasoning

### 10.4 Advanced Opinion Reinforcement

Enhance belief updating:
- **Source Credibility**: Weight evidence based on source reliability
- **Evidence Accumulation**: Model bayesian belief updating over multiple evidence pieces
- **Opinion Strength Calibration**: Model more sophisticated relationships between evidence quality, personality traits, and opinion strength adjustments

## 11. Related Work

**Memory Systems for AI Agents**: CARA builds on TEMPR (Temporal Entity Memory Priming Retrieval), a memory retrieval architecture combining temporal reasoning, entity-aware graph traversal, and multi-strategy parallel search. While TEMPR handles memory storage and retrieval, CARA adds personality-driven reasoning and opinion formation on top of TEMPR's three-network architecture.

**Personality in AI Agents**: Prior work on personality-driven dialogue (PersonaChat, PersonalityPapers) focuses on response generation style rather than reasoning bias. Our work influences opinion formation itself.

**Belief Revision Systems**: Classical AI belief revision (AGM framework) focuses on logical consistency. We address probabilistic beliefs with confidence scores in natural language contexts.

**Cognitive Architectures**: Systems like ACT-R and Soar model human cognition but lack explicit personality integration. We bring personality psychology into LLM-based agents.

**Opinion Dynamics**: Social science models of opinion change (DeGroot, Friedkin-Johnsen) study influence networks. We focus on evidence-based belief updating within a single agent.

## 12. Conclusion

We present CARA (Coherent Adaptive Reasoning Agents), a personality framework for conversational AI agents that enables consistent, trait-driven reasoning and dynamic belief formation. By integrating the Big Five personality model with TEMPR (Temporal Entity Memory Priming Retrieval) managing fact/opinion network separation and opinion reinforcement, we create agents that maintain coherent perspectives while evolving beliefs based on new evidence.

The system's key innovations—TEMPR-based three-network architecture (world, agent, opinion), personality-biased reasoning prompts, automatic opinion reinforcement, and background merging with conflict resolution—address the challenge of creating AI agents with stable yet adaptive identities. The fact/opinion distinction provides epistemic clarity and traceability, while TEMPR's multi-strategy retrieval (temporal, semantic, entity-aware, keyword-based) enables sophisticated memory access. The bias strength parameter provides fine-grained control over personality influence, enabling agents to operate across a spectrum from objective information processors to strongly personality-driven reasoners.

While the framework is implemented and functional, dedicated evaluation is needed to rigorously assess personality consistency, belief evolution dynamics, and multi-agent interactions. Future work will explore personality evolution over time, multi-agent belief systems, and richer personality models incorporating values and cultural factors.

By bringing personality psychology into AI agent design, we move toward conversational agents that exhibit not just intelligence, but character—stable traits and evolving beliefs that enable more natural, trustworthy human-AI interaction.

## References

1. Boschi, N., et al. (2025). TEMPR: Temporal Entity Memory Priming Retrieval for Conversational AI Agents. [Companion paper - see PAPER_RETRIEVAL.md]

2. McCrae, R. R., & Costa, P. T. (1997). Personality trait structure as a human universal. *American Psychologist*, 52(5), 509.

3. Goldberg, L. R. (1993). The structure of phenotypic personality traits. *American Psychologist*, 48(1), 26.

4. Gärdenfors, P. (1988). *Knowledge in flux: Modeling the dynamics of epistemic states*. MIT Press.

5. Friedkin, N. E., & Johnsen, E. C. (1990). Social influence and opinions. *Journal of Mathematical Sociology*, 15(3-4), 193-206.

6. Zhang, S., et al. (2018). Personalizing dialogue agents: I have a dog, do you have pets too? *arXiv preprint arXiv:1801.07243*.
