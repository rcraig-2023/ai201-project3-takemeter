# TakeMeter Planning Specification: Hacker News Discourse Classifier

## 1. Community Focus
This project evaluates text discourse on **Hacker News (HN)**. Hacker News is an ideal environment for a classification task because its user base is composed of highly opinionated software engineers, founders, and tech enthusiasts. The discourse quality varies dramatically: a single thread can contain a brilliant, multi-paragraph engineering breakdown side-by-side with a dismissive, single-sentence cynical quip or a basic query. This extreme variation in depth, tone, and substance creates a challenging and highly practical landscape for text classification.

## 2. Label Taxonomy
The classifier uses a three-label system designed to capture the structural intent and quality of community contributions:

* **`technical_analysis`**: The comment makes a structured, informative argument or explanation about technology, business, or engineering, backed by specific details, personal industry experience, or technical mechanics.
  * *Example 1:* "We migrated our production database from standard Postgres to a distributed setup using CockroachDB last year. The primary headache wasn't data replication; it was adjusting our application layer's retry logic to handle transient transaction conflicts gracefully."
  * *Example 2:* "This exploit relies on a classic buffer overflow vulnerability in the network stack where bounds checking is omitted. By sending a malformed UDP packet with an oversized payload, an attacker overrides the instruction pointer."
* **`dismissive_take`**: The comment expresses a cynical, shallow, or reactionary opinion that criticizes or dismisses a technology, project, or concept without offering constructive reasoning, substantive context, or technical evidence.
  * *Example 1:* "Just what the world needs, yet another bloated JavaScript framework trying to reinvent the wheel. Give it two years and everyone will move on to the next fad."
  * *Example 2:* "This entire startup looks like an obvious cash grab riding the AI hype wave. There is zero actual proprietary tech under the hood."
* **`clarifying_question`**: The comment is explicitly framed around gathering more information, requesting clarification on a technical point, or seeking advice on the topic being discussed.
  * *Example 1:* "Could you expand on how you managed state synchronization across regions without introducing massive latency overhead for your European users?"
  * *Example 2:* "Does this specific security patch apply to older LTS versions of Node, or are those already deprecated?"

## 3. Hard Edge Cases & Decision Rules

* **The Ambiguity:** A comment starts with a highly cynical, sarcastic sentence (`dismissive_take`) but immediately pivots into a deeply technical breakdown of *why* the product fails or succeeds (`technical_analysis`).
* **Decision Rule:** If a comment provides verifiable technical context, metrics, architectural trade-offs, or concrete engineering explanations, it must be labeled `technical_analysis`, even if the overall tone is highly negative, snarky, or dismissive. A comment is only labeled a `dismissive_take` if it lacks structural, substantive reasoning. 

### Actual Annotated Edge Cases
The following 3 specific examples from the dataset gave genuine pause during the annotation process and were resolved using the taxonomy rules:

1. **Case: Tonal Cynicism vs. Structural Context**
   * **Text:** `"TBH I think mesh routers are overhyped garbage. They don't work well, and pollute the spectrum, and are a really poor substitute for cables. The only reason why they sell well is because people will buy anything as long as they don't need to lay cables."`
   * **Resolution:** `dismissive_take`
   * **Reasoning:** While the post mentions technical concepts ("pollute the spectrum", "mesh routers"), it uses them entirely as buzzwords to anchor a cynical rant about consumer behavior rather than breaking down an actual engineering architecture or networking trade-off.

2. **Case: Rhetorical Questions as Criticism**
   * **Text:** `"Absolutely ridiculous feature. Who actually asked for this? It feels like the product managers just needed something to justify their salaries this quarter."`
   * **Resolution:** `dismissive_take`
   * **Reasoning:** Although this post contains an explicit question mark ("Who actually asked for this?"), the structural intent is entirely critical and dismissive rather than a genuine quest for informational clarity. It was classified as a dismissive take rather than a clarifying question.

3. **Case: High Frustration but Substantive Claims**
   * **Text:** `"Kevin was famous for being mistreated by the DoJ and writing some books which were perhaps not particularly true in hindsight... you shouldn't envy Kevin's life. For the rest: nothing's stopping you from having fun, regardless of age."`
   * **Resolution:** `technical_analysis`
   * **Reasoning:** The tone borders on an emotional community vent, but the comment provides highly specific, verifiable historical context regarding a public figure's legal case and books. Per the decision rule, structural substance overrides a frustrated tone.

## 4. Data Collection Plan
* **Source:** Text comments extracted via the public Hacker News Algolia Search API.
* **Target:** A baseline pool of 200 rows (filtered for length greater than 100 characters to eliminate trivial one-word replies). 
* **Target Distribution:** Aiming for a minimum of 20% representation per class (roughly 40+ examples per label).
* **Imbalance Mitigation:** If any class (e.g., `clarifying_question`) falls below 20% after the pre-labeling and manual audit, a secondary programmatic query filtering for comments containing question marks (`?`) will be executed to selectively harvest and balance the underrepresented label.

## 5. Evaluation Metrics
* **Primary Metrics:** Overall Accuracy, alongside Class-Specific **F1-Score** (harmonic mean of precision and recall).
* **Justification:** Accuracy alone fails if the dataset leans slightly imbalanced. We must isolate **Precision** (to ensure that when the model predicts a post is a high-value `technical_analysis`, it isn't polluting it with lazy snark) and **Recall** (to check if we are missing genuine technical insights because they happen to be short). The F1-Score acts as the definitive performance metric for each distinct boundary.

## 6. Definition of Success
* **Threshold:** A minimum overall Accuracy of **70%** on the locked test split, with no individual class F1-score falling below **0.60**. 
* **Real-World Utility:** This performance level is sufficient to act as an automated browser-extension filter that highlights high-substance technical content while automatically collapsing unhelpful, low-effort rants for an end-user reading long tech forums.

---

## 7. AI Tool Plan

### Label Stress-Testing
Prior to completing manual verification, an LLM will be prompted to generate ambiguous edge-case responses specifically designed to straddle the boundary between `technical_analysis` and `dismissive_take`. These synthetic prompts will be tested against our decision rule to ensure the boundaries do not overlap or require a fourth label.

### Annotation Assistance
To accelerate development, an LLM (Gemini/Groq) will be used to generate initial pre-labels for all raw data based on the taxonomy definitions above. 
* **Tracking Protocol:** A dedicated binary column named `is_edited` will be appended to the local dataset. Any row where the human reviewer overrides or modifies the AI-generated pre-label will be marked as `True` to track and transparently report human-in-the-loop discrepancies in the final report.

### Failure Analysis
Following evaluation in the Colab notebook, all misclassified text examples from the test split will be fed back into an LLM. The model will be tasked with identifying semantic patterns among the failures (e.g., determining if the model consistently fails on short sentences containing structural code snippets, or if it struggles heavily with subtle developer sarcasm). These patterns will be cross-verified manually before compiling the final README.