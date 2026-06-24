# TakeMeter: Hacker News Discourse Classifier

## 📌 Project Overview
This project implements a text classifier designed to evaluate discourse quality on Hacker News. Tech community discourse often blends highly structured engineering arguments with cynical "hot takes" and genuine requests for clarification. The goal of this classifier is to separate substantive technical analysis from low-effort dismissiveness and logistical questions.

**Base Model:** `distilbert-base-uncased`
**Fine-Tuning Platform:** Google Colab (T4 GPU)
**Baseline Model:** `llama-3.3-70b-versatile` (via Groq)

---

## 🏷️ Label Taxonomy
The classifier evaluates text against three mutually exclusive labels:

* **`technical_analysis`**: The comment makes a structured, informative argument or explanation about technology, business, or engineering, backed by specific details, personal industry experience, or technical mechanics.
* **`dismissive_take`**: The comment expresses a cynical, shallow, or reactionary opinion that criticizes or dismisses a technology, project, or concept without offering constructive reasoning, substantive context, or technical evidence.
* **`clarifying_question`**: The comment is explicitly framed around gathering more information, requesting clarification on a technical point, or seeking advice on the topic being discussed.

---

## 🗄️ Dataset Collection and Annotation
* **Source:** 200 public comments scraped from Hacker News using the Algolia Search API.
* **Filtering:** Comments were restricted to >100 characters to remove trivial, one-word replies.
* **Balancing:** Initial collection yielded heavily imbalanced data (74% `technical_analysis`). The dataset was manually re-balanced by extracting targeted `dismissive_take` and `clarifying_question` posts.
* **Final Distribution:** 128 `technical_analysis` (64%), 47 `dismissive_take` (23.5%), 25 `clarifying_question` (12.5%).
* **Annotation Process:** An initial pass was pre-labeled using Groq (`llama-3.3-70b-versatile`) via a Python script, followed by manual human review to verify accuracy and document difficult edge cases in the `notes` column.

---

## ⚙️ Fine-Tuning Setup
The model was fine-tuned using the HuggingFace `transformers` and `datasets` libraries.

* **Model:** `distilbert-base-uncased`
* **Epochs:** 3
* **Learning Rate:** 2e-5
* **Batch Size:** 16
* **Rationale:** Default hyperparameters were maintained because 3 epochs at a 2e-5 learning rate is the standard defensive baseline to prevent severe overfitting on a small dataset of only 140 training examples.

---

## 📊 Evaluation Report

### Overall Performance Comparison
| Model | Overall Accuracy |
| :--- | :--- |
| **Zero-Shot Baseline (Groq)** | 83.3% |
| **Fine-Tuned DistilBERT** | 63.3% |

*Note: The fine-tuning process resulted in a 20.0% regression compared to the zero-shot baseline.*

### Per-Class Metrics (F1-Score)
| Label | Baseline F1 | Fine-Tuned F1 |
| :--- | :--- | :--- |
| `technical_analysis` | 0.85 | 0.77 |
| `dismissive_take` | 0.78 | 0.22 |
| `clarifying_question` | 0.89 | 0.00 |

### Fine-Tuned Model Confusion Matrix (Test Set)
| True \ Predicted | `technical_analysis` | `dismissive_take` | `clarifying_question` |
| :--- | :--- | :--- | :--- |
| **`technical_analysis`** | **18** | 1 | 0 |
| **`dismissive_take`** | 6 | **1** | 0 |
| **`clarifying_question`** | 4 | 0 | **0** |

*(A visual `.png` of this matrix is also committed to the repository).*

---

## 🔍 Failure Analysis

The fine-tuned model performed worse than the baseline, heavily over-predicting the majority class (`technical_analysis`). Here are 3 specific failures:

1. **Missing Interrogative Structures (Class Collapse)**
   * **Text:** *"Can someone use this on Elon's 'my heart goes out to you' video, and compare it to... similar gestures. Would be interested to see exactly how close it is."*
   * **True Label:** `clarifying_question` | **Predicted:** `technical_analysis`
   * **Why it failed:** The model completely failed to recognize the clear question structure ("Can someone use this..."). Because the `clarifying_question` class only had 17 training examples, the model suffered from class collapse and defaulted to the majority class.
2. **Confusing Informal Formatting with Cynicism**
   * **Text:** *"Recently - from YT recommended - I learned about Glauber's salt (sodium sulfate). Glauber's salt is a PCM phase-change material that melts at 90F / 32.4C and starts absorbing thermal energy."*
   * **True Label:** `technical_analysis` | **Predicted:** `dismissive_take`
   * **Why it failed:** This is a purely informational post, but the model likely triggered on informal abbreviations ("YT") or the conversational opener. It lacked the vocabulary depth to understand that informal framing can precede factual statements.
3. **Over-associating Vocabulary with Analysis**
   * **Text:** *"It's not a capital 'S' scam in a legal sense, but it's a scam in that they are playing a trick on you by jacking the price way up and relying on your ignorance."*
   * **True Label:** `dismissive_take` | **Predicted:** `technical_analysis`
   * **Why it failed:** The post is highly cynical and dismissive, lacking structural evidence. However, it uses semi-formal vocabulary ("legal sense", "ignorance"). The model incorrectly learned that longer, formal-sounding words automatically equate to `technical_analysis`.

### Reflection: Intended vs. Learned Behavior
I intended the model to separate structural, evidence-backed arguments from shallow complaints. Instead, due to data starvation (only 140 training examples), the DistilBERT model learned a much lazier boundary. It overfitted to the majority class and associated formal vocabulary with `technical_analysis`, while completely forgetting how to identify questions. Conversely, the zero-shot baseline (Groq) had the vast world-knowledge to catch all the questions, but struggled with tone—often misclassifying a technical analysis as a dismissive take simply because the author sounded frustrated. 

---

## 📝 Sample Classifications
Here is a sample of how the fine-tuned model predicts novel text:

| Post Text | Predicted Label | Confidence | Reasoning |
| :--- | :--- | :--- | :--- |
| *"The main reason why CBTC is so expensive is MTA is installing 2 signaling systems while ripping out the old one..."* | `technical_analysis` | 89% | **Reasonable.** The model correctly identifies technical acronyms and structural reasoning. |
| *"Just another completely unnecessary abstraction layer to hide the fact that nobody actually knows how to write raw SQL anymore."* | `dismissive_take` | 55% | **Reasonable.** The model catches the distinct lack of technical evidence alongside cynical phrasing. |
| *"Who actually asked for this? It feels like the product managers just needed something to justify their salaries this quarter."* | `technical_analysis` | 68% | **Incorrect.** The model completely misses the cynical framing and assigns the majority class. |

---

## 🛠️ Spec Reflection
**How the spec helped:** Writing out the hard edge cases and defining the decision rule *before* annotating forced me to realize that tone and structure are completely separate. If I hadn't defined that boundary early, my annotation would have been wildly inconsistent.
**Where implementation diverged:** I planned to use purely random scraping, but I realized this created massive class imbalance (too much analysis, almost no questions). I had to pivot and intentionally query Hacker News for specific keyword strings (like "?") to manually force balance in the dataset.

---

## 🤖 AI Usage Disclosure
* **Annotation Assistance:** I utilized a Python script generated by Gemini calling the Groq API (`llama-3.3-70b-versatile`) to generate initial pre-labels for the 200 raw text examples based on my taxonomy prompt. I then manually reviewed the CSV, overwriting incorrect labels and adding edge-case notes by hand.
* **Failure Analysis/Pattern Recognition:** I fed the misclassified outputs from the Colab evaluation back to Gemini, asking it to identify common semantic patterns in the errors. It correctly pointed out the model's tendency to over-associate long vocabulary words with the `technical_analysis` label, which I then manually verified against the test set.