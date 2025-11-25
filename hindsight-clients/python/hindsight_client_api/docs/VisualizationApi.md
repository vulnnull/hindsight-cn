# hindsight_client_api.VisualizationApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_graph**](VisualizationApi.md#get_graph) | **GET** /api/v1/agents/{agent_id}/graph | Get memory graph data


# **get_graph**
> GraphDataResponse get_graph(agent_id, fact_type=fact_type)

Get memory graph data

Retrieve graph data for visualization, optionally filtered by fact_type (world/agent/opinion). Limited to 1000 most recent items.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.graph_data_response import GraphDataResponse
from hindsight_client_api.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = hindsight_client_api.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
async with hindsight_client_api.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = hindsight_client_api.VisualizationApi(api_client)
    agent_id = 'agent_id_example' # str | 
    fact_type = 'fact_type_example' # str |  (optional)

    try:
        # Get memory graph data
        api_response = await api_instance.get_graph(agent_id, fact_type=fact_type)
        print("The response of VisualizationApi->get_graph:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling VisualizationApi->get_graph: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **fact_type** | **str**|  | [optional] 

### Return type

[**GraphDataResponse**](GraphDataResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

