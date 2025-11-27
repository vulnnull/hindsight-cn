# EntityIncludeOptions

Options for including entity observations in recall results.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**max_tokens** | **int** | Maximum tokens for entity observations | [optional] [default to 500]

## Example

```python
from hindsight_client_api.models.entity_include_options import EntityIncludeOptions

# TODO update the JSON string below
json = "{}"
# create an instance of EntityIncludeOptions from a JSON string
entity_include_options_instance = EntityIncludeOptions.from_json(json)
# print the JSON string representation of the object
print(EntityIncludeOptions.to_json())

# convert the object into a dict
entity_include_options_dict = entity_include_options_instance.to_dict()
# create an instance of EntityIncludeOptions from a dict
entity_include_options_from_dict = EntityIncludeOptions.from_dict(entity_include_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


