import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebar: SidebarsConfig = {
  apisidebar: [
    {
      type: "doc",
      id: "api-reference/endpoints/hindsight-http-api",
    },
    {
      type: "category",
      label: "Monitoring",
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/health-endpoint-health-get",
          label: "Health check endpoint",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/metrics-endpoint-metrics-get",
          label: "Prometheus metrics endpoint",
          className: "api-method get",
        },
      ],
    },
    {
      type: "category",
      label: "UNTAGGED",
      items: [
        {
          type: "doc",
          id: "api-reference/endpoints/get-graph",
          label: "Get memory graph data",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/list-memories",
          label: "List memory units",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/recall-memories",
          label: "Recall memory",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/reflect",
          label: "Reflect and generate answer",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/list-banks",
          label: "List all memory banks",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/get-agent-stats",
          label: "Get statistics for memory bank",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/list-entities",
          label: "List entities",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/get-entity",
          label: "Get entity details",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/regenerate-entity-observations",
          label: "Regenerate entity observations",
          className: "api-method post",
        },
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
        {
          type: "doc",
          id: "api-reference/endpoints/get-chunk",
          label: "Get chunk details",
          className: "api-method get",
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
          id: "api-reference/endpoints/get-bank-profile",
          label: "Get memory bank profile",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/update-bank-disposition",
          label: "Update memory bank disposition",
          className: "api-method put",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/add-bank-background",
          label: "Add/merge memory bank background",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/create-or-update-bank",
          label: "Create or update memory bank",
          className: "api-method put",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/retain-memories",
          label: "Retain memories",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "api-reference/endpoints/clear-bank-memories",
          label: "Clear memory bank memories",
          className: "api-method delete",
        },
      ],
    },
  ],
};

export default sidebar.apisidebar;
