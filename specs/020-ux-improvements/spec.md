# UX Improvements Specification

## Overview
Improve the user experience of the online resume by adding standard web navigation features. This aims to transform the single-page document into a proper web portfolio application.

## Goals
1.  **Global Navigation**: Allow users to navigate between Resume, Portfolio (future), and potential multi-language versions.
2.  **Context Awareness**: Breadcrumbs to show current location (useful for future nested pages like project details).
3.  **Mobile Support**: Responsive menu for smaller screens.
4.  **Print Optimization**: Ensure navigation elements are hidden when printing to PDF.

## Components

### GlobalNav
-   **Location**: Top of viewport.
-   **Structure**: Logo/Name (Home link), Links (Resume, Portfolio, Contact).
-   **Behavior**: Sticky or static. Mobile hamburger menu.
-   **Styling**: Matches design system colors (`--color-primary` background, white text).

### Breadcrumbs
-   **Location**: Below GlobalNav, above content.
-   **Items**: Home > Current Page.
-   **Styling**: Subtle, text-sm, muted colors.

### Footer
-   **Location**: Bottom of page.
-   **Content**: Copyright, Links to GitHub/LinkedIn (social icons).
-   **Styling**: Simple, centered, muted.

## Technical Details
-   **Framework**: Astro Components.
-   **Styling**: Tailwind CSS v4.
-   **Responsive**: Use `md:` prefixes for desktop styles.
-   **Print**: Use `@media print` or `.no-print` class to hide nav/footer.
