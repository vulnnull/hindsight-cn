# hindsight_client_api.ReasoningApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**think**](ReasoningApi.md#think) | **POST** /api/v1/agents/{agent_id}/think | Think and generate answer


# **think**
> ThinkResponse think(agent_id, think_request)

Think and generate answer

Think and formulate an answer using agent identity, world facts, and opinions.

    This endpoint:
    1. Retrieves agent facts (agent's identity)
    2. Retrieves world facts relevant to the query
    3. Retrieves existing opinions (agent's perspectives)
    4. Uses LLM to formulate a contextual answer
    5. Extracts and stores any new opinions formed
    6. Returns plain text answer, the facts used, and new opinions

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.think_request import ThinkRequest
from hindsight_client_api.models.think_response import ThinkResponse
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
    api_instance = hindsight_client_api.ReasoningApi(api_client)
    agent_id = 'agent_id_example' # str | 
    think_request = hindsight_client_api.ThinkRequest() # ThinkRequest | 

    try:
        # Think and generate answer
        api_response = await api_instance.think(agent_id, think_request)
        print("The response of ReasoningApi->think:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ReasoningApi->think: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **think_request** | [**ThinkRequest**](ThinkRequest.md)|  | 

### Return type

[**ThinkResponse**](ThinkResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

