#!/usr/bin/env python3
"""Deterministic stdlib concept index over a markdown corpus.

Serves the ideation loop's knowledge augmentation: from the literature-review
corpus it extracts candidate research entities (capitalised noun-phrase
candidates plus frequent noun-ish tokens) and pairwise co-occurrence counts
across documents (co-mention adjacency, used as the citation-graph analog).

Public API:
- ``build_concept_index(md_text_paths) -> dict``
  Reads each markdown file deterministically (input order-insensitive; file
  list is sorted) and returns an index dict::

      {
        "entities": [{"name": str, "count": int, "docs": [doc_id, ...]}],
        "cooccurrences": [["name_a", "name_b", count], ...],
        "papers": [{"id": str, "title": str, "path": str}, ...],
      }

  * ``entities`` -- candidate entities after the frequency filter: total
    occurrence count >= ``MIN_COUNT`` (2) across the corpus, capped at
    ``MAX_ENTITIES`` (500) by default.  ``count`` is the total number of
    occurrences (capitalised and lowercase forms of the same concept merge
    into one canonical entity); ``docs`` is the sorted list of document ids
    the entity appears in.  Entities are sorted by (count desc, name asc).
  * ``cooccurrences`` -- symmetric per-document co-mention counts: for every
    pair (a, b) with a < b sorting both appear in a document, the count is
    incremented once.  Entries are ``[name_a, name_b, count]`` sorted by
    (count desc, name_a asc, name_b asc).
  * ``papers`` -- one entry per corpus file: ``id`` is the file stem (with a
    deterministic numeric suffix on stem collisions), ``title`` is the first
    markdown heading if one exists else the stem, ``path`` is the path as
    passed in.  Sorted by id.

- ``top_k_related(index, query_text, k) -> list[str]``
  Ranks related concepts by co-mention adjacency: entities named by the query
  (matched case-insensitively against indexed entity names using the same
  extractor) act as seeds; every other entity is scored by the summed
  co-occurrence count it shares with the seeds.  Returns the top-k entity
  names, ordered by (score desc, entity count desc, name asc).  Returns ``[]``
  when the query names no indexed concept or ``k <= 0``.

- ``query_papers(index, query_text, k) -> list[dict]``
  Companion ranking for papers: a paper's score is the number of distinct
  seed entities whose ``docs`` include the paper's id (co-mention adjacency);
  returns the top-k ``{"id", "title", "path"}`` entries.

CLI (matches the documented contract)::

    python3 scripts/concept_store.py build --corpus DIR [PATH ...] \\
        --output ideas/concept-index.json [--top-k N]
    python3 scripts/concept_store.py query INDEX.json [--top-k N] \\
        [--papers N] [--json] [--output FILE] SEED_CONCEPT...

  * ``build`` -- gathers ``*.md`` files under ``--corpus`` (sorted) merged
    with any explicit positional paths, builds the index, writes it as JSON
    to ``--output`` (default ``ideas/concept-index.json``).  ``--top-k``
    caps the number of retained entities (default ``MAX_ENTITIES``).
  * ``query`` -- first positional is the index file, the rest are seed
    concepts; prints the top-k related concepts and top-k papers.  With
    ``--json`` prints (or writes to ``--output``) a JSON object
    ``{"related": [...], "papers": [...]}``.

Deterministic and stdlib-only (os, re, json, argparse).  A missing or
unreadable explicitly-passed corpus file raises OSError; a ``--corpus`` scan
only includes files that exist.
"""
import argparse
import json
import os
import re
import sys

MIN_COUNT = 2          # frequency filter: entities must occur >= MIN_COUNT times
MAX_ENTITIES = 500     # default retention cap for the build CLI (--top-k)
MIN_TOKEN_LEN = 4      # frequent-token floor: lowercase tokens this long or longer

# Linking words allowed INSIDE a title-case chunk ("Attention Is All You Need").
_LINKING_WORDS = frozenset(
    "of the and for in on at to with from by a an as or vs".split()
)

# Single capitalised words that are usually sentence-starters, not concepts.
_COMMON_CAPITALISED = frozenset(
    "The This These Those However Moreover Furthermore Therefore Thus Hence "
    "We Our You Your It Its They Their In As But And If While When Where "
    "Although Because Since After Before During Among Between Within There "
    "Here Not A An One Two Both Each Some Any".split()
)

# Common function words never treated as noun-ish tokens.
_STOPWORDS = frozenset(
    "a an and are as at be been being but by can could did do does done down "
    "for from had has have having he her hers him his how i if in into is it "
    "its itself just may might me more most must my no nor not now of off on "
    "once only or other our ours out over own same she should so some such "
    "than that the their theirs them themselves then there these they this "
    "those through to too under until up very was we were what when where "
    "which while who whom why will with would you your yours yourself "
    "yourselves themselves among between during after before about against "
    "because since both each few many much onto upon without also however "
    "therefore thus moreover furthermore hence likewise whereas".split()
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'\-]*")
_HEADING_RE = re.compile(r"^\s*#+\s+(.*?)\s*$")


# ---------------------------------------------------------------------------
# Extraction primitives
# ---------------------------------------------------------------------------

def _words(text):
    """All word tokens in ``text``, in order."""
    return _WORD_RE.findall(text)


def extract_capitalised_phrases(text):
    """-> list[str] of title-case chunk candidates from ``text``.

    A chunk is a maximal run of words where every word starts with an
    uppercase letter, with linking words (of/the/and/for/...) allowed between
    capitalised words.  Leading/trailing linking words are trimmed, and a
    single-token chunk that is a common sentence-starter (The/This/However/
    ...) is dropped.  Example: "Attention Is All You Need" is one chunk.
    """
    words = _words(text)
    chunks = []
    current = []
    for word in words:
        if word[0].isupper():
            current.append(word)
        elif word.lower() in _LINKING_WORDS and current:
            current.append(word)
        else:
            if current:
                chunks.append(current)
                current = []
    if current:
        chunks.append(current)

    phrases = []
    for chunk in chunks:
        while chunk and chunk[0].lower() in _LINKING_WORDS:
            chunk = chunk[1:]
        while chunk and chunk[-1].lower() in _LINKING_WORDS:
            chunk = chunk[:-1]
        if not chunk:
            continue
        phrase = " ".join(chunk)
        if len(chunk) == 1 and phrase in _COMMON_CAPITALISED:
            continue
        phrases.append(phrase)
    return phrases


def _nounish_tokens(text):
    """-> list[str] of lowercase noun-ish token candidates (not stopwords,
    alphabetic, length >= MIN_TOKEN_LEN)."""
    out = []
    for word in _words(text):
        low = word.lower()
        if low in _STOPWORDS:
            continue
        if len(low) < MIN_TOKEN_LEN or not low.isalpha():
            continue
        out.append(low)
    return out


def _first_heading(text, fallback):
    """-> first markdown heading line content, or ``fallback``."""
    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            return match.group(1).strip()
    return fallback


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_concept_index(md_text_paths):
    """Build the deterministic concept index over ``md_text_paths``.

    Corpus files are read in sorted order (order-insensitive); a file that
    cannot be read raises OSError.  Returns the index dict documented in the
    module docstring; every list inside is deterministically ordered, so the
    same corpus always produces byte-identical JSON.
    """
    paths = sorted(set(os.fspath(p) for p in md_text_paths))

    # --- paper registry (deterministic doc ids) ----------------------------
    papers = []
    doc_ids = {}   # path -> doc id
    used_ids = set()
    for path in paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        doc_id = stem
        suffix = 2
        while doc_id in used_ids:
            doc_id = "%s-%d" % (stem, suffix)
            suffix += 1
        used_ids.add(doc_id)
        doc_ids[path] = doc_id
        with open(path, "rt", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        papers.append({"id": doc_id,
                       "title": _first_heading(text, stem),
                       "path": path})

    texts = []
    for path in paths:
        with open(path, "rt", encoding="utf-8", errors="replace") as fh:
            texts.append(fh.read())

    # --- canonical entity names (case-insensitive merge, phrase-first) -----
    canonical = {}   # lowercase form -> canonical display name (phrase wins)
    for text in texts:
        for phrase in extract_capitalised_phrases(text):
            canonical.setdefault(phrase.lower(), phrase)
    for text in texts:
        for token in _nounish_tokens(text):
            canonical.setdefault(token, token)

    # --- per-document occurrence counts ------------------------------------
    per_doc_counts = []   # list (aligned with texts) of {canonical_name: count}
    per_doc_present = []  # list of frozenset(canonical names present)
    for text in texts:
        counts = {}
        for phrase in extract_capitalised_phrases(text):
            name = canonical[phrase.lower()]
            counts[name] = counts.get(name, 0) + 1
        for token in _nounish_tokens(text):
            name = canonical[token]
            counts[name] = counts.get(name, 0) + 1
        per_doc_counts.append(counts)
        per_doc_present.append(frozenset(counts))

    # --- entity table with frequency filter --------------------------------
    totals = {}
    doc_occurrence = {}   # name -> sorted list of doc ids
    for ix, counts in enumerate(per_doc_counts):
        doc_id = papers[ix]["id"]
        for name, count in counts.items():
            totals[name] = totals.get(name, 0) + count
            doc_occurrence.setdefault(name, []).append(doc_id)

    filtered = [name for name in totals if totals[name] >= MIN_COUNT]
    filtered.sort(key=lambda name: (-totals[name], name))
    filtered = filtered[:MAX_ENTITIES]

    entities = [
        {"name": name, "count": totals[name], "docs": sorted(doc_occurrence[name])}
        for name in filtered
    ]

    # --- co-occurrence counts (per-document pair presence) -----------------
    pair_counts = {}
    for present in per_doc_present:
        members = [name for name in present if name in totals and totals[name] >= MIN_COUNT]
        members.sort()
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                key = (members[i], members[j])
                pair_counts[key] = pair_counts.get(key, 0) + 1

    cooccurrences = sorted(
        ([a, b, count] for (a, b), count in pair_counts.items()),
        key=lambda entry: (-entry[2], entry[0], entry[1]),
    )

    papers.sort(key=lambda p: p["id"])
    return {"entities": entities, "cooccurrences": cooccurrences, "papers": papers}


def _query_seed_names(index, query_text):
    """-> sorted list of indexed entity names the query names (case-insensitive)."""
    names = [e["name"] for e in index.get("entities", [])]
    by_lower = {}
    for name in names:
        by_lower.setdefault(name.lower(), name)
    query_names = set(extract_capitalised_phrases(query_text))
    query_names.update(_nounish_tokens(query_text))
    seeds = []
    for qn in query_names:
        match = by_lower.get(qn.lower())
        if match is not None:
            seeds.append(match)
    return sorted(set(seeds))


def top_k_related(index, query_text, k):
    """-> list[str] of the top-k related entity names (co-mention adjacency).

    Deterministic ordering: (co-occurrence score with the seeds desc, entity
    count desc, name asc).  ``[]`` when the query names no indexed concept,
    ``k <= 0``, or no adjacency exists.
    """
    try:
        k = max(0, int(k))
    except (TypeError, ValueError):
        return []
    if k == 0 or not isinstance(index, dict):
        return []
    seeds = _query_seed_names(index, query_text)
    if not seeds:
        return []

    cooc = {}
    for a, b, count in index.get("cooccurrences", []):
        cooc[(a, b)] = count
        cooc[(b, a)] = count

    name_meta = {e["name"]: e for e in index.get("entities", [])}
    seed_set = set(seeds)
    scores = {}
    for name in name_meta:
        if name in seed_set:
            continue
        total = sum(cooc.get((name, seed), 0) for seed in seeds)
        if total > 0:
            scores[name] = total
    ranked = sorted(scores, key=lambda n: (-scores[n], -name_meta[n]["count"], n))
    return ranked[:k]


def query_papers(index, query_text, k):
    """-> list[dict] of the top-k related papers (co-mention adjacency).

    A paper's score is the number of distinct seed entities whose ``docs``
    include the paper's id; ties break by paper id asc.  ``[]`` when the
    query names no indexed concept, ``k <= 0``, or no paper co-mentions a
    seed.
    """
    try:
        k = max(0, int(k))
    except (TypeError, ValueError):
        return []
    if k == 0 or not isinstance(index, dict):
        return []
    seeds = _query_seed_names(index, query_text)
    if not seeds:
        return []

    by_id = {p["id"]: p for p in index.get("papers", [])}
    doc_scores = {}
    for name in seeds:
        for entity in index.get("entities", []):
            if entity["name"] != name:
                continue
            for doc_id in entity["docs"]:
                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1
    ranked_ids = sorted(doc_scores, key=lambda d: (-doc_scores[d], d))
    return [by_id[d] for d in ranked_ids[:k] if d in by_id]


# ---------------------------------------------------------------------------
# CLI (no subparsers: the documented query form interleaves options with
# positionals, which argparse subparsers reject; each command parses its own
# argument list with parse_intermixed_args)
# ---------------------------------------------------------------------------

_USAGE = """usage:
  concept_store.py build --corpus DIR [PATH ...] [--output FILE] [--top-k N]
  concept_store.py query INDEX.json [--top-k N] [--papers N] [--json] \\
                          [--output FILE] SEED_CONCEPT...
"""


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="concept_store.py build",
        description="Build the concept index over a corpus and write JSON.")
    parser.add_argument("--corpus", metavar="DIR",
                        help="directory scanned for *.md corpus files")
    parser.add_argument("paths", nargs="*", metavar="PATH",
                        help="explicit markdown files (merged with --corpus)")
    parser.add_argument("--output", metavar="FILE",
                        default="ideas/concept-index.json",
                        help="output JSON path (default: ideas/concept-index.json)")
    parser.add_argument("--top-k", type=int, default=MAX_ENTITIES, metavar="N",
                        help="max entities retained after the frequency filter "
                             "(default %d)" % MAX_ENTITIES)
    return parser


def _query_parser():
    parser = argparse.ArgumentParser(
        prog="concept_store.py query",
        description="Query the index: top-k co-mention neighbours + top-k papers.")
    parser.add_argument("pos", nargs="*", metavar="ARG",
                        help="first: index file; the rest: seed concepts")
    parser.add_argument("--top-k", type=int, default=5, metavar="N",
                        help="number of related concepts (default 5)")
    parser.add_argument("--papers", type=int, default=5, dest="papers_k",
                        metavar="N", help="number of related papers (default 5)")
    parser.add_argument("--json", action="store_true",
                        help="emit a JSON object instead of human-readable lines")
    parser.add_argument("--output", metavar="FILE", default=None,
                        help="write the JSON object to FILE (with --json)")
    return parser


def _cmd_build(args):
    paths = []
    if args.corpus:
        if not os.path.isdir(args.corpus):
            raise SystemExit("build: corpus directory not found: %s" % args.corpus)
        for name in sorted(os.listdir(args.corpus)):
            path = os.path.join(args.corpus, name)
            if name.endswith(".md") and os.path.isfile(path):
                paths.append(path)
    paths.extend(args.paths)
    if not paths:
        raise SystemExit("build: no corpus files (need --corpus DIR and/or PATH arguments)")

    index = build_concept_index(paths)
    output = args.output
    directory = os.path.dirname(output)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(output, "wt", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, sort_keys=False)
        fh.write("\n")
    print("concept-store build: %d entities, %d cooccurrences, %d papers -> %s"
          % (len(index["entities"]), len(index["cooccurrences"]),
             len(index["papers"]), output))


def _cmd_query(args):
    pos = args.pos
    if not pos:
        raise SystemExit("query: first positional argument must be the index file")
    index_file, seeds = pos[0], pos[1:]
    if not os.path.isfile(index_file):
        raise SystemExit("query: index file not found: %s" % index_file)
    with open(index_file, "rt", encoding="utf-8") as fh:
        index = json.load(fh)
    query_text = " ".join(seeds)
    related = top_k_related(index, query_text, args.top_k)
    papers = query_papers(index, query_text, args.papers_k)

    if args.json:
        result = {"related": related, "papers": papers}
        payload = json.dumps(result, indent=2, sort_keys=False)
        if args.output:
            directory = os.path.dirname(args.output)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(args.output, "wt", encoding="utf-8") as fh:
                fh.write(payload + "\n")
            print("concept-store query: wrote JSON -> %s" % args.output)
        else:
            print(payload)
        return

    print("Related concepts (top %d):" % args.top_k)
    for name in related:
        print("  - %s" % name)
    print("Papers (top %d):" % args.papers_k)
    for paper in papers:
        print("  - %s  %s" % (paper["id"], paper.get("title", "")))


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(_USAGE)
        return 0
    command = argv[0]
    rest = argv[1:]
    if command == "build":
        return _cmd_build(_build_parser().parse_intermixed_args(rest))
    if command == "query":
        return _cmd_query(_query_parser().parse_intermixed_args(rest))
    print("concept_store.py: unknown command %r (try --help)" % command,
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())