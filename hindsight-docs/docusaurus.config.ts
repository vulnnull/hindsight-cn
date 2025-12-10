import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

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
        media: 'print',
        onload: "this.media='all'",
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
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
    [
      'redocusaurus',
      {
        specs: [
          {
            id: 'hindsight-api',
            spec: 'openapi.json',
            route: '/api-reference',
            url: '/openapi.json',
          },
        ],
        theme: {
          primaryColor: '#0d9488',
          sidebar: {
            backgroundColor: '#09090b',
          },
          rightPanel: {
            backgroundColor: '#18181b',
          },
          typography: {
            fontSize: '15px',
            fontFamily: "'Avenir Book', 'Avenir', 'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            headings: {
              fontFamily: "'Avenir', 'Avenir Book', 'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            },
            code: {
              fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', Monaco, Consolas, monospace",
              fontSize: '13px',
            },
          },
        },
        config: {
          scrollYOffset: 60,
          nativeScrollbars: true,
          expandSingleSchemaField: true,
          expandResponses: '200,201',
        },
      },
    ],
  ],

  themes: ['@docusaurus/theme-mermaid'],

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
              to: '/api-reference/',
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
