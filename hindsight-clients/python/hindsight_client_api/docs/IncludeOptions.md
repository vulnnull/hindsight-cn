# IncludeOptions

Options for including additional data in recall results.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entities** | [**EntityIncludeOptions**](EntityIncludeOptions.md) |  | [optional] 
**chunks** | [**ChunkIncludeOptions**](ChunkIncludeOptions.md) |  | [optional] 

## Example

```python
from hindsight_client_api.models.include_options import IncludeOptions

# TODO update the JSON string below
json = "{}"
# create an instance of IncludeOptions from a JSON string
include_options_instance = IncludeOptions.from_json(json)
# print the JSON string representation of the object
print(IncludeOptions.to_json())

# convert the object into a dict
include_options_dict = include_options_instance.to_dict()
# create an instance of IncludeOptions from a dict
include_options_from_dict = IncludeOptions.from_dict(include_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


