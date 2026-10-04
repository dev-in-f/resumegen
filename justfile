default:
    @just --list

alias bi := build-image

version := `git describe --tags --abbrev=0 2>/dev/null || echo "1.0.0"`

# Builds the Docker image for the resume generator MCP server.
build-image:
    docker build -t resumegen-mcp:{{ version }} .

# Updates the README.md file with the current version from git tags.
update-readme:
    #!/usr/bin/env python3
    from string import Template
    with open("docs/readme-template.md") as f:
        template_content = Template(f.read())
    with open("README.md", "w") as f:
        f.write(template_content.substitute(version="{{ version }}"))
    print("README.md updated with version {{ version }}")
