# Articles

Long-form technical articles published on [Medium](https://medium.com/), with the
LaTeX source converted to Markdown and JPEG assets so the images render natively
inside Medium posts.



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
