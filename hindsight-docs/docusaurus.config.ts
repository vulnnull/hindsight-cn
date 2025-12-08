import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import type * as OpenApiPlugin from 'docusaurus-plugin-openapi-docs';

const config: Config = {
  title: 'Hindsight',
  tagline: 'Entity-Aware Memory System for AI Agents',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  markdown: {
    mermaid: true,
  },

  url: 'https://hindsight.vectorize.io',
  baseUrl: '/',

  organizationName: 'vectorize-io',
  projectName: 'hindsight',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  headTags: [
    {
      tagName: 'link',
      attributes: {
        rel: 'preconnect',
        href: 'https://fonts.googleapis.com',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'preconnect',
        href: 'https://fonts.gstatic.com',
        crossorigin: 'anonymous',
      },
    },
    {
      tagName: 'link',
      attributes: {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Nunito+Sans:wght@400;500;600;700;800&display=swap',
      },
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/vectorize-io/hindsight/tree/main/hindsight-docs/',
          routeBasePath: '/',
          docItemComponent: '@theme/ApiItem',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    [
      'docusaurus-plugin-openapi-docs',
      {
        id: 'api',
        docsPluginId: 'default',
        config: {
          hindsight: {
            specPath: 'openapi.json',
            outputDir: 'docs/api-reference/endpoints',
            sidebarOptions: {
              groupPathsBy: 'tag',
            },
          } satisfies OpenApiPlugin.Options,
        },
      },
    ],
  ],

  themes: ['docusaurus-theme-openapi-docs', '@docusaurus/theme-mermaid'],

  themeConfig: {
    image: 'img/hindsight-social-card.jpg',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Hindsight',
      logo: {
        alt: 'Hindsight Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'custom-iconLink',
          position: 'left',
          icon: 'code',
          label: 'Developer',
          to: '/',
        },
        {
          type: 'custom-iconLink',
          position: 'left',
          icon: 'package',
          label: 'SDKs',
          to: '/sdks/python',
        },
        {
          type: 'custom-iconLink',
          position: 'left',
          icon: 'file-code',
          label: 'API Reference',
          to: '/api-reference',
        },
        {
          type: 'custom-iconLink',
          position: 'left',
          icon: 'book-open',
          label: 'Cookbook',
          to: '/cookbook',
        },
        {
          type: 'custom-iconLink',
          position: 'left',
          icon: 'clock',
          label: 'Changelog',
          to: '/changelog',
        },
        {
          href: 'https://github.com/vectorize-io/hindsight',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Introduction',
              to: '/',
            },
            {
              label: 'SDKs',
              to: '/sdks/python',
            },
            {
              label: 'API Reference',
              to: '/api-reference',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/vectorize-io/hindsight',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Hindsight. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'python', 'rust'],
    },
    mermaid: {
      theme: {
        light: 'base',
        dark: 'dark',
      },
      options: {
        themeVariables: {
          primaryColor: '#6366f1',
          primaryTextColor: '#ffffff',
          primaryBorderColor: '#4f46e5',
          secondaryColor: '#f1f5f9',
          secondaryTextColor: '#1e293b',
          secondaryBorderColor: '#cbd5e1',
          tertiaryColor: '#e0e7ff',
          lineColor: '#94a3b8',
          textColor: '#1e293b',
          mainBkg: '#ffffff',
          nodeBorder: '#4f46e5',
          clusterBkg: '#f8fafc',
          clusterBorder: '#e2e8f0',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        },
      },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
