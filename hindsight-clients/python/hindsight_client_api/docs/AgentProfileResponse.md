# AgentProfileResponse

Response model for agent profile.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**agent_id** | **str** |  | 
**name** | **str** |  | 
**personality** | [**PersonalityTraits**](PersonalityTraits.md) |  | 
**background** | **str** |  | 

## Example

```python
from hindsight_client_api.models.agent_profile_response import AgentProfileResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AgentProfileResponse from a JSON string
agent_profile_response_instance = AgentProfileResponse.from_json(json)
# print the JSON string representation of the object
print(AgentProfileResponse.to_json())

# convert the object into a dict
agent_profile_response_dict = agent_profile_response_instance.to_dict()
# create an instance of AgentProfileResponse from a dict
agent_profile_response_from_dict = AgentProfileResponse.from_dict(agent_profile_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


