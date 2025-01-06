import json
from apps.integrations.db.schemas import IntegrationsSchema
from apps.integrations.loris.domain.domain import InternalModel


class ProlificIntegration(InternalModel):
    api_key: str

    @classmethod
    def from_schema(cls, schema: IntegrationsSchema):
        configuration = json.loads(schema.configuration.replace("'", '"'))
        return cls(api_key=configuration["api_key"])
    
    def __repr__(self):
        return "ProlificIntegration()"
    
class PublicProlificIntegration(InternalModel):
    exists: bool
