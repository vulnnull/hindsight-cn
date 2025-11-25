# hindsight_client_api.DocumentsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_document**](DocumentsApi.md#delete_document) | **DELETE** /api/v1/agents/{agent_id}/documents/{document_id} | Delete a document
[**get_document**](DocumentsApi.md#get_document) | **GET** /api/v1/agents/{agent_id}/documents/{document_id} | Get document details
[**list_documents**](DocumentsApi.md#list_documents) | **GET** /api/v1/agents/{agent_id}/documents | List documents


# **delete_document**
> object delete_document(agent_id, document_id)

Delete a document

Delete a document and all its associated memory units and links.

This will cascade delete:
- The document itself
- All memory units extracted from this document
- All links (temporal, semantic, entity) associated with those memory units

This operation cannot be undone.

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
    api_instance = hindsight_client_api.DocumentsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    document_id = 'document_id_example' # str | 

    try:
        # Delete a document
        api_response = await api_instance.delete_document(agent_id, document_id)
        print("The response of DocumentsApi->delete_document:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DocumentsApi->delete_document: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **document_id** | **str**|  | 

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

# **get_document**
> DocumentResponse get_document(agent_id, document_id)

Get document details

Get a specific document including its original text

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.document_response import DocumentResponse
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
    api_instance = hindsight_client_api.DocumentsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    document_id = 'document_id_example' # str | 

    try:
        # Get document details
        api_response = await api_instance.get_document(agent_id, document_id)
        print("The response of DocumentsApi->get_document:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DocumentsApi->get_document: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **document_id** | **str**|  | 

### Return type

[**DocumentResponse**](DocumentResponse.md)

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

# **list_documents**
> ListDocumentsResponse list_documents(agent_id, q=q, limit=limit, offset=offset)

List documents

List documents with pagination and optional search. Documents are the source content from which memory units are extracted.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.list_documents_response import ListDocumentsResponse
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
    api_instance = hindsight_client_api.DocumentsApi(api_client)
    agent_id = 'agent_id_example' # str | 
    q = 'q_example' # str |  (optional)
    limit = 100 # int |  (optional) (default to 100)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List documents
        api_response = await api_instance.list_documents(agent_id, q=q, limit=limit, offset=offset)
        print("The response of DocumentsApi->list_documents:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DocumentsApi->list_documents: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **q** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListDocumentsResponse**](ListDocumentsResponse.md)

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

