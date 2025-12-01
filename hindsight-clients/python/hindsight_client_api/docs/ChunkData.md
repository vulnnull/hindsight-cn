# ChunkData

Chunk data for a single chunk.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**text** | **str** |  | 
**chunk_index** | **int** |  | 
**truncated** | **bool** | Whether the chunk text was truncated due to token limits | [optional] [default to False]

## Example

```python
from hindsight_client_api.models.chunk_data import ChunkData

# TODO update the JSON string below
json = "{}"
# create an instance of ChunkData from a JSON string
chunk_data_instance = ChunkData.from_json(json)
# print the JSON string representation of the object
print(ChunkData.to_json())

# convert the object into a dict
chunk_data_dict = chunk_data_instance.to_dict()
# create an instance of ChunkData from a dict
chunk_data_from_dict = ChunkData.from_dict(chunk_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


