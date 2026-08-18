"""Diagnostic-only reimplementation of the deterministic S0 verifier's
plain reading: case-insensitive whole-word occurrences of "however",
where words are maximal runs of alphabetic characters. Kept independent
of dci1v3 so this environment never imports the scientific package;
tests assert equality against the registered counts recorded in the
committed review material."""


def s0_count(text: str) -> int:
    count = 0
    run: list[str] = []
    for ch in text:
        if ch.isalpha():
            run.append(ch)
        else:
            if run and "".join(run).lower() == "however":
                count += 1
            run = []
    if run and "".join(run).lower() == "however":
        count += 1
    return count


def verifier_label(text: str, n: int) -> str:
    return "pass" if s0_count(text) == n else "fail"
