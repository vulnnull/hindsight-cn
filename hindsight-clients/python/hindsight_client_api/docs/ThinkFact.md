# ThinkFact

A fact used in think response.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**text** | **str** |  | 
**type** | **str** |  | [optional] 
**context** | **str** |  | [optional] 
**event_date** | **str** |  | [optional] 

## Example

```python
from hindsight_client_api.models.think_fact import ThinkFact

# TODO update the JSON string below
json = "{}"
# create an instance of ThinkFact from a JSON string
think_fact_instance = ThinkFact.from_json(json)
# print the JSON string representation of the object
print(ThinkFact.to_json())

# convert the object into a dict
think_fact_dict = think_fact_instance.to_dict()
# create an instance of ThinkFact from a dict
think_fact_from_dict = ThinkFact.from_dict(think_fact_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


