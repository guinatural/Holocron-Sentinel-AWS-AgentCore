"""LGPD Compliant Anonymization module for sensitive data protection."""

from typing import Dict, Any, List


def lgpd_anonymize(
    payload: Dict[str, Any], preserve_ids: bool = True
) -> Dict[str, Any]:
    """
    Remove or anonymize all LGPD-sensitive fields from payload.

    Implements Article 46 (Security) and Article 18 (Anonymization) of LGPD.

    Args:
        payload: Dictionary containing potentially sensitive data
        preserve_ids: If True, keep non-sensitive IDs (user_id, tenant_id, etc.)

    Returns:
        Anonymized dictionary with sensitive fields replaced
    """
    # Sensitive fields per LGPD: name, contact, document, financial, health, location
    sensitive_patterns = {
        # Names
        "nome",
        "nome_completo",
        "name",
        "full_name",
        "razao_social",
        # Contact
        "email",
        "e-mail",
        "telefone",
        "celular",
        "whatsapp",
        "fax",
        "ddd",
        "phone",
        "mobile",
        "contact",
        "endereco",
        "address",
        "cep",
        "cidade",
        "estado",
        "pais",
        "localizacao",
        # Documents
        "cpf",
        "cnpj",
        "rg",
        "cnh",
        "passaporte",
        "titulo",
        "cartao",
        "document",
        "document_number",
        "identidade",
        # Financial
        "renda",
        "salario",
        "salario_bruto",
        "rendimento",
        "banco",
        "agencia",
        "conta",
        "credito",
        "cartao_credito",
        "numero_cartao",
        "cvv",
        "validade",
        # Health
        "saude",
        "medico",
        "hospital",
        "convenio",
        "plano_saude",
        "prontuario",
        "diagnostico",
        "prescricao",
        # Location
        "ip",
        "mac",
        "geolocalizacao",
        "latitude",
        "longitude",
        # Timestamps that could be sensitive
        "nascimento",
        "data_nascimento",
        "dt_nasc",
        "birthdate",
        "data_nasc",
        "idade",
        # Other sensitive
        "senha",
        "password",
        "secret",
        "chave",
        "token",
        "api_key",
        "api_key",
        "private_key",
        "secret_key",
        "credential",
        "ssn",
        "social_security",
        "nacionalidade",
        "etnia",
        "religiao",
        "orientacao_sexual",
        "genero",
        "estado_civil",
    }

    def anonymize_value(value: Any) -> Any:
        """Recursively anonymize a value."""
        if isinstance(value, str):
            # Replace string with anonymized version
            if len(value) > 3:
                return f"[ANONYMIZED: {value[:3]}...]"
            return "[ANONYMIZED]"
        elif isinstance(value, dict):
            return lgpd_anonymize(value, preserve_ids)
        elif isinstance(value, list):
            return [anonymize_value(item) for item in value]
        return value

    def is_sensitive(key: str) -> bool:
        """Check if a key is considered sensitive per LGPD."""
        key_lower = key.lower()
        for pattern in sensitive_patterns:
            if pattern in key_lower:
                return True
        return False

    def is_id_field(key: str) -> bool:
        """Check if key is a non-sensitive ID field."""
        key_lower = key.lower()
        id_patterns = {"id", "_id", "uuid", "guid", "pk", "foreign_key"}
        return any(pattern in key_lower for pattern in id_patterns)

    result = {}
    for key, value in payload.items():
        if is_id_field(key) and not is_sensitive(key):
            # Preserve non-sensitive ID fields
            result[key] = value
        elif is_sensitive(key):
            # Anonymize sensitive fields
            result[key] = anonymize_value(value)
        elif isinstance(value, dict):
            # Recursively process nested dicts
            result[key] = lgpd_anonymize(value, preserve_ids)
        elif isinstance(value, list):
            # Process list items
            result[key] = [
                (
                    lgpd_anonymize(item, preserve_ids)
                    if isinstance(item, dict)
                    else anonymize_value(item)
                )
                for item in value
            ]
        else:
            result[key] = value

    return result


def anonymize_list(
    items: List[Dict[str, Any]], preserve_ids: bool = True
) -> List[Dict[str, Any]]:
    """
    Anonymize a list of dictionaries.

    Args:
        items: List of dictionaries to anonymize
        preserve_ids: If True, keep non-sensitive IDs

    Returns:
        List of anonymized dictionaries
    """
    return [lgpd_anonymize(item, preserve_ids) for item in items]


def test_anonymization():
    """Test the anonymization function with sample data."""
    # Test 1: Basic anonymization
    test1 = {
        "nome": "João da Silva",
        "email": "joao@example.com",
        "idade": 30,
        "user_id": "12345",
    }
    result1 = lgpd_anonymize(test1)
    print("Test 1 - Basic:", result1)
    assert "[ANONYMIZED:" in result1["nome"]
    assert "[ANONYMIZED:" in result1["email"]
    assert result1["idade"] == 30  # Not sensitive
    assert result1["user_id"] == "12345"  # ID field preserved

    # Test 2: CPF anonymization
    test2 = {"cpf": "123.456.789-00", "data_nascimento": "1990-01-01"}
    result2 = lgpd_anonymize(test2)
    print("Test 2 - CPF:", result2)
    assert "[ANONYMIZED:" in result2["cpf"]
    assert "[ANONYMIZED:" in result2["data_nascimento"]

    # Test 3: Nested structure
    test3 = {
        "user": {
            "nome": "Maria",
            "email": "maria@test.com",
            "profile": {"cpf": "987.654.321-00", "idade": 25},
        }
    }
    result3 = lgpd_anonymize(test3)
    print("Test 3 - Nested:", result3)
    assert "[ANONYMIZED:" in result3["user"]["nome"]
    assert "[ANONYMIZED:" in result3["user"]["email"]
    assert "[ANONYMIZED:" in result3["user"]["profile"]["cpf"]
    assert result3["user"]["profile"]["idade"] == 25

    print("\nAll tests passed! ✓")
    return True


if __name__ == "__main__":
    test_anonymization()
