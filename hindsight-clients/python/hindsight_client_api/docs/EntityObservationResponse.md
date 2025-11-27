# EntityObservationResponse

An observation about an entity.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**text** | **str** |  | 
**mentioned_at** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.entity_observation_response import EntityObservationResponse

# TODO update the JSON string below
json = "{}"
# create an instance of EntityObservationResponse from a JSON string
entity_observation_response_instance = EntityObservationResponse.from_json(json)
# print the JSON string representation of the object
print(EntityObservationResponse.to_json())

# convert the object into a dict
entity_observation_response_dict = entity_observation_response_instance.to_dict()
# create an instance of EntityObservationResponse from a dict
entity_observation_response_from_dict = EntityObservationResponse.from_dict(entity_observation_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


