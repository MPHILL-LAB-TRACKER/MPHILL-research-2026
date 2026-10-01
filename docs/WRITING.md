# Private writing & Overleaf

## Create a draft

Open **Writing & Overleaf**, add a project and assign its researcher. Linking an active project is optional. Choose a report (IMRaD), review-article or protocol-outline template, import a `.tex`/`.bib` file, or write your own source. Files are limited to 50 KB in each source field. No research results, approvals, dosages or procedural parameters are invented by a template.

Save changes before exporting. **Download saved LaTeX ZIP** returns `main.tex`, `references.bib` and a README. The ZIP is real and uses no optional PHP zip extension. You may compile it in your own editor. Attachments, raw data, private notebooks and uploaded manuscript PDFs are not automatically sent with the source. Add required figures separately in your chosen editor.

## One-way hand-off

Select **Open saved copy in Overleaf**, read the transfer notice, confirm, then select **Open in Overleaf** in the resulting dialog. The browser POSTs a ZIP data URI to the documented Overleaf `/docs` endpoint with `main_document=main.tex` and `engine=pdflatex`. Overleaf may require you to sign in. The laboratory application never receives your Overleaf password.

This creates a **new copy**, not bidirectional synchronization or an embedded Overleaf account. Save a genuine HTTPS Overleaf project URL in the private project field to reopen the same project later. Institutional transfer/privacy rules still apply. Sources and edit links are never exported to the public laboratory site.

There is intentionally **no server-side TeX execution endpoint**. Compiling arbitrary uploaded TeX on the admin server would require a separately sandboxed service and resource policy. The requested simpler Overleaf-link alternative is provided instead.

Official integration reference: https://www.overleaf.com/devs
