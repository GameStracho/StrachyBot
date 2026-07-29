import re

from shared import console


def __strip_header(text: str) -> str:
    """"Strips markdown characters (#) from a header"""
    return re.sub(r'^[#]* ', '', text)

def parse_changelog() -> list[tuple[str, str]]:
    """Parses sections of the newest version in CHANGELOG.md into list of pairs - section names and contents."""
    sections: list[tuple[str, str]] = []
    console.log_debug("utils: Parsing 'CHANGELOG.md' file...")

    with open("CHANGELOG.md", "r") as file:
        line: str = file.readline()
        
        # parse version
        sections.append(("Version", __strip_header(line).strip()))

        section_name: str = ""
        section_content: str = ""

        line = file.readline()
        console.log_debug(f"utils: Parsing version '{sections[0][1]}'...")

        while line and line != "---\n":
            # parse empty line
            if not line.strip():
                # end section
                if section_name:
                    section_content = section_content.rstrip()
                    sections.append((section_name, section_content))
                    indented_content: str = re.sub(r"\n", "\n\t", section_content)
                    console.log_debug(
                        f"utils: {section_name} section parsed with content: \n"
                        f"\t{indented_content}"
                    )
                    section_name = ""
                    section_content = ""

                line = file.readline()
                continue
            
            # start section
            if not section_name:
                section_name = __strip_header(line).strip()
                line = file.readline()
                continue

            # parse section content
            section_content += line
            line = file.readline()
    
    console.log_success("utils: All sections parsed.")

    return sections
