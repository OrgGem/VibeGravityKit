---
description: Document Generator - AI-driven multi-format SVG content generation system for PPTX.
---

# Gen-Doc Workflow

## Core Competencies
1. **Document Conversion**: Convert PDF, DOCX, URL, or plain text to normalized Markdown.
2. **Template Selection**: Recommend layout and styling based on content.
3. **Design Blueprinting**: Strategist AI constructs full design specifications (Content + Visual rules).
4. **Image Generation**: Auto-prompting for AI image generation when required.
5. **SVG & Presentation Rendering**: Convert SVG vectors plus design parameters directly to PPTX.

## Workflow

### Phase 0: Environment Validation (Auto-Install)
*Objective: Ensure all specialized libraries are installed seamlessly.*
1. **Auto-Install Dependencies**:
    ```bash
    # Automatically install missing libraries required by this skill
    pip install -r .agent/skills/gen-doc-ppt-master/requirements.txt --quiet
    ```

### Phase 1: Source Material Assimilation
*Objective: Prepare the workspace and ingest content.*
1. **Initialize Project**:
    ```bash
    python .agent/skills/gen-doc-ppt-master/scripts/project_manager.py init "my_presentation" --format ppt169
    ```
2. **Import Sources**:
    Import and auto-convert PDFs, DOCs, or URLs to Markdown.
    ```bash
    python .agent/skills/gen-doc-ppt-master/scripts/project_manager.py import-sources projects/my_presentation_ppt169_YYYYMMDD <url/file_path> --copy
    ```

### Phase 2: Template Selection & Strategy
*Objective: Decide visual structure and generate standard Design Spec.*
1. **List Templates**: Look up available templates.
    ```bash
    cat .agent/skills/gen-doc-ppt-master/templates/layouts/layouts_index.json
    ```
2. **Strategy Formulation**: AI reviews the source markdown and produces `design_spec.md` conforming to the 8 Core Confirmations.
    *(Wait for User Confirmation!)*

### Phase 3: Visual & Content Execution
*Objective: Build standard images and map out SVG slides.*
1. **Image Analysis & Generation** (If needed):
    ```bash
    python .agent/skills/gen-doc-ppt-master/scripts/analyze_images.py projects/my_presentation_ppt169_YYYYMMDD/images
    ```
2. **SVG Execution**: Render SVG vector files inside `svg_output/` sequentially.

### Phase 4: Finalize & Export
*Objective: Assemble presentation to PPTX.*
1. **Post-Process SVG**: Handle icons, images, bounds.
    ```bash
    python .agent/skills/gen-doc-ppt-master/scripts/finalize_svg.py projects/my_presentation_ppt169_YYYYMMDD
    ```
2. **Export to PPTX**:
    ```bash
    python .agent/skills/gen-doc-ppt-master/scripts/svg_to_pptx.py projects/my_presentation_ppt169_YYYYMMDD -s final
    ```
