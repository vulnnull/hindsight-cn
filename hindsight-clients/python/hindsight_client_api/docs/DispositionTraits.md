# DispositionTraits

Disposition traits based on Big Five model.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**openness** | **float** | Openness to experience (0-1) | 
**conscientiousness** | **float** | Conscientiousness (0-1) | 
**extraversion** | **float** | Extraversion (0-1) | 
**agreeableness** | **float** | Agreeableness (0-1) | 
**neuroticism** | **float** | Neuroticism (0-1) | 
**bias_strength** | **float** | How strongly disposition influences opinions (0-1) | 

## Example

```python
from hindsight_client_api.models.disposition_traits import DispositionTraits

# TODO update the JSON string below
json = "{}"
# create an instance of DispositionTraits from a JSON string
disposition_traits_instance = DispositionTraits.from_json(json)
# print the JSON string representation of the object
print(DispositionTraits.to_json())

# convert the object into a dict
disposition_traits_dict = disposition_traits_instance.to_dict()
# create an instance of DispositionTraits from a dict
disposition_traits_from_dict = DispositionTraits.from_dict(disposition_traits_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


