# hindsight_client_api.AgentManagementApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_agent_background**](AgentManagementApi.md#add_agent_background) | **POST** /api/v1/agents/{agent_id}/background | Add/merge agent background
[**clear_agent_memories**](AgentManagementApi.md#clear_agent_memories) | **DELETE** /api/v1/agents/{agent_id}/memories | Clear agent memories
[**create_or_update_agent**](AgentManagementApi.md#create_or_update_agent) | **PUT** /api/v1/agents/{agent_id} | Create or update agent
[**get_agent_profile**](AgentManagementApi.md#get_agent_profile) | **GET** /api/v1/agents/{agent_id}/profile | Get agent profile
[**get_agent_stats**](AgentManagementApi.md#get_agent_stats) | **GET** /api/v1/agents/{agent_id}/stats | Get memory statistics for an agent
[**list_agents**](AgentManagementApi.md#list_agents) | **GET** /api/v1/agents | List all agents
[**update_agent_personality**](AgentManagementApi.md#update_agent_personality) | **PUT** /api/v1/agents/{agent_id}/profile | Update agent personality


# **add_agent_background**
> BackgroundResponse add_agent_background(agent_id, add_background_request)

Add/merge agent background

Add new background information or merge with existing. LLM intelligently resolves conflicts, normalizes to first person, and optionally infers personality traits.

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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)
    agent_id = 'agent_id_example' # str | 
    add_background_request = hindsight_client_api.AddBackgroundRequest() # AddBackgroundRequest | 

    try:
        # Add/merge agent background
        api_response = await api_instance.add_agent_background(agent_id, add_background_request)
        print("The response of AgentManagementApi->add_agent_background:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->add_agent_background: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **add_background_request** | [**AddBackgroundRequest**](AddBackgroundRequest.md)|  | 

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

# **clear_agent_memories**
> DeleteResponse clear_agent_memories(agent_id, fact_type=fact_type)

Clear agent memories

Delete memory units for an agent. Optionally filter by fact_type (world, agent, opinion) to delete only specific types. This is a destructive operation that cannot be undone. The agent profile (personality and background) will be preserved.

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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)
    agent_id = 'agent_id_example' # str | 
    fact_type = 'fact_type_example' # str | Optional fact type filter (world, agent, opinion) (optional)

    try:
        # Clear agent memories
        api_response = await api_instance.clear_agent_memories(agent_id, fact_type=fact_type)
        print("The response of AgentManagementApi->clear_agent_memories:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->clear_agent_memories: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **fact_type** | **str**| Optional fact type filter (world, agent, opinion) | [optional] 

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

# **create_or_update_agent**
> AgentProfileResponse create_or_update_agent(agent_id, create_agent_request)

Create or update agent

Create a new agent or update existing agent with personality and background. Auto-fills missing fields with defaults.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.agent_profile_response import AgentProfileResponse
from hindsight_client_api.models.create_agent_request import CreateAgentRequest
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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)
    agent_id = 'agent_id_example' # str | 
    create_agent_request = hindsight_client_api.CreateAgentRequest() # CreateAgentRequest | 

    try:
        # Create or update agent
        api_response = await api_instance.create_or_update_agent(agent_id, create_agent_request)
        print("The response of AgentManagementApi->create_or_update_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->create_or_update_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **create_agent_request** | [**CreateAgentRequest**](CreateAgentRequest.md)|  | 

### Return type

[**AgentProfileResponse**](AgentProfileResponse.md)

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

# **get_agent_profile**
> AgentProfileResponse get_agent_profile(agent_id)

Get agent profile

Get personality traits and background for an agent. Auto-creates agent with defaults if not exists.

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.agent_profile_response import AgentProfileResponse
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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)
    agent_id = 'agent_id_example' # str | 

    try:
        # Get agent profile
        api_response = await api_instance.get_agent_profile(agent_id)
        print("The response of AgentManagementApi->get_agent_profile:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->get_agent_profile: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 

### Return type

[**AgentProfileResponse**](AgentProfileResponse.md)

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
> object get_agent_stats(agent_id)

Get memory statistics for an agent

Get statistics about nodes and links for a specific agent

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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)
    agent_id = 'agent_id_example' # str | 

    try:
        # Get memory statistics for an agent
        api_response = await api_instance.get_agent_stats(agent_id)
        print("The response of AgentManagementApi->get_agent_stats:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->get_agent_stats: %s\n" % e)
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

# **list_agents**
> AgentListResponse list_agents()

List all agents

Get a list of all agents with their profiles

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.agent_list_response import AgentListResponse
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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)

    try:
        # List all agents
        api_response = await api_instance.list_agents()
        print("The response of AgentManagementApi->list_agents:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->list_agents: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**AgentListResponse**](AgentListResponse.md)

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

# **update_agent_personality**
> AgentProfileResponse update_agent_personality(agent_id, update_personality_request)

Update agent personality

Update agent's Big Five personality traits and bias strength

### Example


```python
import hindsight_client_api
from hindsight_client_api.models.agent_profile_response import AgentProfileResponse
from hindsight_client_api.models.update_personality_request import UpdatePersonalityRequest
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
    api_instance = hindsight_client_api.AgentManagementApi(api_client)
    agent_id = 'agent_id_example' # str | 
    update_personality_request = hindsight_client_api.UpdatePersonalityRequest() # UpdatePersonalityRequest | 

    try:
        # Update agent personality
        api_response = await api_instance.update_agent_personality(agent_id, update_personality_request)
        print("The response of AgentManagementApi->update_agent_personality:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AgentManagementApi->update_agent_personality: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agent_id** | **str**|  | 
 **update_personality_request** | [**UpdatePersonalityRequest**](UpdatePersonalityRequest.md)|  | 

### Return type

[**AgentProfileResponse**](AgentProfileResponse.md)

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

