# RecallResponse

Response model for recall endpoints.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[RecallResult]**](RecallResult.md) |  | 
**trace** | **Dict[str, object]** |  | [optional] 
**entities** | [**Dict[str, EntityStateResponse]**](EntityStateResponse.md) |  | [optional] 
**chunks** | [**Dict[str, ChunkData]**](ChunkData.md) |  | [optional] 

## Example

```python
from hindsight_client_api.models.recall_response import RecallResponse

# TODO update the JSON string below
json = "{}"
# create an instance of RecallResponse from a JSON string
recall_response_instance = RecallResponse.from_json(json)
# print the JSON string representation of the object
print(RecallResponse.to_json())

# convert the object into a dict
recall_response_dict = recall_response_instance.to_dict()
# create an instance of RecallResponse from a dict
recall_response_from_dict = RecallResponse.from_dict(recall_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


