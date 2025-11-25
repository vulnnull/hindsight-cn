# BatchPutRequest

Request model for batch put endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**items** | [**List[MemoryItem]**](MemoryItem.md) |  | 
**document_id** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.batch_put_request import BatchPutRequest

# TODO update the JSON string below
json = "{}"
# create an instance of BatchPutRequest from a JSON string
batch_put_request_instance = BatchPutRequest.from_json(json)
# print the JSON string representation of the object
print(BatchPutRequest.to_json())

# convert the object into a dict
batch_put_request_dict = batch_put_request_instance.to_dict()
# create an instance of BatchPutRequest from a dict
batch_put_request_from_dict = BatchPutRequest.from_dict(batch_put_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


