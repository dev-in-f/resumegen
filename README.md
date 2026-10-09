# resumegen

A Python tool for rendering resumes from structured data with optional AI integration for tailoring data and scoring against job descriptions. The main goal of the utility is to provide separation between the content and the style and layout of a resume, preventing the headache of having to reformat a document every time the information is modified. This separation also makes the process of tailoring your set of skills using an LLM easier, since it only needs to operate on text, not worry about managing a PDF.

## Installation

**Dependencies**

- [WeasyPrint](https://weasyprint.org/) (for PDF generation): Please follow the instructions for your platform from the [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

```bash
uv tool install resumegen-cli
```

## Usage

### Available Commands

Usage: `resumegen COMMAND [OPTIONS] [ARGUMENTS]`

- `render`: Renders a resume using a resume data YAML file into a PDF using a Jinja2 template
- `tailor`: Tailors a resume data file based on a given job description and master resume file using an LLM
- `score`: Scores the information from the master resume file against the given job description
- `scan-pdf`: Scans a PDF for accessibility issues
- `render-html`: Renders an existing HTML file to a PDF

Use `resumegen COMMAND --help` to learn more about the available options and arguments for each command

### Structured Data Files

There are examples for a [Master Resume file](examples/master-resume.html), a [Resume Data file](examples/resume-data.yaml), and [configuration file](examples/config.yaml) in the examples directory. The schemas for these files can be found under `src/resumegen/schemas`.

## Configuration

Certain options are available for configuration through environment variables or the configuration file. They may not be available in both. Precedence is given to CLI arguments, then environment variables, then the configuration file.

### Environment Variables

The following can only be set using environment variables, and not in the configuration file or command line:

| Variable                      | Default                           | Description                                                                                                                              |
| ----------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| RESUMEGEN_DATA_DIR            | `~/.local/share/resumegen`        | Directory where resumegen stores its data, uses the platform-specific user config directory if not set                                   |
| RESUMEGEN_DEFAULT_CONFIG_PATH | `~/.config/resumegen/config.yaml` | Path to the default configuration file used when no other file is specified, uses the platform-specific user config directory if not set |
| RESUMEGEN_ENV_PATH            | `.env`                            | The path to an environment variable file to load                                                                                         |
