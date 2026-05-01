# iac-diff-engine

A semantic diff engine for Infrastructure-as-Code (Terraform) that goes beyond line-by-line diffs — it understands **what changed**, **what it affects**, and **how risky it is**.

Built with a resource dependency graph, BFS-based blast radius computation, and LLM-powered risk classification.

---

## The problem

Standard `terraform plan` tells you *which lines changed*. It does not tell you:
- Which downstream resources are affected by a change
- Whether a change opens a security vulnerability
- What the intent of the change actually is

This tool answers all three.

---

## Demo

```
$ python main.py samples/before.tf samples/after.tf

Parsing samples/before.tf...
Parsing samples/after.tf...
Found 4 → 5 resources
Detected 4 changes
Classifying 4 changes with LLM...

IaC Semantic Diff Report

┌──────┬──────────────────────────────┬──────────┬──────────────┬──────────────────────────────────────────────────────────────┬───────────────────────────┐
│ Cha… │ Resource                     │ Risk     │ Blast Radius │ Intent                                                       │ Flags                     │
├──────┼──────────────────────────────┼──────────┼──────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────┤
│  ~   │ "aws_security_group"."web"   │ HIGH     │ 2 resources  │ Opened SSH port 22 to the internet, allowing unauthorized... │ opens_port_22, public_ip  │
│  ~   │ "aws_vpc"."main"             │ MEDIUM   │ 3 resources  │ Modified the CIDR block of the main VPC to 10.0.0.0/8        │ opens_cidr_block          │
│  +   │ "aws_db_instance"."main"     │ MEDIUM   │ 0 resources  │ Create a new PostgreSQL database instance in AWS             │ public_db_instance        │
│  ~   │ "aws_instance"."web"         │ NONE     │ 0 resources  │ Change the instance type of the web server from t2 to t3     │ —                         │
└──────┴──────────────────────────────┴──────────┴──────────────┴──────────────────────────────────────────────────────────────┴───────────────────────────┘

High-Risk Changes — Detail

  >>> "aws_security_group"."web"
      Risk: Potential unauthorized access via SSH.
      Transitively affects: aws_instance.web, aws_db_instance.main
```

---

## Architecture

```
IaC diff input (Terraform .tf files)
        │
        ▼
  HCL Parser (python-hcl2)
        │
        ▼
  Dependency Graph Builder (NetworkX DAG)
  → nodes = resources
  → edges = "depends on" relationships
        │
        ▼
  Diff Engine
  → detects added / removed / modified resources
        │
        ▼
  Blast Radius Engine (BFS traversal)
  → for each changed node, finds all downstream affected resources
        │
        ▼
  LLM Classifier (Groq / Llama 3.1)
  → intent classification
  → risk level: none / low / medium / high / critical
  → security flags: opens_port_22, public_ip, iam_privilege_escalation, ...
        │
        ▼
  Rich CLI Report
```

---

## Key concepts

**Dependency graph** — resources are parsed from HCL and their cross-references (`aws_vpc.main.id`) are resolved into directed edges in a NetworkX DAG.

**Blast radius** — for each changed resource, a BFS traversal identifies all downstream nodes. Severity is computed from the count: 1 = low, 2–5 = medium, 6–10 = high, 10+ = critical.

**LLM classification** — each change's before/after config, changed fields, and blast radius context are sent to an LLM (Llama 3.1 via Groq) with a structured prompt. The model returns JSON: intent, risk level, risk reason, and security flags.

---

## Installation

```bash
git clone https://github.com/NehaSama4833/iac-diff-engine
cd iac-diff-engine
python -m venv venv
venv\Scripts\activate        # Windows
pip install python-hcl2 networkx groq rich click
```

Set your Groq API key (free at console.groq.com):

```bash
set GROQ_API_KEY=your_key_here       # Windows
export GROQ_API_KEY=your_key_here    # Linux/Mac
```

---

## Usage

```bash
# Full analysis with LLM classification
python main.py samples/before.tf samples/after.tf

# Skip LLM (faster, graph + blast radius only)
python main.py samples/before.tf samples/after.tf --no-llm
```

---

## Project structure

```
iac-diff-engine/
├── iac_diff/
│   ├── parser.py        # HCL parser → Resource dataclass
│   ├── graph.py         # NetworkX DAG builder
│   ├── differ.py        # Diff engine (added/removed/modified)
│   ├── blast_radius.py  # BFS blast radius computation
│   ├── classifier.py    # LLM risk classifier (Groq/Llama)
│   └── report.py        # Rich CLI report renderer
├── samples/
│   ├── before.tf        # Sample Terraform state
│   └── after.tf         # Sample Terraform state with changes
└── main.py              # CLI entrypoint (Click)
```

---

## Roadmap

- [ ] Fix graph reference resolution for `resource.name.attribute` syntax
- [ ] Add Pulumi HCL support
- [ ] Export findings as SARIF format (GitHub Security tab integration)
- [ ] GitHub Action for PR-level IaC diff comments
- [ ] Support multi-file Terraform modules

---

## Tech stack

| Component | Technology |
|---|---|
| IaC parsing | python-hcl2 |
| Dependency graph | NetworkX (directed acyclic graph) |
| Blast radius | BFS traversal |
| LLM classification | Groq API (Llama 3.1 8B) |
| CLI | Click + Rich |
| Language | Python 3.12 |

---

## Why this is different from `terraform plan`

| Feature | terraform plan | iac-diff-engine |
|---|---|---|
| Line-level diff | ✓ | ✓ |
| Dependency graph | ✗ | ✓ |
| Blast radius | ✗ | ✓ |
| Security risk classification | ✗ | ✓ |
| Plain-English intent | ✗ | ✓ |
| Works without cloud credentials | ✗ | ✓ |

---

## Author

Neha Sharma — 2nd year Computer Engineering student  
Building toward GSoC 2026
