# ReflectFact

A fact used in think response.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**text** | **str** |  | 
**type** | **str** |  | [optional] 
**context** | **str** |  | [optional] 
**occurred_start** | **str** |  | [optional] 
**occurred_end** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.reflect_fact import ReflectFact

# TODO update the JSON string below
json = "{}"
# create an instance of ReflectFact from a JSON string
reflect_fact_instance = ReflectFact.from_json(json)
# print the JSON string representation of the object
print(ReflectFact.to_json())

# convert the object into a dict
reflect_fact_dict = reflect_fact_instance.to_dict()
# create an instance of ReflectFact from a dict
reflect_fact_from_dict = ReflectFact.from_dict(reflect_fact_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


