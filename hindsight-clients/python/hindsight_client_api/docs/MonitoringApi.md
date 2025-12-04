# hindsight_client_api.MonitoringApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**health_endpoint_health_get**](MonitoringApi.md#health_endpoint_health_get) | **GET** /health | Health check endpoint
[**metrics_endpoint_metrics_get**](MonitoringApi.md#metrics_endpoint_metrics_get) | **GET** /metrics | Prometheus metrics endpoint


# **health_endpoint_health_get**
> object health_endpoint_health_get()

Health check endpoint

Checks the health of the API and database connection

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
    api_instance = hindsight_client_api.MonitoringApi(api_client)

    try:
        # Health check endpoint
        api_response = await api_instance.health_endpoint_health_get()
        print("The response of MonitoringApi->health_endpoint_health_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MonitoringApi->health_endpoint_health_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **metrics_endpoint_metrics_get**
> object metrics_endpoint_metrics_get()

Prometheus metrics endpoint

Exports metrics in Prometheus format for scraping

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
    api_instance = hindsight_client_api.MonitoringApi(api_client)

    try:
        # Prometheus metrics endpoint
        api_response = await api_instance.metrics_endpoint_metrics_get()
        print("The response of MonitoringApi->metrics_endpoint_metrics_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MonitoringApi->metrics_endpoint_metrics_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

