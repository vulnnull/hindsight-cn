# GraphDataResponse

Response model for graph data endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**nodes** | **List[Dict[str, object]]** |  | 
**edges** | **List[Dict[str, object]]** |  | 
**table_rows** | **List[Dict[str, object]]** |  | 
**total_units** | **int** |  | 

## Example

```python
from hindsight_client_api.models.graph_data_response import GraphDataResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GraphDataResponse from a JSON string
graph_data_response_instance = GraphDataResponse.from_json(json)
# print the JSON string representation of the object
print(GraphDataResponse.to_json())

# convert the object into a dict
graph_data_response_dict = graph_data_response_instance.to_dict()
# create an instance of GraphDataResponse from a dict
graph_data_response_from_dict = GraphDataResponse.from_dict(graph_data_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


