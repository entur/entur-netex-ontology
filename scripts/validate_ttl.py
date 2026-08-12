#!/usr/bin/env python3
"""Parse-port: valider at oppgitte .ttl-filer er gyldig Turtle.

Brukes som required PR-check. En fil som ikke parser skal aldri lande på main.
Exit != 0 ved minst én feil.

Bruk: python3 scripts/validate_ttl.py <fil1.ttl> [<fil2.ttl> ...]
"""
import sys

from rdflib import Graph


def main(paths: list[str]) -> int:
    failed = False
    for path in paths:
        try:
            count = len(Graph().parse(path, format="turtle"))
            print(f"OK   {path} ({count} tripler)")
        except Exception as exc:  # rapporter alle, ikke stopp ved første
            failed = True
            print(f"FAIL {path}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
