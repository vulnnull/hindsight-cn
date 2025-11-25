# AgentListItem

Agent list item with profile summary.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**agent_id** | **str** |  | 
**name** | **str** |  | 
**personality** | [**PersonalityTraits**](PersonalityTraits.md) |  | 
**background** | **str** |  | 
**created_at** | **str** |  | [optional] 
**updated_at** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.agent_list_item import AgentListItem

# TODO update the JSON string below
json = "{}"
# create an instance of AgentListItem from a JSON string
agent_list_item_instance = AgentListItem.from_json(json)
# print the JSON string representation of the object
print(AgentListItem.to_json())

# convert the object into a dict
agent_list_item_dict = agent_list_item_instance.to_dict()
# create an instance of AgentListItem from a dict
agent_list_item_from_dict = AgentListItem.from_dict(agent_list_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


