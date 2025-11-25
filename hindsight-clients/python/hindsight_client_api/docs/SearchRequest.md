# SearchRequest

Request model for search endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** |  | 
**fact_type** | **List[str]** |  | [optional] 
**thinking_budget** | **int** |  | [optional] [default to 100]
**max_tokens** | **int** |  | [optional] [default to 4096]
**trace** | **bool** |  | [optional] [default to False]
**question_date** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.search_request import SearchRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SearchRequest from a JSON string
search_request_instance = SearchRequest.from_json(json)
# print the JSON string representation of the object
print(SearchRequest.to_json())

# convert the object into a dict
search_request_dict = search_request_instance.to_dict()
# create an instance of SearchRequest from a dict
search_request_from_dict = SearchRequest.from_dict(search_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


