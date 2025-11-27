import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';
import apiSidebar from './docs/api-reference/endpoints/sidebar';

const sidebars: SidebarsConfig = {
  developerSidebar: [
    {
      type: 'category',
      label: 'Concepts',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'developer/index',
          label: 'Overview',
        },
        {
          type: 'doc',
          id: 'developer/retain',
          label: 'Retain',
        },
        {
          type: 'doc',
          id: 'developer/retrieval',
          label: 'Recall',
        },
        {
          type: 'doc',
          id: 'developer/personality',
          label: 'Reflect',
        },
      ],
    },
    {
      type: 'category',
      label: 'Getting Started',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'developer/api/installation',
          label: 'Installation',
        },
        {
          type: 'doc',
          id: 'developer/api/quickstart',
          label: 'Quick Start',
        },
      ],
    },
    {
      type: 'category',
      label: 'API',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'developer/api/retain',
          label: 'Retain',
        },
        {
          type: 'doc',
          id: 'developer/api/recall',
          label: 'Recall',
        },
        {
          type: 'doc',
          id: 'developer/api/reflect',
          label: 'Reflect',
        },
        {
          type: 'doc',
          id: 'developer/api/memory-banks',
          label: 'Memory Banks',
        },
        {
          type: 'doc',
          id: 'developer/api/entities',
          label: 'Entities',
        },
        {
          type: 'doc',
          id: 'developer/api/documents',
          label: 'Documents',
        },
        {
          type: 'doc',
          id: 'developer/api/operations',
          label: 'Operations',
        },
      ],
    },
    {
      type: 'category',
      label: 'Server',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'developer/server',
          label: 'Administration',
        },
      ],
    },
  ],
  sdksSidebar: [
    {
      type: 'category',
      label: 'Clients',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'sdks/python',
          label: 'Python',
        },
        {
          type: 'doc',
          id: 'sdks/nodejs',
          label: 'Node.js',
        },
        {
          type: 'doc',
          id: 'sdks/cli',
          label: 'CLI',
        },
      ],
    },
    {
      type: 'category',
      label: 'Integrations',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'sdks/openai',
          label: 'OpenAI',
        },
        {
          type: 'doc',
          id: 'sdks/langgraph',
          label: 'LangGraph',
        },
        {
          type: 'doc',
          id: 'sdks/mcp',
          label: 'MCP Server',
        },
      ],
    },
  ],
  apiReferenceSidebar: [
    {
      type: 'doc',
      id: 'api-reference/index',
      label: 'Overview',
    },
    {
      type: 'category',
      label: 'HTTP API',
      collapsible: false,
      items: apiSidebar,
    },
    {
      type: 'category',
      label: 'MCP API',
      collapsible: false,
      items: [
        {
          type: 'doc',
          id: 'api-reference/mcp',
          label: 'Tools Reference',
        },
      ],
    },
  ],
  cookbookSidebar: [
    {
      type: 'doc',
      id: 'cookbook/index',
      label: 'Cookbook',
    },
  ],
  changelogSidebar: [
    {
      type: 'doc',
      id: 'changelog/index',
      label: 'Changelog',
    },
  ],
};

export default sidebars;
