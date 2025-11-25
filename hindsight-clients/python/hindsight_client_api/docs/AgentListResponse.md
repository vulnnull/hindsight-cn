# AgentListResponse

Response model for listing all agents.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**agents** | [**List[AgentListItem]**](AgentListItem.md) |  | 

## Example

```python
from hindsight_client_api.models.agent_list_response import AgentListResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AgentListResponse from a JSON string
agent_list_response_instance = AgentListResponse.from_json(json)
# print the JSON string representation of the object
print(AgentListResponse.to_json())

# convert the object into a dict
agent_list_response_dict = agent_list_response_instance.to_dict()
# create an instance of AgentListResponse from a dict
agent_list_response_from_dict = AgentListResponse.from_dict(agent_list_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


