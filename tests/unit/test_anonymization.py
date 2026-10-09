"""Unit tests for LGPD anonymization."""

import pytest
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.security.anonymization import lgpd_anonymize, anonymize_list


class TestAnonymization:
    """Test LGPD anonymization functions."""

    def test_anonymizes_sensitive_strings(self):
        """Test that sensitive strings are anonymized."""
        payload = {"nome": "João da Silva", "email": "joao@example.com"}
        result = lgpd_anonymize(payload)

        assert "[ANONYMIZED:" in result["nome"]
        assert "[ANONYMIZED:" in result["email"]
        assert result["nome"] != "João da Silva"
        assert result["email"] != "joao@example.com"

    def test_preserves_non_sensitive_fields(self):
        """Test that non-sensitive fields are preserved."""
        payload = {"user_id": "12345", "idade": 30, "ativo": True}
        result = lgpd_anonymize(payload)

        assert result["user_id"] == "12345"
        assert result["idade"] == 30
        assert result["ativo"] is True

    def test_preserves_id_fields(self):
        """Test that ID fields are preserved."""
        payload = {
            "id": "123",
            "tenant_id": "456",
            "user_uuid": "abc-123",
            "cpf": "123.456.789-00",
        }
        result = lgpd_anonymize(payload)

        assert result["id"] == "123"
        assert result["tenant_id"] == "456"
        assert result["user_uuid"] == "abc-123"
        assert "[ANONYMIZED:" in result["cpf"]

    def test_anonymizes_nested_structures(self):
        """Test nested dictionary anonymization."""
        payload = {
            "user": {
                "nome": "Maria",
                "email": "maria@test.com",
                "profile": {"cpf": "987.654.321-00", "idade": 25},
            }
        }
        result = lgpd_anonymize(payload)

        assert "[ANONYMIZED:" in result["user"]["nome"]
        assert "[ANONYMIZED:" in result["user"]["email"]
        assert "[ANONYMIZED:" in result["user"]["profile"]["cpf"]
        assert result["user"]["profile"]["idade"] == 25

    def test_anonymizes_list_of_dicts(self):
        """Test list of dictionaries anonymization."""
        items = [{"nome": "João", "idade": 30}, {"nome": "Maria", "idade": 25}]
        result = anonymize_list(items)

        assert "[ANONYMIZED:" in result[0]["nome"]
        assert "[ANONYMIZED:" in result[1]["nome"]
        assert result[0]["idade"] == 30
        assert result[1]["idade"] == 25

    def test_anonymizes_cpf(self):
        """Test CPF anonymization."""
        payload = {"cpf": "123.456.789-00"}
        result = lgpd_anonymize(payload)

        assert "[ANONYMIZED:" in result["cpf"]
        assert result["cpf"] != "123.456.789-00"

    def test_anonymizes_cnpj(self):
        """Test CNPJ anonymization."""
        payload = {"cnpj": "12.345.678/0001-99"}
        result = lgpd_anonymize(payload)

        assert "[ANONYMIZED:" in result["cnpj"]

    def test_anonymizes_data_nascimento(self):
        """Test birth date anonymization."""
        payload = {"data_nascimento": "1990-01-15"}
        result = lgpd_anonymize(payload)

        assert "[ANONYMIZED:" in result["data_nascimento"]

    def test_preserves_tenant_id(self):
        """Test that tenant_id is preserved (non-sensitive ID)."""
        payload = {"tenant_id": "empresa_123", "nome": "Cliente"}
        result = lgpd_anonymize(payload)

        assert result["tenant_id"] == "empresa_123"
        assert "[ANONYMIZED:" in result["nome"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
