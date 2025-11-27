# EntityDetailResponse

Response model for entity detail endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**canonical_name** | **str** |  | 
**mention_count** | **int** |  | 
**first_seen** | **str** |  | [optional] 
**last_seen** | **str** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 
**observations** | [**List[EntityObservationResponse]**](EntityObservationResponse.md) |  | 

## Example

```python
from hindsight_client_api.models.entity_detail_response import EntityDetailResponse

# TODO update the JSON string below
json = "{}"
# create an instance of EntityDetailResponse from a JSON string
entity_detail_response_instance = EntityDetailResponse.from_json(json)
# print the JSON string representation of the object
print(EntityDetailResponse.to_json())

# convert the object into a dict
entity_detail_response_dict = entity_detail_response_instance.to_dict()
# create an instance of EntityDetailResponse from a dict
entity_detail_response_from_dict = EntityDetailResponse.from_dict(entity_detail_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


