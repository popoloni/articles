# Publishing the revised companion

Use [article.md](article.md) as the manuscript and the seven PNGs in [figures](figure-captions.md) as separate Medium uploads. Keep Figure 7's historical label. The October 29 table and audit finding provide the latest results.

## Before sharing

1. Follow [tools/README.md](tools/README.md) to regenerate the HTML and build a fresh ZIP.
2. Extract that ZIP into a new directory, run `python3 tools/verify_package.py`, then run `python3 starter/validate.py`. Keep the outputs outside the distribution before rebuilding it.
3. Open `index.html` and `preview.html` from the extracted folder; follow the reproduction and evidence links. Do not distribute an isolated HTML file.
4. Keep the five-of-six shell retry finding adjacent to the native 47/47 result. Do not describe the public starter as a reproduction of the private native matrix or of the historical 1,197-test regression.
5. Review archival sources before public distribution. The preexisting original records contain author provenance and private/local repository references. New native projections omit personal paths and private transcripts; their derivative status is explicit.

Medium does not host files merely because relative Markdown links point to them. Host the companion ZIP and extracted evidence at a stable location you control, then replace article-relative links with those public URLs or clearly identified paths inside the ZIP. The repository URL is real, but local edits and generated releases are not automatically published. No upload or repository push is performed by the build tools.

The starter's code and documentation use the [MIT license](starter/LICENSE). Article text, artwork, and historical records retain their own rights. If historical records require redaction, retain an unmodified private archive, label the derivative, and give it new hashes. Never reuse an original digest for altered evidence.
