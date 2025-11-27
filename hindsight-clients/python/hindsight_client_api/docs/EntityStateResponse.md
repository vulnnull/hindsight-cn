# EntityStateResponse

Current mental model of an entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entity_id** | **str** |  | 
**canonical_name** | **str** |  | 
**observations** | [**List[EntityObservationResponse]**](EntityObservationResponse.md) |  | 

## Example

```python
from hindsight_client_api.models.entity_state_response import EntityStateResponse

# TODO update the JSON string below
json = "{}"
# create an instance of EntityStateResponse from a JSON string
entity_state_response_instance = EntityStateResponse.from_json(json)
# print the JSON string representation of the object
print(EntityStateResponse.to_json())

# convert the object into a dict
entity_state_response_dict = entity_state_response_instance.to_dict()
# create an instance of EntityStateResponse from a dict
entity_state_response_from_dict = EntityStateResponse.from_dict(entity_state_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


