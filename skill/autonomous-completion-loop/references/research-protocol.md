# Research Protocol Reference

Use external research only for a concrete information gap. Record the question before searching.

## Adoption gate

A conclusion may affect execution only when it has:

1. a real absolute `http://` or `https://` URL;
2. an identified publisher and source type;
3. retrieval date and applicable version;
4. a bounded evidence summary and limitations;
5. a local validation result.

Prefer official documentation, official repositories, release notes, standards, and other primary sources. Search results or snippets alone are not final evidence.

Never execute `curl URL | bash` or `wget URL -O- | sh`. Save public code first, inspect it, pin the relevant revision where possible, then decide whether a local test is safe.

`RESEARCH_APPLIED` is written to `RESEARCH_LOG.md` and `DECISION_LOG.md`; it is not a final state and does not bypass verification.
