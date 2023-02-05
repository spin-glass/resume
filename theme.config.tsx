import React from "react";
import { DocsThemeConfig } from "nextra-theme-docs";

const config: DocsThemeConfig = {
  logo: <span>Resume</span>,
  project: {
    link: "https://github.com/spin-glass/resume",
  },
  docsRepositoryBase: "https://github.com/spin-glass/resume",
  footer: {
    text: "Repository of my resume",
    link: "https://github.com/spin-glass/resume",
  },
};

export default config;
