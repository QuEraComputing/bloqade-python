"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files


SRC_PATH = "src"

skip_keywords = [
    "julia",  ## [KHW] skip for now since we didn't have julia codegen rdy
    "builder/base",  ## hiding from user
    "builder/terminate",  ## hiding from user
]

nav = mkdocs_gen_files.Nav()
for path in sorted(Path(SRC_PATH).rglob("*.py")):
    module_path = path.relative_to(SRC_PATH).with_suffix("")
    doc_path = path.relative_to(SRC_PATH).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    iskip = False

    for kwrd in skip_keywords:
        if kwrd in str(doc_path):
            iskip = True
            break
    if iskip:
        print("[Ignore]", str(doc_path))
        continue

    print("[>]", str(doc_path))

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1].startswith("_"):
        continue

    nav[parts] = doc_path.as_posix()
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, ".." / path)

with mkdocs_gen_files.open("reference/SUMMARY.txt", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
