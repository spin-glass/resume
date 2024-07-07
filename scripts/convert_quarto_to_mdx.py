import os

quarto_file_path = 'public/assets/resume-ja.qmd'
mdx_file_path = 'pages/index.mdx'

with open(quarto_file_path, 'r', encoding='utf-8') as quarto_file:
    quarto_content = quarto_file.readlines()

content_start = False
mdx_content = []
for i, line in enumerate(quarto_content):
    if i == 0: continue
    if content_start:
        mdx_content.append(line)
    if line.strip() == '---':
        content_start = not content_start

mdx_header = """import Downloads from "../components/downloads";
import DateAndName from "../components/DateAndName";

<DateAndName name="山口 敏弘" />

"""

with open(mdx_file_path, 'w', encoding='utf-8') as mdx_file:
    mdx_file.write(mdx_header)
    mdx_file.writelines(mdx_content)

print(f"MDX file created at{mdx_file_path}")
