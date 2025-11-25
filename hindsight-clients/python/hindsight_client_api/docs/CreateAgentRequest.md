# CreateAgentRequest

Request model for creating/updating an agent.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**personality** | [**PersonalityTraits**](PersonalityTraits.md) |  | [optional] 
**background** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.create_agent_request import CreateAgentRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateAgentRequest from a JSON string
create_agent_request_instance = CreateAgentRequest.from_json(json)
# print the JSON string representation of the object
print(CreateAgentRequest.to_json())

# convert the object into a dict
create_agent_request_dict = create_agent_request_instance.to_dict()
# create an instance of CreateAgentRequest from a dict
create_agent_request_from_dict = CreateAgentRequest.from_dict(create_agent_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


