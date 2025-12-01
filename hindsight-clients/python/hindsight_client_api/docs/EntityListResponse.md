# EntityListResponse

Response model for entity list endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[EntityListItem]**](EntityListItem.md) |  | 

## Example

```python
from hindsight_client_api.models.entity_list_response import EntityListResponse

# TODO update the JSON string below
json = "{}"
# create an instance of EntityListResponse from a JSON string
entity_list_response_instance = EntityListResponse.from_json(json)
# print the JSON string representation of the object
print(EntityListResponse.to_json())

# convert the object into a dict
entity_list_response_dict = entity_list_response_instance.to_dict()
# create an instance of EntityListResponse from a dict
entity_list_response_from_dict = EntityListResponse.from_dict(entity_list_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


