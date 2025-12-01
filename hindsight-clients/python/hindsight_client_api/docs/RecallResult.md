# RecallResult

Single recall result item.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**text** | **str** |  | 
**type** | **str** |  | [optional] 
**entities** | **List[str]** |  | [optional] 
**context** | **str** |  | [optional] 
**occurred_start** | **str** |  | [optional] 
**occurred_end** | **str** |  | [optional] 
**mentioned_at** | **str** |  | [optional] 
**document_id** | **str** |  | [optional] 
**metadata** | **Dict[str, str]** |  | [optional] 
**chunk_id** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.recall_result import RecallResult

# TODO update the JSON string below
json = "{}"
# create an instance of RecallResult from a JSON string
recall_result_instance = RecallResult.from_json(json)
# print the JSON string representation of the object
print(RecallResult.to_json())

# convert the object into a dict
recall_result_dict = recall_result_instance.to_dict()
# create an instance of RecallResult from a dict
recall_result_from_dict = RecallResult.from_dict(recall_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


