# hindsight_client_api.BanksApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_bank_background**](BanksApi.md#add_bank_background) | **POST** /v1/default/banks/{bank_id}/background | Add/merge memory bank background
[**create_or_update_bank**](BanksApi.md#create_or_update_bank) | **PUT** /v1/default/banks/{bank_id} | Create or update memory bank
[**delete_bank**](BanksApi.md#delete_bank) | **DELETE** /v1/default/banks/{bank_id} | Delete memory bank
[**get_agent_stats**](BanksApi.md#get_agent_stats) | **GET** /v1/default/banks/{bank_id}/stats | Get statistics for memory bank
[**get_bank_profile**](BanksApi.md#get_bank_profile) | **GET** /v1/default/banks/{bank_id}/profile | Get memory bank profile
[**list_banks**](BanksApi.md#list_banks) | **GET** /v1/default/banks | List all memory banks
[**update_bank_disposition**](BanksApi.md#update_bank_disposition) | **PUT** /v1/default/banks/{bank_id}/profile | Update memory bank disposition


# **add_bank_background**
> BackgroundResponse add_bank_background(bank_id, add_background_request, authorization=authorization)

Add/merge memory bank background

Add new background information or merge with existing. LLM intelligently resolves conflicts, normalizes to first person, and optionally infers disposition traits.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.add_background_request import AddBackgroundRequest
from hindsight_client_api.models.background_response import BackgroundResponse
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
    api_instance = hindsight_client_api.BanksApi(api_client)
    bank_id = 'bank_id_example' # str | 
    add_background_request = hindsight_client_api.AddBackgroundRequest() # AddBackgroundRequest | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Add/merge memory bank background
        api_response = await api_instance.add_bank_background(bank_id, add_background_request, authorization=authorization)
        print("The response of BanksApi->add_bank_background:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->add_bank_background: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **add_background_request** | [**AddBackgroundRequest**](AddBackgroundRequest.md)|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**BackgroundResponse**](BackgroundResponse.md)

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

# **create_or_update_bank**
> BankProfileResponse create_or_update_bank(bank_id, create_bank_request, authorization=authorization)

Create or update memory bank

Create a new agent or update existing agent with disposition and background. Auto-fills missing fields with defaults.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.bank_profile_response import BankProfileResponse
from hindsight_client_api.models.create_bank_request import CreateBankRequest
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
    api_instance = hindsight_client_api.BanksApi(api_client)
    bank_id = 'bank_id_example' # str | 
    create_bank_request = hindsight_client_api.CreateBankRequest() # CreateBankRequest | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Create or update memory bank
        api_response = await api_instance.create_or_update_bank(bank_id, create_bank_request, authorization=authorization)
        print("The response of BanksApi->create_or_update_bank:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->create_or_update_bank: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **create_bank_request** | [**CreateBankRequest**](CreateBankRequest.md)|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**BankProfileResponse**](BankProfileResponse.md)

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

# **delete_bank**
> DeleteResponse delete_bank(bank_id, authorization=authorization)

Delete memory bank

Delete an entire memory bank including all memories, entities, documents, and the bank profile itself. This is a destructive operation that cannot be undone.

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
    api_instance = hindsight_client_api.BanksApi(api_client)
    bank_id = 'bank_id_example' # str | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Delete memory bank
        api_response = await api_instance.delete_bank(bank_id, authorization=authorization)
        print("The response of BanksApi->delete_bank:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->delete_bank: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
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

# **get_agent_stats**
> BankStatsResponse get_agent_stats(bank_id)

Get statistics for memory bank

Get statistics about nodes and links for a specific agent

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.bank_stats_response import BankStatsResponse
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
    api_instance = hindsight_client_api.BanksApi(api_client)
    bank_id = 'bank_id_example' # str | 

    try:
        # Get statistics for memory bank
        api_response = await api_instance.get_agent_stats(bank_id)
        print("The response of BanksApi->get_agent_stats:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->get_agent_stats: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 

### Return type

[**BankStatsResponse**](BankStatsResponse.md)

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

# **get_bank_profile**
> BankProfileResponse get_bank_profile(bank_id, authorization=authorization)

Get memory bank profile

Get disposition traits and background for a memory bank. Auto-creates agent with defaults if not exists.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.bank_profile_response import BankProfileResponse
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
    api_instance = hindsight_client_api.BanksApi(api_client)
    bank_id = 'bank_id_example' # str | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Get memory bank profile
        api_response = await api_instance.get_bank_profile(bank_id, authorization=authorization)
        print("The response of BanksApi->get_bank_profile:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->get_bank_profile: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**BankProfileResponse**](BankProfileResponse.md)

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

# **list_banks**
> BankListResponse list_banks(authorization=authorization)

List all memory banks

Get a list of all agents with their profiles

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.bank_list_response import BankListResponse
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
    api_instance = hindsight_client_api.BanksApi(api_client)
    authorization = 'authorization_example' # str |  (optional)

    try:
        # List all memory banks
        api_response = await api_instance.list_banks(authorization=authorization)
        print("The response of BanksApi->list_banks:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->list_banks: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **authorization** | **str**|  | [optional] 

### Return type

[**BankListResponse**](BankListResponse.md)

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

# **update_bank_disposition**
> BankProfileResponse update_bank_disposition(bank_id, update_disposition_request, authorization=authorization)

Update memory bank disposition

Update bank's disposition traits (skepticism, literalism, empathy)

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.bank_profile_response import BankProfileResponse
from hindsight_client_api.models.update_disposition_request import UpdateDispositionRequest
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
    api_instance = hindsight_client_api.BanksApi(api_client)
    bank_id = 'bank_id_example' # str | 
    update_disposition_request = hindsight_client_api.UpdateDispositionRequest() # UpdateDispositionRequest | 
    authorization = 'authorization_example' # str |  (optional)

    try:
        # Update memory bank disposition
        api_response = await api_instance.update_bank_disposition(bank_id, update_disposition_request, authorization=authorization)
        print("The response of BanksApi->update_bank_disposition:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BanksApi->update_bank_disposition: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bank_id** | **str**|  | 
 **update_disposition_request** | [**UpdateDispositionRequest**](UpdateDispositionRequest.md)|  | 
 **authorization** | **str**|  | [optional] 

### Return type

[**BankProfileResponse**](BankProfileResponse.md)

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

