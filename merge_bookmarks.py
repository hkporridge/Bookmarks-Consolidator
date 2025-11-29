import re
import sys
from collections import defaultdict

# Data structure:
# folders[(path_tuple)] = {url: title}
# e.g. path_tuple = ("Bookmarks Bar", "Programming", "Python")

def parse_bookmarks_html(path):
    folders = defaultdict(dict)  # path_tuple -> {url: title}
    folder_stack = []  # list of folder names, root -> current

    # Regexes for folder names and links
    h3_re = re.compile(r"<H3[^>]*>(.*?)</H3>", re.IGNORECASE)
    a_href_re = re.compile(r'HREF="([^"]+)"', re.IGNORECASE)
    a_title_re = re.compile(r'<A[^>]*>(.*?)</A>', re.IGNORECASE)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            # Folder opening line: <DT><H3>Folder Name</H3>
            h3_match = h3_re.search(line)
            if h3_match:
                folder_name = h3_match.group(1)
                folder_stack.append(folder_name)
                continue

            # Folder closing: </DL> usually means we finished a folder level
            if line.upper().startswith("</DL>"):
                if folder_stack:
                    folder_stack.pop()
                continue

            # Link line: <DT><A HREF="...">Title</A>
            if "<A " in line.upper():
                href_match = a_href_re.search(line)
                title_match = a_title_re.search(line)
                if href_match and title_match:
                    url = href_match.group(1).strip()
                    title = title_match.group(1).strip()

                    path_tuple = tuple(folder_stack)
                    # If URL already exists under this folder, skip (dedupe)
                    if url not in folders[path_tuple]:
                        folders[path_tuple][url] = title

    return folders


def merge_folders(f1, f2):
    merged = defaultdict(dict)
    # Start with first file
    for path, links in f1.items():
        for url, title in links.items():
            merged[path][url] = title

    # Add second file, merging and deduping
    for path, links in f2.items():
        for url, title in links.items():
            if url not in merged[path]:
                merged[path][url] = title  # keep title from second if new

    return merged


def write_bookmarks_html(folders, output_path):
    # Simple Netscape-style header
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
""")

        def write_folder(path_tuple, indent_level=1):
            indent = "    " * indent_level
            if not path_tuple:
                # root (we treat as already opened by outer <DL>)
                pass
            else:
                name = path_tuple[-1]
                out.write(f'{indent}<DT><H3>{name}</H3>\n')
                out.write(f'{indent}<DL><p>\n')

            # Links directly in this folder
            links = folders.get(path_tuple, {})
            for url, title in sorted(links.items(), key=lambda x: x[1].lower()):
                out.write(f'{indent}    <DT><A HREF="{url}">{title}</A>\n')

            # Child folders: look for paths that start with this path_tuple
            child_prefix_len = len(path_tuple)
            child_folders = set()
            for p in folders.keys():
                if len(p) > child_prefix_len and p[:child_prefix_len] == path_tuple:
                    child_folders.add(p[child_prefix_len:child_prefix_len+1][0])

            # For stable order
            for child_name in sorted(child_folders, key=lambda s: s.lower()):
                child_path = path_tuple + (child_name,)
                write_folder(child_path, indent_level + (0 if not path_tuple else 1))

            if path_tuple:
                out.write(f'{indent}</DL><p>\n')

        # First, figure out top-level folders
        top_levels = set()
        for path in folders.keys():
            if len(path) > 0:
                top_levels.add(path[0])

        # Write all top-level folders
        for top in sorted(top_levels, key=lambda s: s.lower()):
            write_folder((top,), indent_level=1)

        out.write("</DL><p>\n")


def main():
    if len(sys.argv) != 4:
        print("Usage: python merge_bookmarks.py bookmarks1.html bookmarks2.html merged.html")
        sys.exit(1)

    file1, file2, out_file = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"Parsing {file1}...")
    folders1 = parse_bookmarks_html(file1)
    print(f"Found {len(folders1)} folders in first file.")

    print(f"Parsing {file2}...")
    folders2 = parse_bookmarks_html(file2)
    print(f"Found {len(folders2)} folders in second file.")

    print("Merging...")
    merged = merge_folders(folders1, folders2)

    print(f"Writing merged bookmarks to {out_file}...")
    write_bookmarks_html(merged, out_file)
    print("Done.")


if __name__ == "__main__":
    main()
# End of file