"""
Testes unitários para o Global Registry do Registro.

Este módulo testa o funcionamento do catálogo global de tipos que permite
resolver 'nome_do_recurso' -> 'ClassePython' de forma automática.
"""

import pytest
from typing import Type
from unittest.mock import patch

from registro.core.global_registry import (
    GlobalRegistry, 
    registry, 
    register, 
    get, 
    create_instance
)
from registro.core.resource_base import ResourceTypeBaseModel


class TestGlobalRegistry:
    """Testes para a classe GlobalRegistry."""
    
    def setup_method(self):
        """Configura um registry limpo para cada teste."""
        # Limpa o registry para testes isolados
        registry.clear()
    
    def test_singleton_pattern(self):
        """Testa que GlobalRegistry implementa Singleton pattern."""
        registry1 = GlobalRegistry()
        registry2 = GlobalRegistry()
        
        # Deve ser a mesma instância
        assert registry1 is registry2
        assert id(registry1) == id(registry2)
    
    def test_register_and_get(self):
        """Testa registro e recuperação de tipos."""
        # Define uma classe de teste
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test_model"
            name: str
        
        # Registra a classe
        registry.register("test_model", TestModel)
        
        # Verifica que foi registrada
        assert registry.is_registered("test_model")
        
        # Recupera a classe
        retrieved_class = registry.get("test_model")
        assert retrieved_class == TestModel
    
    def test_register_with_override_allowed(self):
        """Testa registro com permissão de sobrescrever."""
        class Model1(ResourceTypeBaseModel):
            __resource_type__ = "model"
            name: str
        
        class Model2(ResourceTypeBaseModel):
            __resource_type__ = "model" 
            value: int
        
        # Primeiro registro
        registry.register("model", Model1)
        assert registry.get("model") == Model1
        
        # Segundo registro com allow_override=True
        registry.register("model", Model2, allow_override=True)
        assert registry.get("model") == Model2
    
    def test_register_without_override_raises_error(self):
        """Testa que tentar sobrescrever sem permissão levanta erro."""
        class Model1(ResourceTypeBaseModel):
            __resource_type__ = "model"
            name: str
        
        class Model2(ResourceTypeBaseModel):
            __resource_type__ = "model"
            value: int
        
        # Primeiro registro
        registry.register("model", Model1)
        
        # Tentativa de sobrescrever sem permissão deve falhar
        with pytest.raises(ValueError, match="already registered"):
            registry.register("model", Model2, allow_override=False)
    
    def test_get_nonexistent_returns_none(self):
        """Testa que get() retorna None para tipos não registrados."""
        assert registry.get("nonexistent") is None
    
    def test_get_or_error_for_nonexistent(self):
        """Testa que get_or_error() levanta erro para tipos não registrados."""
        with pytest.raises(KeyError, match="not found in registry"):
            registry.get_or_error("nonexistent")
    
    def test_list_types(self):
        """Testa listagem de tipos registrados."""
        # Inicialmente vazio
        assert registry.list_types() == []
        
        # Registra alguns tipos manualmente (evitando auto-registro)
        class Model1(ResourceTypeBaseModel):
            __resource_type__ = "model1_manual"
        
        class Model2(ResourceTypeBaseModel):
            __resource_type__ = "model2_manual"
        
        # Limpa os auto-registrados e registra manualmente
        registry.clear()
        registry.register("type1", Model1)
        registry.register("type2", Model2)
        
        types = registry.list_types()
        assert "type1" in types
        assert "type2" in types
        assert len(types) == 2
    
    def test_unregister(self):
        """Testa remoção de registros."""
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test"
        
        # Registra
        registry.register("test", TestModel)
        assert registry.is_registered("test")
        
        # Remove
        removed_class = registry.unregister("test")
        assert removed_class == TestModel
        assert not registry.is_registered("test")
        
        # Tentar remover novamente deve retornar None
        assert registry.unregister("test") is None
    
    def test_create_instance(self):
        """Testa criação de instâncias via registry."""
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test"
            name: str
            value: int = 42
        
        # Registra
        registry.register("test", TestModel)
        
        # Cria instância com dados mínimos necessários
        instance = registry.create_instance(
            "test", 
            name="test_name",
            rid="ri.test.prod.test.1234567890ABCDEFGHIJ",  # RID necessário
            api_name="test_name"  # api_name necessário
        )
        
        assert isinstance(instance, TestModel)
        assert instance.name == "test_name"
        assert instance.value == 42  # valor default
    
    def test_create_instance_nonexistent_raises_error(self):
        """Testa que criar instância de tipo não registrado levanta erro."""
        with pytest.raises(KeyError, match="not found in registry"):
            registry.create_instance("nonexistent", name="test")
    
    def test_clear(self):
        """Testa limpeza do registry."""
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test"
        
        # Registra
        registry.register("test", TestModel)
        assert len(registry.list_types()) > 0
        
        # Limpa
        registry.clear()
        assert len(registry.list_types()) == 0
        assert not registry.is_registered("test")
    
    def test_get_stats(self):
        """Testa obtenção de estatísticas do registry."""
        # Inicialmente vazio
        stats = registry.get_stats()
        assert stats["total_types"] == 0
        assert stats["types"] == []
        assert stats["modules"] == []
        
        # Registra algumas classes manualmente (evita auto-registro)
        class Model1(ResourceTypeBaseModel):
            __resource_type__ = "model1_stats"
        
        class Model2(ResourceTypeBaseModel):
            __resource_type__ = "model2_stats"
        
        # Limpa e registra manualmente
        registry.clear()
        registry.register("type1", Model1)
        registry.register("type2", Model2)
        
        # Verifica estatísticas
        stats = registry.get_stats()
        assert stats["total_types"] == 2
        assert "type1" in stats["types"]
        assert "type2" in stats["types"]
        # Verifica se o módulo está na lista (pode ter formato diferente)
        modules_str = " ".join(stats["modules"])
        assert "test_global_registry" in modules_str


class TestFacadeFunctions:
    """Testa as funções facade para facilitar o uso."""
    
    def setup_method(self):
        """Limpa o registry antes de cada teste."""
        registry.clear()
    
    def test_register_facade_function(self):
        """Testa função facade register()."""
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test"
        
        register("test", TestModel)
        assert registry.get("test") == TestModel
    
    def test_get_facade_function(self):
        """Testa função facade get()."""
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test"
        
        registry.register("test", TestModel)
        retrieved = get("test")
        assert retrieved == TestModel
    
    def test_create_instance_facade_function(self):
        """Testa função facade create_instance()."""
        class TestModel(ResourceTypeBaseModel):
            __resource_type__ = "test_facade"
            name: str
        
        registry.register("test_facade", TestModel)
        instance = create_instance(
            "test_facade", 
            name="test_name",
            rid="ri.test.prod.test_facade.1234567890ABCDEFGHIJ",
            api_name="test_name"
        )
        
        assert isinstance(instance, TestModel)
        assert instance.name == "test_name"


class TestAutoRegistration:
    """Testa o auto-registro via __init_subclass__."""
    
    def setup_method(self):
        """Limpa o registry antes de cada teste."""
        registry.clear()
    
    def test_auto_registration_on_subclass_creation(self):
        """Testa que subclasses são automaticamente registradas."""
        # Define uma classe herdando de ResourceTypeBaseModel
        class AutoRegisteredModel(ResourceTypeBaseModel):
            __resource_type__ = "auto_model"
            name: str
        
        # A classe deve ser automaticamente registrada
        assert registry.is_registered("auto_model")
        retrieved_class = registry.get("auto_model")
        assert retrieved_class == AutoRegisteredModel
    
    def test_no_auto_registration_without_resource_type(self):
        """Testa que classes sem __resource_type__ não são registradas."""
        # A verificação é feita apenas para classes com __tablename__
        # Define uma classe sem __tablename__ para testar
        class NoResourceTypeModel(ResourceTypeBaseModel):
            # Sem __tablename__, não deve tentar registrar
            name: str
        
        # Não deve ser registrada (não tem __tablename__)
        assert not registry.is_registered("noresourcetypemodel")
    
    def test_multiple_inheritance_registration(self):
        """Testa registro com múltiplas heranças."""
        class Mixin:
            pass
        
        class MultiInheritanceModel(Mixin, ResourceTypeBaseModel):
            __resource_type__ = "multi_model"
            name: str
        
        # Deve ser registrada mesmo com herança múltipla
        assert registry.is_registered("multi_model")
        assert registry.get("multi_model") == MultiInheritanceModel
    
    def test_registration_override_warning(self):
        """Testa que sobrescrever registro gera warning."""
        with patch('registro.core.resource_base.logger') as mock_logger:
            # Primeira classe
            class OriginalModel(ResourceTypeBaseModel):
                __resource_type__ = "conflict_model"
                name: str
            
            # Segunda classe com mesmo tipo (gera warning)
            class ConflictModel(ResourceTypeBaseModel):
                __resource_type__ = "conflict_model"
                value: int
            
            # Deve ter gerado warning
            mock_logger.warning.assert_called()
            assert "Failed to auto-register" in str(mock_logger.warning.call_args)


class TestKernelIntegrationSimulation:
    """Testa simulação de como o Kernel usará o registry."""
    
    def setup_method(self):
        """Configura modelos de teste e limpa registry."""
        registry.clear()
        
        # Define modelos que o Kernel precisaria encontrar
        class User(ResourceTypeBaseModel):
            __resource_type__ = "user"
            name: str
            email: str
        
        class Product(ResourceTypeBaseModel):
            __resource_type__ = "product"
            title: str
            price: float
    
    def test_kernel_dynamic_resolution(self):
        """Simula como o Kernel resolveria tipos dinamicamente."""
        # RID de exemplo: "ri.myapp.prod.user.12345"
        rid = "ri.myapp.prod.user.12345"
        
        # Kernel extrai o tipo do RID (usando função de identity)
        from registro.core.identity import get_resource_type_from_rid
        resource_type = get_resource_type_from_rid(rid)
        
        assert resource_type == "user"
        
        # Kernel obtém a classe do registry
        UserClass = registry.get_or_error(resource_type)
        
        # Kernel pode agora criar instâncias ou fazer queries
        assert UserClass.__name__ == "User"
        
        # Simula criar instância a partir de dados do banco
        user_instance = UserClass(
            name="Test User", 
            email="test@example.com",
            rid="ri.myapp.prod.user.1234567890ABCDEFGHIJ",
            api_name="test_user"
        )
        assert user_instance.name == "Test User"
    
    def test_kernel_can_list_all_available_types(self):
        """Testa que o Kernel pode listar todos os tipos disponíveis."""
        available_types = registry.list_types()
        
        assert "user" in available_types
        assert "product" in available_types
        
        # Kernel pode usar isso para validação ou UI
        stats = registry.get_stats()
        assert stats["total_types"] == 2
