import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebar: SidebarsConfig = {
  apisidebar: [
    {
      type: "doc",
      id: "api-reference/endpoints/agent-memory-api",
    },
    {
      type: "category",
      label: "Visualization",
      collapsed: false,
      collapsible: false,
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/get-graph",
          label: "Get memory graph data",
          className: "api-method get",
        },
      ],
    },
    {
      type: "category",
      label: "Memory Operations",
      collapsed: false,
      collapsible: false,
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/list-memories",
          label: "List memory units",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/search-memories",
          label: "Search memory",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/batch-put-memories",
          label: "Store multiple memories",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/batch-put-async",
          label: "Store multiple memories asynchronously",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/list-operations",
          label: "List async operations",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/cancel-operation",
          label: "Cancel a pending async operation",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/delete-memory-unit",
          label: "Delete a memory unit",
          className: "api-method delete",
        },
      ],
    },
    {
      type: "category",
      label: "Reasoning",
      collapsed: false,
      collapsible: false,
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/think",
          label: "Think and generate answer",
          className: "api-method post",
        },
      ],
    },
    {
      type: "category",
      label: "Agent Management",
      collapsed: false,
      collapsible: false,
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/list-agents",
          label: "List all agents",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/get-agent-stats",
          label: "Get memory statistics for an agent",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/clear-agent-memories",
          label: "Clear agent memories",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/get-agent-profile",
          label: "Get agent profile",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/update-agent-personality",
          label: "Update agent personality",
          className: "api-method put",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/add-agent-background",
          label: "Add/merge agent background",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/create-or-update-agent",
          label: "Create or update agent",
          className: "api-method put",
        },
      ],
    },
    {
      type: "category",
      label: "Documents",
      collapsed: false,
      collapsible: false,
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/list-documents",
          label: "List documents",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/get-document",
          label: "Get document details",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/delete-document",
          label: "Delete a document",
          className: "api-method delete",
        },
      ],
    },
  ],
};

export default sidebar.apisidebar;
