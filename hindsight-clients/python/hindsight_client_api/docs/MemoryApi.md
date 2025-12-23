# hindsight_client_api.MemoryApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**clear_bank_memories**](MemoryApi.md#clear_bank_memories) | **DELETE** /v1/default/banks/{bank_id}/memories | Clear memory bank memories
[**get_graph**](MemoryApi.md#get_graph) | **GET** /v1/default/banks/{bank_id}/graph | Get memory graph data
[**list_memories**](MemoryApi.md#list_memories) | **GET** /v1/default/banks/{bank_id}/memories/list | List memory units
[**recall_memories**](MemoryApi.md#recall_memories) | **POST** /v1/default/banks/{bank_id}/memories/recall | Recall memory
[**reflect**](MemoryApi.md#reflect) | **POST** /v1/default/banks/{bank_id}/reflect | Reflect and generate answer
[**retain_memories**](MemoryApi.md#retain_memories) | **POST** /v1/default/banks/{bank_id}/memories | Retain memories


# **clear_bank_memories**
> DeleteResponse clear_bank_memories(bank_id, type=type, authorization=authorization)

Clear memory bank memories

Delete memory units for a memory bank. Optionally filter by type (world, experience, opinion) to delete only specific types. This is a destructive operation that cannot be undone. The bank profile (disposition and background) will be preserved.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.delete_response import DeleteResponse
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
    api_instance = hindsight_client_api.MemoryApi(api_client)
    bank_id = 'bank_id_example' # str | 
    type = 'type_example' # str | Optional fact type filter (world, experience, opinion) (optional)
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Clear memory bank memories
        api_response = await api_instance.clear_bank_memories(bank_id, type=type, authorization=authorization)
        print("The response of MemoryApi->clear_bank_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryApi->clear_bank_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **type** | **str**| Optional fact type filter (world, experience, opinion) | [optional] 
 **authorization** | **str**|  | [optional] 

### Return type

[**DeleteResponse**](DeleteResponse.md)

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

# **get_graph**
> GraphDataResponse get_graph(bank_id, type=type, authorization=authorization)

Get memory graph data

Retrieve graph data for visualization, optionally filtered by type (world/experience/opinion). Limited to 1000 most recent items.

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
    api_instance = hindsight_client_api.MemoryApi(api_client)
    bank_id = 'bank_id_example' # str | 
    type = 'type_example' # str |  (optional)
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Get memory graph data
        api_response = await api_instance.get_graph(bank_id, type=type, authorization=authorization)
        print("The response of MemoryApi->get_graph:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryApi->get_graph: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **type** | **str**|  | [optional] 
 **authorization** | **str**|  | [optional] 

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

# **list_memories**
> ListMemoryUnitsResponse list_memories(bank_id, type=type, q=q, limit=limit, offset=offset, authorization=authorization)

List memory units

List memory units with pagination and optional full-text search. Supports filtering by type. Results are sorted by most recent first (mentioned_at DESC, then created_at DESC).

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.list_memory_units_response import ListMemoryUnitsResponse
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
    api_instance = hindsight_client_api.MemoryApi(api_client)
    bank_id = 'bank_id_example' # str | 
    type = 'type_example' # str |  (optional)
    q = 'q_example' # str |  (optional)
    limit = 100 # int |  (optional) (default to 100)
    offset = 0 # int |  (optional) (default to 0)
    authorization = 'authorization_example' # str |  (optional)

    try:
        # List memory units
        api_response = await api_instance.list_memories(bank_id, type=type, q=q, limit=limit, offset=offset, authorization=authorization)
        print("The response of MemoryApi->list_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryApi->list_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **type** | **str**|  | [optional] 
 **q** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]
 **offset** | **int**|  | [optional] [default to 0]
 **authorization** | **str**|  | [optional] 

### Return type

[**ListMemoryUnitsResponse**](ListMemoryUnitsResponse.md)

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

# **recall_memories**
> RecallResponse recall_memories(bank_id, recall_request, authorization=authorization)

Recall memory

Recall memory using semantic similarity and spreading activation.

The type parameter is optional and must be one of:
- `world`: General knowledge about people, places, events, and things that happen
- `experience`: Memories about experience, conversations, actions taken, and tasks performed
- `opinion`: The bank's formed beliefs, perspectives, and viewpoints

Set `include_entities=true` to get entity observations alongside recall results.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.recall_request import RecallRequest
from hindsight_client_api.models.recall_response import RecallResponse
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
    api_instance = hindsight_client_api.MemoryApi(api_client)
    bank_id = 'bank_id_example' # str | 
    recall_request = hindsight_client_api.RecallRequest() # RecallRequest | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Recall memory
        api_response = await api_instance.recall_memories(bank_id, recall_request, authorization=authorization)
        print("The response of MemoryApi->recall_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryApi->recall_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **recall_request** | [**RecallRequest**](RecallRequest.md)|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**RecallResponse**](RecallResponse.md)

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

# **reflect**
> ReflectResponse reflect(bank_id, reflect_request, authorization=authorization)

Reflect and generate answer

Reflect and formulate an answer using bank identity, world facts, and opinions.

This endpoint:
1. Retrieves experience (conversations and events)
2. Retrieves world facts relevant to the query
3. Retrieves existing opinions (bank's perspectives)
4. Uses LLM to formulate a contextual answer
5. Extracts and stores any new opinions formed
6. Returns plain text answer, the facts used, and new opinions

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.reflect_request import ReflectRequest
from hindsight_client_api.models.reflect_response import ReflectResponse
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
    api_instance = hindsight_client_api.MemoryApi(api_client)
    bank_id = 'bank_id_example' # str | 
    reflect_request = hindsight_client_api.ReflectRequest() # ReflectRequest | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Reflect and generate answer
        api_response = await api_instance.reflect(bank_id, reflect_request, authorization=authorization)
        print("The response of MemoryApi->reflect:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryApi->reflect: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **reflect_request** | [**ReflectRequest**](ReflectRequest.md)|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**ReflectResponse**](ReflectResponse.md)

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

# **retain_memories**
> RetainResponse retain_memories(bank_id, retain_request, authorization=authorization)

Retain memories

Retain memory items with automatic fact extraction.

This is the main endpoint for storing memories. It supports both synchronous and asynchronous processing via the `async` parameter.

**Features:**
- Efficient batch processing
- Automatic fact extraction from natural language
- Entity recognition and linking
- Document tracking with automatic upsert (when document_id is provided)
- Temporal and semantic linking
- Optional asynchronous processing

**The system automatically:**
1. Extracts semantic facts from the content
2. Generates embeddings
3. Deduplicates similar facts
4. Creates temporal, semantic, and entity links
5. Tracks document metadata

**When `async=true`:** Returns immediately after queuing. Use the operations endpoint to monitor progress.

**When `async=false` (default):** Waits for processing to complete.

**Note:** If a memory item has a `document_id` that already exists, the old document and its memory units will be deleted before creating new ones (upsert behavior).

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.retain_request import RetainRequest
from hindsight_client_api.models.retain_response import RetainResponse
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
    api_instance = hindsight_client_api.MemoryApi(api_client)
    bank_id = 'bank_id_example' # str | 
    retain_request = hindsight_client_api.RetainRequest() # RetainRequest | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Retain memories
        api_response = await api_instance.retain_memories(bank_id, retain_request, authorization=authorization)
        print("The response of MemoryApi->retain_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryApi->retain_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **retain_request** | [**RetainRequest**](RetainRequest.md)|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**RetainResponse**](RetainResponse.md)

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

