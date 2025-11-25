# hindsight_client_api.MemoryOperationsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**batch_put_async**](MemoryOperationsApi.md#batch_put_async) | **POST** /api/v1/agents/{agent_id}/memories/async | Store multiple memories asynchronously
[**batch_put_memories**](MemoryOperationsApi.md#batch_put_memories) | **POST** /api/v1/agents/{agent_id}/memories | Store multiple memories
[**cancel_operation**](MemoryOperationsApi.md#cancel_operation) | **DELETE** /api/v1/agents/{agent_id}/operations/{operation_id} | Cancel a pending async operation
[**delete_memory_unit**](MemoryOperationsApi.md#delete_memory_unit) | **DELETE** /api/v1/agents/{agent_id}/memories/{unit_id} | Delete a memory unit
[**list_memories**](MemoryOperationsApi.md#list_memories) | **GET** /api/v1/agents/{agent_id}/memories/list | List memory units
[**list_operations**](MemoryOperationsApi.md#list_operations) | **GET** /api/v1/agents/{agent_id}/operations | List async operations
[**search_memories**](MemoryOperationsApi.md#search_memories) | **POST** /api/v1/agents/{agent_id}/memories/search | Search memory


# **batch_put_async**
> BatchPutAsyncResponse batch_put_async(agent_id, batch_put_request)

Store multiple memories asynchronously

Store multiple memory items in batch asynchronously using the task backend.

    This endpoint returns immediately after queuing the task, without waiting for completion.
    The actual processing happens in the background.

    Features:
    - Immediate response (non-blocking)
    - Background processing via task queue
    - Efficient batch processing
    - Automatic fact extraction from natural language
    - Entity recognition and linking
    - Document tracking with automatic upsert (when document_id is provided)
    - Temporal and semantic linking

    The system automatically:
    1. Queues the batch put task
    2. Returns immediately with success=True, queued=True
    3. Processes in background: extracts facts, generates embeddings, creates links

    Note: If document_id is provided and already exists, the old document and its memory units will be deleted before creating new ones (upsert behavior).

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.batch_put_async_response import BatchPutAsyncResponse
from hindsight_client_api.models.batch_put_request import BatchPutRequest
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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    batch_put_request = hindsight_client_api.BatchPutRequest() # BatchPutRequest | 

    try:
        # Store multiple memories asynchronously
        api_response = await api_instance.batch_put_async(agent_id, batch_put_request)
        print("The response of MemoryOperationsApi->batch_put_async:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->batch_put_async: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **batch_put_request** | [**BatchPutRequest**](BatchPutRequest.md)|  | 

### Return type

[**BatchPutAsyncResponse**](BatchPutAsyncResponse.md)

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

# **batch_put_memories**
> BatchPutResponse batch_put_memories(agent_id, batch_put_request)

Store multiple memories

Store multiple memory items in batch with automatic fact extraction.

    Features:
    - Efficient batch processing
    - Automatic fact extraction from natural language
    - Entity recognition and linking
    - Document tracking with automatic upsert (when document_id is provided)
    - Temporal and semantic linking

    The system automatically:
    1. Extracts semantic facts from the content
    2. Generates embeddings
    3. Deduplicates similar facts
    4. Creates temporal, semantic, and entity links
    5. Tracks document metadata

    Note: If document_id is provided and already exists, the old document and its memory units will be deleted before creating new ones (upsert behavior).

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.batch_put_request import BatchPutRequest
from hindsight_client_api.models.batch_put_response import BatchPutResponse
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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    batch_put_request = hindsight_client_api.BatchPutRequest() # BatchPutRequest | 

    try:
        # Store multiple memories
        api_response = await api_instance.batch_put_memories(agent_id, batch_put_request)
        print("The response of MemoryOperationsApi->batch_put_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->batch_put_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **batch_put_request** | [**BatchPutRequest**](BatchPutRequest.md)|  | 

### Return type

[**BatchPutResponse**](BatchPutResponse.md)

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

# **cancel_operation**
> object cancel_operation(agent_id, operation_id)

Cancel a pending async operation

Cancel a pending async operation by removing it from the queue

### Example


```python
import hindsight_client_api
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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    operation_id = 'operation_id_example' # str | 

    try:
        # Cancel a pending async operation
        api_response = await api_instance.cancel_operation(agent_id, operation_id)
        print("The response of MemoryOperationsApi->cancel_operation:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->cancel_operation: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **operation_id** | **str**|  | 

### Return type

**object**

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

# **delete_memory_unit**
> object delete_memory_unit(agent_id, unit_id)

Delete a memory unit

Delete a single memory unit and all its associated links (temporal, semantic, and entity links)

### Example


```python
import hindsight_client_api
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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    unit_id = 'unit_id_example' # str | 

    try:
        # Delete a memory unit
        api_response = await api_instance.delete_memory_unit(agent_id, unit_id)
        print("The response of MemoryOperationsApi->delete_memory_unit:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->delete_memory_unit: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **unit_id** | **str**|  | 

### Return type

**object**

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
> ListMemoryUnitsResponse list_memories(agent_id, fact_type=fact_type, q=q, limit=limit, offset=offset)

List memory units

List memory units with pagination and optional full-text search. Supports filtering by fact_type.

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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    fact_type = 'fact_type_example' # str |  (optional)
    q = 'q_example' # str |  (optional)
    limit = 100 # int |  (optional) (default to 100)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List memory units
        api_response = await api_instance.list_memories(agent_id, fact_type=fact_type, q=q, limit=limit, offset=offset)
        print("The response of MemoryOperationsApi->list_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->list_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **fact_type** | **str**|  | [optional] 
 **q** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]
 **offset** | **int**|  | [optional] [default to 0]

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

# **list_operations**
> object list_operations(agent_id)

List async operations

Get a list of all async operations (pending and failed) for a specific agent, including error messages for failed operations

### Example


```python
import hindsight_client_api
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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 

    try:
        # List async operations
        api_response = await api_instance.list_operations(agent_id)
        print("The response of MemoryOperationsApi->list_operations:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->list_operations: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 

### Return type

**object**

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

# **search_memories**
> SearchResponse search_memories(agent_id, search_request)

Search memory

Search memory using semantic similarity and spreading activation.

    The fact_type parameter is optional and must be one of:
    - 'world': General knowledge about people, places, events, and things that happen
    - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
    - 'opinion': The agent's formed beliefs, perspectives, and viewpoints

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.search_request import SearchRequest
from hindsight_client_api.models.search_response import SearchResponse
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
    api_instance = hindsight_client_api.MemoryOperationsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    search_request = hindsight_client_api.SearchRequest() # SearchRequest | 

    try:
        # Search memory
        api_response = await api_instance.search_memories(agent_id, search_request)
        print("The response of MemoryOperationsApi->search_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MemoryOperationsApi->search_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **search_request** | [**SearchRequest**](SearchRequest.md)|  | 

### Return type

[**SearchResponse**](SearchResponse.md)

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

