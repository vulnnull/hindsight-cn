# ListMemoryUnitsResponse

Response model for list memory units endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | **List[Dict[str, object]]** |  | 
**total** | **int** |  | 
**limit** | **int** |  | 
**offset** | **int** |  | 

## Example

```python
from hindsight_client_api.models.list_memory_units_response import ListMemoryUnitsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ListMemoryUnitsResponse from a JSON string
list_memory_units_response_instance = ListMemoryUnitsResponse.from_json(json)
# print the JSON string representation of the object
print(ListMemoryUnitsResponse.to_json())

# convert the object into a dict
list_memory_units_response_dict = list_memory_units_response_instance.to_dict()
# create an instance of ListMemoryUnitsResponse from a dict
list_memory_units_response_from_dict = ListMemoryUnitsResponse.from_dict(list_memory_units_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


