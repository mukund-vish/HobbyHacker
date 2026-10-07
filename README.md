# HobbyHacker

> An AI-powered, containerized pentesting & bug hunting framework — bring your own tools, bring your own model.

HobbyHacker is a modular penetration testing and bug bounty framework that orchestrates a curated set of security tools inside a disposable Docker container, driven by an LLM of your choice via any OpenAI-compatible API. You choose the target, the scope, and the tools. The AI does the thinking. The deny list keeps things sane.

---

## ✨ Features

- **Bring Your Own Model** — Works with any OpenAI-compatible endpoint (OpenAI, Ollama, LM Studio, OpenRouter, vLLM, etc.).
- **Bring Your Own Tools** — No bloated pre-installed arsenal. You pick exactly which tools run in the container.
- **Engagement Presets** — Not sure what you need? Pick a preset like `bug-hunting`, `network-pentest`, `web-audit`, or `recon` and we'll load a sensible default toolset. You can still add/remove tools afterwards.
- **Core Tools Always On** — Essential utilities (`git`, `curl`/`httpie`, `file`, `jq`, `ripgrep`, etc.) are always present, whether you like it or not. They're the floor, not the ceiling.
- **Disposable Docker Sandbox** — Every session spins up a fresh Ubuntu container. When you're done, it's gone. Nothing leaks between engagements.
- **Immutable Deny List** — A hardcoded, non-bypassable list of forbidden actions. If the model proposes a denied command, it simply doesn't run. No prompt injection gets around it.
- **System-Prompted Agent Loop** — The model receives the full tool manifest, engagement context, and skill description, then reasons and acts step-by-step.

---

## 🧠 How It Works

```
┌─────────────────┐
│  You (Operator) │
└────────┬────────┘
         │  1. Target + engagement guidelines
         │  2. Tool selection (preset or manual)
         │  3. OpenAI-compatible URL + API key
         ▼
┌─────────────────────────────┐
│       HobbyHacker CLI       │
│  ┌───────────────────────┐  │
│  │  Tool Manifest Builder│  │
│  └──────────┬────────────┘  │
│             │               │
│  ┌──────────▼────────────┐  │
│  │  Docker Orchestrator  │  │
│  │  (disposable Ubuntu)  │  │
│  └──────────┬────────────┘  │
│             │               │
│  ┌──────────▼────────────┐  │
│  │  Immutable Deny List  │◄─┼── hardcoded, cannot be edited at runtime
│  └──────────┬────────────┘  │
│             │               │
│  ┌──────────▼────────────┐  │
│  │   AI Agent Loop       │  │
│  │  think → act → observe│  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

1. **Collect input** — Target, scope, rules of engagement, and any constraints.
2. **Select tools** — Manual pick or preset. Core tools are auto-injected.
3. **Configure model** — Provide an OpenAI-compatible base URL, API key, and model name.
4. **Spin up container** — A throwaway Ubuntu image is launched with your selected toolset baked in.
5. **Prompt the model** — The agent receives a system prompt containing the tool manifest, engagement details, and available skills.
6. **Reason + act** — The model proposes actions. Each action is checked against the immutable deny list before execution.
7. **Observe + iterate** — Output flows back to the model, which continues until the engagement goal is met or you stop it.

---

## 🚀 Quick Start

### Prerequisites

- Docker (running, with permissions to create containers)
- Python 3.10+ (or your runtime of choice — see `INSTALL.md`)
- An API key for any OpenAI-compatible LLM endpoint

### Install

```bash
git clone https://github.com/yourname/hobbyhacker.git
cd hobbyhacker
pip install -e .
```

### Run

```bash
hobbyhacker start
```

You'll be walked through:

```
[?] Target (domain / IP / CIDR): example.com
[?] Engagement type: bug-hunting
[?] Guidelines: Only in-scope subdomains, no DoS, respect robots.txt
[?] Preset tools? (y/N): y
[?] Add extra tools: ffuf, nuclei, subfinder
[?] OpenAI-compatible base URL: http://localhost:11434/v1
[?] API key: ****
[?] Model: llama3.1:70b

[+] Building tool manifest...
[+] Core tools locked in: git, curl, file, jq, rg, python3
[+] Spinning up disposable container...
[+] Loading deny list (immutable)...
[+] Handing off to agent. Ctrl+C to abort.
```

---

## 🧰 Tool Presets

| Preset              | Included Tools (example)                              |
| ------------------- | ----------------------------------------------------- |
| `recon`             | `subfinder`, `amass`, `httpx`, `dnsx`                 |
| `bug-hunting`       | `nuclei`, `ffuf`, `katana`, `gau`, `dalfox`           |
| `network-pentest`   | `nmap`, `masscan`, `netcat`, `tcpdump`                |
| `web-audit`         | `nikto`, `whatweb`, `wpscan`, `sqlmap`                |
| `cloud-audit`       | `prowler`, `scoutsuite`, `trivy`                      |

Presets are **starting points**, not constraints. You can add or remove anything before launch.

---

## 🛑 The Immutable Deny List

The deny list is the backbone of HobbyHacker's safety model. It is:

- **Hardcoded** into the framework — not editable via CLI, config, or prompt.
- **Checked before every action** the model proposes.
- **Non-negotiable** — if an action matches, it is silently dropped and reported back to the model as `DENIED`.

Examples of denied patterns:

- Destructive filesystem operations (`rm -rf /`, `dd` to block devices)
- Fork bombs and resource exhaustion primitives
- Exfiltration to untrusted endpoints (configurable allow-list only)
- Anything outside the declared scope (targets not listed in the engagement)
- Privilege escalation attempts on the host

> ⚠️ **Note:** The deny list is a safety net, not a license to be reckless. **You** are responsible for having explicit written authorization for every target you point HobbyHacker at. See [Legal](#-legal) below.

---

## 🧩 Skills

The agent is given a system prompt that describes the "skills" available to it, each mapping to a category of behavior:

- `recon` — passive/active enumeration
- `scan` — port, service, and vulnerability scanning
- `exploit` — controlled exploitation (subject to deny list)
- `report` — structured findings writeup
- `pivot` — lateral movement within scope

Skills can be enabled or disabled per engagement.

---

## ⚙️ Configuration

A sample `hobbyhacker.yaml`:

```yaml
model:
  base_url: http://localhost:11434/v1
  api_key: env:OPENAI_API_KEY
  model: llama3.1:70b
  temperature: 0.2

container:
  image: ubuntu:24.04
  network: bridge
  memory_limit: 2g
  cpu_limit: 2

engagement:
  type: bug-hunting
  scope:
    - "*.example.com"
  out_of_scope:
    - "admin.example.com"
  guidelines: "No DoS. Respect rate limits. Report findings in markdown."

tools:
  core: [git, curl, file, jq, rg, python3]
  preset: bug-hunting
  extra: [ffuf, nuclei]

deny_list:
  immutable: true   # cannot be changed at runtime
  # actual entries are hardcoded in hobbyhacker/safety/denylist.py
```

---

## 🗺️ Roadmap

- [ ] Web UI for tool selection
- [ ] Session recording & replay
- [ ] Multi-agent mode (recon agent → exploit agent → report agent)
- [ ] Findings export to SARIF / Markdown / PDF
- [ ] Plugin API for custom tools
- [ ] Scoped API allow-list for exfiltration

---

## 🤝 Contributing

PRs welcome. Please read `CONTRIBUTING.md` and keep the following in mind:

- The deny list is sacred. PRs that weaken it will be rejected.
- New tool presets should be documented and justified.
- Any tool that touches the network must respect scope enforcement.

---

## ⚖️ Legal

HobbyHacker is intended for **authorized security testing only**. You must have explicit, written permission from the owner of any system you target. Unauthorized use is illegal in most jurisdictions and is a violation of this project's intent.

The authors and contributors of HobbyHacker accept **no liability** for misuse, damage, or legal consequences arising from use of this software. You are the operator. You are the responsible party.

> Hack responsibly. Or don't hack at all.

---

## 📜 License

MIT — see `LICENSE`.

---

## 🙏 Acknowledgements

Built on the shoulders of the open-source security community. Thanks to every maintainer of every tool this framework orchestrates.
