# Articles

Long-form technical articles published on [Medium](https://medium.com/), with the
LaTeX source converted to Markdown and JPEG assets so the images render natively
inside Medium posts.

## Run the SDD testing companion

The [SDD article and companion](Medium/261028_SDD_Testing_Complete_Companion/README.md)
include an illustrated article, dated execution evidence, and a standalone Python
example. Start with the [reproduction guide](Medium/261028_SDD_Testing_Complete_Companion/starter/docs/REPRODUCE.md)
or the [October 29 results and audit finding](Medium/261028_SDD_Testing_Complete_Companion/evidence/local-validation/README.md).

With Python 3.11 or later, run the public example without dependencies or a model:

```sh
cd Medium/261028_SDD_Testing_Complete_Companion/starter
python3 validate.py
```

The guide also covers a container run and an optional local Ollama probe. The
private framework's native-agent matrix is a separate experiment; its full source
and raw transcripts are not distributed in this repository.



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
