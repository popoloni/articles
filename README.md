# Articles

Long-form technical articles published on [Medium](https://medium.com/), with the
LaTeX source converted to Markdown and JPEG assets so the images render natively
inside Medium posts.

## Published

| Date | Title | Link |
|------|-------|------|
| 2026-05-16 | The Evolution of Spec-Driven Development: Architectures, Methodologies, and Frameworks in AI-Assisted Engineering | [`Medium/20260516_TheEvolutionofSpec-DrivenDevelopment/`](Medium/20260516_TheEvolutionofSpec-DrivenDevelopment/medium.md) |

## Repository layout

```
.
├── Medium/                                   # One folder per published article
│   └── <YYYYMMDD>_<TitleWithoutSpaces>/
│       ├── medium.md                         # Markdown ready for Medium import
│       ├── float_map.csv                     # Caption ↔ image mapping (trace)
│       └── assets/                           # JPEG renders of figures & tables
└── scripts/                                  # Toolchain to (re)generate articles
    ├── README.md
    ├── latex_to_medium.py
    ├── run_export.sh
    └── publish_github.sh
```

## How to publish a new article

See [`scripts/README.md`](scripts/README.md) for the conversion + publishing
toolchain.
