# AI Automation Samples

Working sample deliverables from the 5 services I run on Coconala (Japanese freelance marketplace), published as a portfolio for prospective clients.

Author: SHOW ([show-smartwork.dev](https://show-smartwork.dev))

---

## Samples

| # | Sample | Coconala Service | Price (JPY) | Demo |
|---|---|---|---:|---|
| 01 | [CSV Sales Report Generator](samples/01-csv-report-generator/) | Claude Code Dev | ¥30,000+ | `python report.py` |
| 02 | [AI Article Generator](samples/02-ai-article-generator/) | AI Article Tool | ¥15,000 | `python generate.py --keyword "..." --mock` |
| 03 | [RSS → Social Posts](samples/03-rss-to-social/) | Content Automation | ¥22,000 | `python pipeline.py --feed ... --mock` |
| 04 | [Multi-site Price Monitor](samples/04-price-monitor/) | Python Automation | ¥15,000+ | `python monitor.py --demo` |
| 05 | [Consulting Templates](samples/05-automation-consulting-templates/) | Consultation | ¥3,300 | Markdown only |
| 06 | [Excel Monthly Report](samples/06-excel-monthly-report/) | Python Automation | ¥15,000+ | `python monthly_report.py` |
| 07 | [Landing Page Templates](samples/07-landing-page-template/) | Claude Code Dev | ¥30,000+ | Open `templates/*.html` |

---

## How to use this repo

### Browsing as a prospective client
Read each sample's README and look at the `output/` directory — generated artifacts are committed so you can see the actual deliverable without running anything.

### Running locally
Most samples work with **Python 3.10+ standard library only**. A few optional features need extras (`pip install openpyxl` for sample 06, `pip install anthropic` for real API calls in sample 02).

```bash
git clone https://github.com/SHOW-17/ai-automation-samples
cd ai-automation-samples/samples/01-csv-report-generator
python3 report.py
open output/sample_report.html
```

### Considering a custom request
Most samples have a "Customization options" section in their README listing what can be added on top of the base scope, with rough pricing.

---

## Service Map

```
                    ┌─────────────────────┐
                    │  Consultation ¥3,300 │  ← Start here
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ↓                      ↓                      ↓
┌───────────────┐  ┌──────────────────┐  ┌───────────────────┐
│Python Auto    │  │Content Auto      │  │AI Article Tool    │
│¥15,000+       │  │¥22,000           │  │¥15,000            │
└───────┬───────┘  └────────┬─────────┘  └─────────┬─────────┘
        │                   │                       │
        └──────────┬────────┴───────────────────────┘
                   ↓
       ┌──────────────────────────────┐
       │ Claude Code Dev ¥30,000+     │
       └──────────────────────────────┘
```

---

## Tech Stack

- Python 3.10+ (mostly standard library)
- HTML output uses Chart.js via CDN — single-file deliverables that work over email
- LP templates are vanilla HTML/CSS/JS — no framework, no build step
- Mock modes available everywhere AI APIs would normally be needed

---

## License

[MIT](LICENSE) — feel free to reuse the templates.

## Contact

- Coconala: https://coconala.com/users/4380829
- Portfolio: https://show-smartwork.dev
- Email: via Coconala message room
