"""Europe PMC DOI, PMID, and title search."""

from __future__ import annotations

import re

from .common import record, surname

_TAGS = re.compile(r"<[^>]+>")


def _from_result(item: dict) -> dict | None:
    if not isinstance(item, dict):
        return None
    raw_title = str(item.get("title") or "").strip()
    raw_title = _TAGS.sub("", raw_title).strip()
    if raw_title.endswith("."):
        raw_title = raw_title[:-1].strip()
    if not raw_title:
        return None

    author_list = (item.get("authorList") or {}).get("author") or []
    if author_list:
        authors = [
            str(a.get("lastName") or surname(a.get("fullName") or ""))
            for a in author_list
            if isinstance(a, dict) and (a.get("lastName") or a.get("fullName"))
        ]
    elif item.get("authorString"):
        authors = [
            surname(name.strip()) for name in str(item["authorString"]).split(",") if name.strip()
        ]
    else:
        authors = []

    pub_year = item.get("pubYear")
    first_pub = str(item.get("firstPublicationDate") or "")
    year = None
    if pub_year and str(pub_year).isdigit():
        year = int(pub_year)
    elif len(first_pub) >= 4 and first_pub[:4].isdigit():
        year = int(first_pub[:4])

    year_online = int(first_pub[:4]) if len(first_pub) >= 4 and first_pub[:4].isdigit() else year

    journal = (
        item.get("journalTitle")
        or ((item.get("journalInfo") or {}).get("journal") or {}).get("title")
        or ""
    )

    return record(raw_title, year, authors, journal, "europepmc", year_online)


def doi_lookup(doi: str, _config: dict, http_get) -> dict | None:
    data = http_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": f'DOI:"{doi}"', "format": "json", "resultType": "core", "pageSize": 1},
    )
    results = ((data or {}).get("resultList") or {}).get("result") or []
    return _from_result(results[0]) if results else None


def pmid_lookup(pmid: str, _config: dict, http_get) -> dict | None:
    data = http_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": f"EXT_ID:{pmid} AND SRC:MED",
            "format": "json",
            "resultType": "core",
            "pageSize": 1,
        },
    )
    results = ((data or {}).get("resultList") or {}).get("result") or []
    return _from_result(results[0]) if results else None


def pmcid_lookup(pmcid: str, _config: dict, http_get) -> dict | None:
    data = http_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": f"PMCID:{pmcid}",
            "format": "json",
            "resultType": "core",
            "pageSize": 1,
        },
    )
    results = ((data or {}).get("resultList") or {}).get("result") or []
    return _from_result(results[0]) if results else None


def title_search(title: str, _config: dict, http_get) -> list[dict]:
    # Quote the title for exact phrase searching on Europe PMC
    clean_title = title.replace('"', "")
    data = http_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": f'TITLE:"{clean_title}"',
            "format": "json",
            "resultType": "core",
            "pageSize": 3,
        },
    )
    results = ((data or {}).get("resultList") or {}).get("result") or []
    return [rec for rec in (_from_result(item) for item in results) if rec]
