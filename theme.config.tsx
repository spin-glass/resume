import React from "react";
import { DocsThemeConfig } from "nextra-theme-docs";

const config: DocsThemeConfig = {
  logo: <span>Resume</span>,
  project: {
    link: "https://github.com/spin-glass/resume",
  },
  docsRepositoryBase: "https://github.com/spin-glass/resume/blob/main",
  i18n: [
    { locale: "en", text: "English" },
    { locale: "ja", text: "日本語" },
  ],
};

export default config;
