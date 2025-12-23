# hindsight_client_api.OperationsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancel_operation**](OperationsApi.md#cancel_operation) | **DELETE** /v1/default/banks/{bank_id}/operations/{operation_id} | Cancel a pending async operation
[**list_operations**](OperationsApi.md#list_operations) | **GET** /v1/default/banks/{bank_id}/operations | List async operations


# **cancel_operation**
> CancelOperationResponse cancel_operation(bank_id, operation_id, authorization=authorization)

Cancel a pending async operation

Cancel a pending async operation by removing it from the queue

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.cancel_operation_response import CancelOperationResponse
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
    api_instance = hindsight_client_api.OperationsApi(api_client)
    bank_id = 'bank_id_example' # str | 
    operation_id = 'operation_id_example' # str | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Cancel a pending async operation
        api_response = await api_instance.cancel_operation(bank_id, operation_id, authorization=authorization)
        print("The response of OperationsApi->cancel_operation:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OperationsApi->cancel_operation: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **operation_id** | **str**|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**CancelOperationResponse**](CancelOperationResponse.md)

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
> OperationsListResponse list_operations(bank_id, authorization=authorization)

List async operations

Get a list of all async operations (pending and failed) for a specific agent, including error messages for failed operations

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.operations_list_response import OperationsListResponse
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
    api_instance = hindsight_client_api.OperationsApi(api_client)
    bank_id = 'bank_id_example' # str | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # List async operations
        api_response = await api_instance.list_operations(bank_id, authorization=authorization)
        print("The response of OperationsApi->list_operations:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OperationsApi->list_operations: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**OperationsListResponse**](OperationsListResponse.md)

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

