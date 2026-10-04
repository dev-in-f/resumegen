# resumegen

> [!caution] Docs are WIP

A python tool for generating resumes from YAML data and rendering them to accessible (machine parsable) PDFs.
Currently, the data structure available is fixed, but the Jinja templates and CSS can be customized.

## Installation

**Dependencies**

- [WeasyPrint](https://weasyprint.org/) (for PDF generation) Please follow the instructions for your platform from the [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).
- [uv](https://github.com/astral-sh/uv)

```bash
uv tool install git+https://codeberg.org/intothebeans/resumegen.git@v${version}
```

## Usage

`resumegen [OPTIONS] DATA_FILE`

**Options**

```
--log-level                   TEXT       Logging level (e.g., INFO, DEBUG). [env var: RESUMEGEN_LOG_LEVEL]
--log-file                    PATH       Path to the log file. [env var: RESUMEGEN_LOG_FILE]
--output-template     -o      TEXT       Filename template for the generated resume. A bare filename is saved under the output directory; a relative or absolute path is resolved against the current directory.
--force               -f                 Allow overwrite of existing output file.
--template-dir                PATH       Directory containing the resume templates.
--template            -t      TEXT       Filename of the resume template to use.
--author                      TEXT       Author of the resume.
--title                       TEXT       Title of the resume.
--html                                   Render HTML only, no PDF generation.
--config              -c      FILE       Path to the configuration file. Defaults to ~/.config/resumegen/config.yaml [env var: RESUMEGEN_DEFAULT_CONFIG_PATH]
--install-completion                     Install completion for the current shell.
--show-completion                        Show completion for the current shell, to copy it or customize the installation.
--help                                   Show this message and exit.
```

### MCP

The MCP server is designed to be run via docker, and supports both HTTP and STDIO methods for clients.

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

`RESUMEGEN_OUTPUT_DIR` overrides `output_dir` from the configuration file. This is the directory output files are saved to when `-o`/`--output-template` is a bare filename (or not given); a relative or absolute path passed to `-o` is resolved against the current working directory instead.

### Config File

Check out [examples/config.yaml](examples/config.yaml) for an example configuration file. The configuration file is optional, but if it is used, it must be a YAML file matching the JSON [schema](schemas/config.json).
