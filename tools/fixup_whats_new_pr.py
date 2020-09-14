"""
This tool is used during CI testing to make sure sphinx raise no error.

During development, we like to have whatsnew/pr/*.rst documents to track
individual new features. Unfortunately they other either:
  - have no title (sphinx complains)
  - are not included in any toctree (sphinx complain)

This fix-them up by "inventing" a title, before building the docs. At release
time, these title and files will anyway be rewritten into the actual release
notes.
"""

from pathlib import Path

def main():
    folder = Path("docs/source/whatsnew/pr/")
    files = list(folder.glob("*.rst"))
    print(files)

    for filepath in files:
        print("Adding pseudo-title to:", filepath.name)
        title = filepath.name[:-4].split("/")[-1].replace("-", " ").capitalize()

        data = filepath.read_text()
        try:
            if data and data.splitlines()[1].startswith('='):
                continue
        except IndexError:
            pass

        with filepath.open("w") as f:
            f.write(title + "\n")
            f.write("=" * len(title) + "\n\n")
            f.write(data)

if __name__ == '__main__':
    main()

