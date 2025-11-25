# BatchPutResponse

Response model for batch put endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**message** | **str** |  | 
**agent_id** | **str** |  | 
**document_id** | **str** |  | [optional] 
**items_count** | **int** |  | 

## Example

```python
from hindsight_client_api.models.batch_put_response import BatchPutResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BatchPutResponse from a JSON string
batch_put_response_instance = BatchPutResponse.from_json(json)
# print the JSON string representation of the object
print(BatchPutResponse.to_json())

# convert the object into a dict
batch_put_response_dict = batch_put_response_instance.to_dict()
# create an instance of BatchPutResponse from a dict
batch_put_response_from_dict = BatchPutResponse.from_dict(batch_put_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


