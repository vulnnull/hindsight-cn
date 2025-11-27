# EntityListItem

Entity list item with summary.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**canonical_name** | **str** |  | 
**mention_count** | **int** |  | 
**first_seen** | **str** |  | [optional] 
**last_seen** | **str** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 

## Example

```python
from hindsight_client_api.models.entity_list_item import EntityListItem

# TODO update the JSON string below
json = "{}"
# create an instance of EntityListItem from a JSON string
entity_list_item_instance = EntityListItem.from_json(json)
# print the JSON string representation of the object
print(EntityListItem.to_json())

# convert the object into a dict
entity_list_item_dict = entity_list_item_instance.to_dict()
# create an instance of EntityListItem from a dict
entity_list_item_from_dict = EntityListItem.from_dict(entity_list_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


