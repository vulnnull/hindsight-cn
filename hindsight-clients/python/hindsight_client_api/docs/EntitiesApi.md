# hindsight_client_api.EntitiesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_entity**](EntitiesApi.md#get_entity) | **GET** /v1/default/banks/{bank_id}/entities/{entity_id} | Get entity details
[**list_entities**](EntitiesApi.md#list_entities) | **GET** /v1/default/banks/{bank_id}/entities | List entities
[**regenerate_entity_observations**](EntitiesApi.md#regenerate_entity_observations) | **POST** /v1/default/banks/{bank_id}/entities/{entity_id}/regenerate | Regenerate entity observations


# **get_entity**
> EntityDetailResponse get_entity(bank_id, entity_id, authorization=authorization)

Get entity details

Get detailed information about an entity including observations (mental model).

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.entity_detail_response import EntityDetailResponse
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
    api_instance = hindsight_client_api.EntitiesApi(api_client)
    bank_id = 'bank_id_example' # str | 
    entity_id = 'entity_id_example' # str | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Get entity details
        api_response = await api_instance.get_entity(bank_id, entity_id, authorization=authorization)
        print("The response of EntitiesApi->get_entity:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EntitiesApi->get_entity: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **entity_id** | **str**|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**EntityDetailResponse**](EntityDetailResponse.md)

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

# **list_entities**
> EntityListResponse list_entities(bank_id, limit=limit, authorization=authorization)

List entities

List all entities (people, organizations, etc.) known by the bank, ordered by mention count.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.entity_list_response import EntityListResponse
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
    api_instance = hindsight_client_api.EntitiesApi(api_client)
    bank_id = 'bank_id_example' # str | 
    limit = 100 # int | Maximum number of entities to return (optional) (default to 100)
    authorization = 'authorization_example' # str |  (optional)

    try:
        # List entities
        api_response = await api_instance.list_entities(bank_id, limit=limit, authorization=authorization)
        print("The response of EntitiesApi->list_entities:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EntitiesApi->list_entities: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **limit** | **int**| Maximum number of entities to return | [optional] [default to 100]
 **authorization** | **str**|  | [optional] 

### Return type

[**EntityListResponse**](EntityListResponse.md)

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

# **regenerate_entity_observations**
> EntityDetailResponse regenerate_entity_observations(bank_id, entity_id, authorization=authorization)

Regenerate entity observations

Regenerate observations for an entity based on all facts mentioning it.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.entity_detail_response import EntityDetailResponse
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
    api_instance = hindsight_client_api.EntitiesApi(api_client)
    bank_id = 'bank_id_example' # str | 
    entity_id = 'entity_id_example' # str | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Regenerate entity observations
        api_response = await api_instance.regenerate_entity_observations(bank_id, entity_id, authorization=authorization)
        print("The response of EntitiesApi->regenerate_entity_observations:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EntitiesApi->regenerate_entity_observations: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **entity_id** | **str**|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**EntityDetailResponse**](EntityDetailResponse.md)

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

