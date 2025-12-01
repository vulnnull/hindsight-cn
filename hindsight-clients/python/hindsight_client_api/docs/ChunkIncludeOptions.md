# ChunkIncludeOptions

Options for including chunks in recall results.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**max_tokens** | **int** | Maximum tokens for chunks (chunks may be truncated) | [optional] [default to 8192]

## Example

```python
from hindsight_client_api.models.chunk_include_options import ChunkIncludeOptions

# TODO update the JSON string below
json = "{}"
# create an instance of ChunkIncludeOptions from a JSON string
chunk_include_options_instance = ChunkIncludeOptions.from_json(json)
# print the JSON string representation of the object
print(ChunkIncludeOptions.to_json())

# convert the object into a dict
chunk_include_options_dict = chunk_include_options_instance.to_dict()
# create an instance of ChunkIncludeOptions from a dict
chunk_include_options_from_dict = ChunkIncludeOptions.from_dict(chunk_include_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


