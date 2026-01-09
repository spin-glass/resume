import nextra from 'nextra';

const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
});

export default withNextra({
  i18n: {
    locales: ['en', 'ja'],
    defaultLocale: 'ja',
  },
  webpack: (config, options) => {
    config.watchOptions = {
      ...config.watchOptions,
      ignored: ['**/node_modules/**', '**/.git/**', '**/.next/**']
    };
    return config;
  },
  async redirects() {
    return [
      {
        source: '/',
        destination: '/ja',
        permanent: false,
      },
    ]
  }
});
