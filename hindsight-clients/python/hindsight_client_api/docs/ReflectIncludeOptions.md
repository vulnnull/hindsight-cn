# ReflectIncludeOptions

Options for including additional data in reflect results.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**facts** | **object** | Options for including facts (based_on) in reflect results. | [optional] 

## Example

```python
from hindsight_client_api.models.reflect_include_options import ReflectIncludeOptions

# TODO update the JSON string below
json = "{}"
# create an instance of ReflectIncludeOptions from a JSON string
reflect_include_options_instance = ReflectIncludeOptions.from_json(json)
# print the JSON string representation of the object
print(ReflectIncludeOptions.to_json())

# convert the object into a dict
reflect_include_options_dict = reflect_include_options_instance.to_dict()
# create an instance of ReflectIncludeOptions from a dict
reflect_include_options_from_dict = ReflectIncludeOptions.from_dict(reflect_include_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


