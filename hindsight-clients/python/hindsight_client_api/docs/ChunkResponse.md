# ChunkResponse

Response model for get chunk endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**chunk_id** | **str** |  | 
**document_id** | **str** |  | 
**bank_id** | **str** |  | 
**chunk_index** | **int** |  | 
**chunk_text** | **str** |  | 
**created_at** | **str** |  | 

## Example

```python
from hindsight_client_api.models.chunk_response import ChunkResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ChunkResponse from a JSON string
chunk_response_instance = ChunkResponse.from_json(json)
# print the JSON string representation of the object
print(ChunkResponse.to_json())

# convert the object into a dict
chunk_response_dict = chunk_response_instance.to_dict()
# create an instance of ChunkResponse from a dict
chunk_response_from_dict = ChunkResponse.from_dict(chunk_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


