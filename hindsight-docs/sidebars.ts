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
          id: 'developer/architecture',
          label: 'Architecture',
        },
        {
          type: 'doc',
          id: 'developer/retrieval',
          label: 'Retrieval',
        },
        {
          type: 'doc',
          id: 'developer/personality',
          label: 'Personality',
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
          id: 'developer/api/ingest',
          label: 'Ingest Data',
        },
        {
          type: 'doc',
          id: 'developer/api/search',
          label: 'Search Facts',
        },
        {
          type: 'doc',
          id: 'developer/api/think',
          label: 'Think',
        },
        {
          type: 'doc',
          id: 'developer/api/think-vs-search',
          label: 'Think vs Search',
        },
        {
          type: 'doc',
          id: 'developer/api/opinions',
          label: 'Opinions',
        },
        {
          type: 'doc',
          id: 'developer/api/agent-identity',
          label: 'Agent Identity',
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
