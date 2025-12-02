# Technical Guide: Building an Autonomous Brand Monitoring Agent on Google Cloud

**Target Audience:** Google Cloud Architects & Senior Developers
**Version:** 1.0
**Date:** December 2025

## 1. Executive Summary

This guide details the architecture and implementation of a serverless, autonomous Brand Monitoring Agent. The system leverages **Vertex AI Gemini 2.5 Pro** for reasoning and **Grounding with Google Search** for factual verification, orchestrating a workflow that monitors brand sentiment, analyzes financial news, and delivers actionable executive summaries via email.

## 2. Solution Architecture

The solution is built on a **Serverless Event-Driven Architecture** to ensure scalability, low maintenance, and cost-efficiency.

### 2.1 High-Level Diagram

```mermaid
graph TD
    Scheduler[Cloud Scheduler] -->|Trigger (CRON)| RunJob[Cloud Run Job]
    
    subgraph "Cloud Run Execution Environment"
        Agent[Python Agent Logic]
        Tools[Tool Definitions]
    end
    
    RunJob --> Agent
    
    Agent -->|1. Search & Grounding| Vertex[Vertex AI (Gemini 2.5 Pro)]
    Vertex -->|Grounding| GoogleSearch[Google Search]
    
    Agent -->|2. Specialized Search| SerpApi[SerpApi (Fallback/Social)]
    
    Agent -->|3. Retrieve Secrets| Secrets[Secret Manager]
    
    Agent -->|4. Send Report| Gmail[SMTP / Gmail]
    
    subgraph "Data & Context"
        Prompts[YAML Prompts]
    end
    
    Agent -.-> Prompts
```

### 2.2 Key Components

| Component | Purpose | Configuration Highlights |
| :--- | :--- | :--- |
| **Cloud Run Jobs** | Compute | Serverless execution, 512MB-1GB RAM, 60s-300s timeout. Ideal for batch processes. |
| **Vertex AI** | Intelligence | Model: `gemini-2.5-pro`. Feature: **Grounding with Google Search** for hallucination reduction. |
| **Cloud Scheduler** | Orchestration | CRON: `0 8 * * 1` (Weekly). Timezone: `America/Santiago`. Triggers Cloud Run Job via HTTP. |
| **Secret Manager** | Security | Stores API keys (`SERPAPI_KEY`) and credentials (`GMAIL_PASSWORD`). No hardcoded secrets. |
| **Artifact Registry** | Delivery | Stores the Docker container image for the agent. |

## 3. Implementation Details

### 3.1 The "Reasoning Engine" (Agent Logic)

The core agent is a Python application that follows a **Chain-of-Thought** execution flow:

1.  **Context Loading**: Loads persona (`persona.yaml`), instructions (`instructions.yaml`), and rules (`rules.yaml`) to define the agent's behavior.
2.  **Information Retrieval**:
    *   **Primary**: Vertex AI Grounding (Google Search) is used implicitly during generation to verify facts.
    *   **Secondary**: `SerpApi` is used for specific structured data gathering (e.g., social media mentions count, specific financial news headers) to feed into the context.
3.  **Synthesis & Analysis**:
    *   The gathered data is passed to Gemini 2.5 Pro.
    *   The model generates an HTML report following strict formatting rules (Sentiment Color Coding, "Read More" links).
4.  **Delivery**:
    *   The HTML content is wrapped in a branded template and sent via SMTP.

### 3.2 Grounding Strategy

To ensure the "Executive Summary" is trustworthy, we implement **Grounding with Google Search**.

*   **Why?** LLMs can hallucinate. Grounding forces the model to cite sources.
*   **Implementation**:
    ```python
    # Workaround for current SDK compatibility
    tools = [Tool.from_dict({'google_search': {}})]
    model.generate_content(prompt, tools=tools)
    ```
*   **Verification**: The system logs `grounding_metadata` to confirm search queries used (e.g., `"Banco de Chile financial news"`).

## 4. Deployment Strategy

We use a **GitOps-style** approach with a consolidated deployment script (`deploy_brand.sh`).

### 4.1 Containerization

*   **Base Image**: `python:3.11-slim` for minimal footprint.
*   **Dependencies**: `google-cloud-aiplatform`, `google-cloud-secret-manager`, `markdown`.
*   **Security**: Non-root user (recommended for production), environment variables for non-sensitive config.

### 4.2 Infrastructure as Code (Scripted)

The deployment script performs the following atomic operations:
1.  **Build**: `gcloud builds submit` to Artifact Registry.
2.  **Deploy Job**: `gcloud run jobs update` with:
    *   `--set-secrets`: Mounting Secret Manager versions as env vars.
    *   `--set-env-vars`: Setting project ID and configuration.
3.  **Schedule**: `gcloud scheduler jobs update` to trigger the Cloud Run Job.

## 5. Security Best Practices

1.  **Identity & Access Management (IAM)**:
    *   The Cloud Run Service Account (`[project-number]-compute@...`) must have:
        *   `Vertex AI User`
        *   `Secret Manager Secret Accessor`
2.  **Secret Management**:
    *   **NEVER** commit keys to Git.
    *   Use `os.environ.get()` in code.
    *   Inject secrets at runtime via Cloud Run integration.
3.  **Network**:
    *   Cloud Run services default to public endpoints (for invocation). For stricter security, restrict ingress to `Internal` and allow only Cloud Scheduler to invoke via OIDC tokens.

## 6. Monitoring & Observability

*   **Cloud Logging**: All agent `print()` statements and `logging` outputs are captured automatically.
*   **Key Metrics to Watch**:
    *   *Job Duration*: Ensure it doesn't exceed timeout (default 10m).
    *   *Error Rate*: Monitor for non-zero exit codes.
    *   *Vertex AI Quotas*: Monitor `GenerateContent` requests per minute.

## 7. Future Extensibility

*   **Multi-Brand Support**: Refactor `test_agent.py` to accept `--brand` arguments and create parallel Scheduler jobs.
*   **Data Persistence**: Integrate **Firestore** to store historical sentiment trends and generate "Week-over-Week" comparisons.
*   **Instant Alerts**: Add a "Crisis Mode" that triggers an immediate run if a high volume of negative sentiment is detected via a separate stream (e.g., Pub/Sub).
