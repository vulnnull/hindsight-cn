# BatchPutAsyncResponse

Response model for async batch put endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**message** | **str** |  | 
**agent_id** | **str** |  | 
**document_id** | **str** |  | [optional] 
**items_count** | **int** |  | 
**queued** | **bool** |  | 

## Example

```python
from hindsight_client_api.models.batch_put_async_response import BatchPutAsyncResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BatchPutAsyncResponse from a JSON string
batch_put_async_response_instance = BatchPutAsyncResponse.from_json(json)
# print the JSON string representation of the object
print(BatchPutAsyncResponse.to_json())

# convert the object into a dict
batch_put_async_response_dict = batch_put_async_response_instance.to_dict()
# create an instance of BatchPutAsyncResponse from a dict
batch_put_async_response_from_dict = BatchPutAsyncResponse.from_dict(batch_put_async_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


