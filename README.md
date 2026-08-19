# resumegen

> [!caution] Docs are WIP

A python tool for generating resumes from YAML data and rendering them to accessible (machine parsable) PDFs.
Currently, the data structure available is fixed, but the Jinja templates and CSS can be customized.

## Usage

### MCP

TBD

### Resume Data

Check out the [example](examples/resume-data.yaml) for a general idea of the structure. The [schema](schemas/resume-data.json) can be used to explore the data structure in more detail.

## Development

### Installation

Run the following command:

```bash
uv sync && uv pip install -e .
```

## Configuration

There are three ways to supply configuration to the tool, and not all options are available in all methods. The order of precedence is as follows: environment variables, command line, and configuration file. The configuration file is optional, but if it is used, it must be a YAML file.

### Environment Variables

The following can only be set using environment variables, and not in the configuration file or command line:

| Variable                      | Default                           | Description                                                                                                                              |
| ----------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| RESUMEGEN_DATA_DIR            | `~/.config/resumegen`             | Directory where resumegen stores its data, uses the platform-specific user config directory if not set                                   |
| RESUMEGEN_DEFAULT_CONFIG_PATH | `~/.config/resumegen/config.yaml` | Path to the default configuration file used when no other file is specified, uses the platform-specific user config directory if not set |

### Command Line

```txt
❯ resumegen --help                                                                                    󰃰 20:53:13

 Usage: resumegen [OPTIONS] DATA_FILE

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    data_file      PATH  Path to the data file. [required]                                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --log-level                   TEXT       Logging level (e.g., INFO, DEBUG). [env var: RESUMEGEN_LOG_LEVEL]        │
│ --log-file                    PATH       Path to the log file. [env var: RESUMEGEN_LOG_FILE]                      │
│ --output-dir                  DIRECTORY  Directory to save the generated resume. [env var: RESUMEGEN_OUTPUT_DIR]  │
│ --output-template             TEXT       Filename template for the generated resume.                              │
│                                          [env var: RESUMEGEN_OUTPUT_FILENAME]                                     │
│ --force               -f                 Allow overwrite of existing output file.                                 │
│ --template-dir                PATH       Directory containing the resume templates.                               │
│                                          [env var: RESUMEGEN_TEMPLATE_DIR]                                        │
│ --template            -t      TEXT       Filename of the resume template to use.                                  │
│                                          [env var: RESUMEGEN_TEMPLATE_FILENAME]                                   │
│ --author                      TEXT       Author of the resume.                                                    │
│ --title                       TEXT       Title of the resume.                                                     │
│ --html                                   Render HTML only, no PDF generation.                                     │
│ --config              -c      FILE       Path to the configuration file.                                          │
│                                          [env var: RESUMEGEN_CONFIG]                                              │
│                                          [default: /home/admin/.config/resumegen/config.yaml]                     │
│ --install-completion                     Install completion for the current shell.                                │
│ --show-completion                        Show completion for the current shell, to copy it or customize the       │
│                                          installation.                                                            │
│ --help                                   Show this message and exit.                                              │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

### Config File

Check out [examples/config.yaml](examples/config.yaml) for an example configuration file. The configuration file is optional, but if it is used, it must be a YAML file matching the JSON [schema](schemas/config.json).
