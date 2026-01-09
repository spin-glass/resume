import React from "react";
import { DocsThemeConfig } from "nextra-theme-docs";

const config: DocsThemeConfig = {
  logo: <span>Resume</span>,
  project: {
    link: "https://github.com/spin-glass/resume",
  },
  docsRepositoryBase: "https://github.com/spin-glass/resume/blob/main",
  i18n: [
    { locale: 'ja', name: '日本語' },
    { locale: 'en', name: 'English' },
  ]
};

export default config;
