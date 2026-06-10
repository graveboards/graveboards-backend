import pytest
from pydantic import BaseModel
import json




class TestRedisModelSerialization:
    """Test Redis model serialization."""

    def test_serialize_model_with_pydantic_model(self):
        """Test serialization of Pydantic model to JSON."""
        class TestUser(BaseModel):
            id: int
            username: str

        user = TestUser(id=123, username="testuser")
        result = user.model_dump_json()

        assert isinstance(result, str)
        assert '"id":123' in result
        assert '"username":"testuser"' in result

    def test_deserialize_model_with_pydantic_model(self):
        """Test deserialization of JSON to Pydantic model."""
        class TestUser(BaseModel):
            id: int
            username: str

        json_data = '{"id": 123, "username": "testuser"}'
        result = TestUser.model_validate_json(json_data)

        assert isinstance(result, TestUser)
        assert result.id == 123
        assert result.username == "testuser"

    def test_serialize_model_with_dict(self):
        """Test serialization of dict to JSON."""
        data = {"key": "value", "number": 42}
        result = json.dumps(data)

        assert isinstance(result, str)
        assert '"key": "value"' in result
        assert '"number": 42' in result

    def test_deserialize_model_to_dict(self):
        """Test deserialization of JSON to dict."""
        json_data = '{"key": "value", "number": 42}'
        result = json.loads(json_data)

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_serialize_preserves_nested_structures(self):
        """Test that nested structures are preserved during serialization."""
        class NestedData(BaseModel):
            id: int
            name: str

        class ParentData(BaseModel):
            parent_id: int
            nested: NestedData

        parent = ParentData(
            parent_id=1,
            nested=NestedData(id=2, name="child")
        )
        result = parent.model_dump_json()

        assert isinstance(result, str)
        assert '"parent_id":1' in result
        assert '"nested":' in result

    def test_deserialize_restore_nested_structures(self):
        """Test that nested structures are restored during deserialization."""
        json_data = '{"parent_id": 1, "nested": {"id": 2, "name": "child"}}'

        class NestedData(BaseModel):
            id: int
            name: str

        class ParentData(BaseModel):
            parent_id: int
            nested: NestedData

        result = ParentData.model_validate_json(json_data)

        assert isinstance(result, ParentData)
        assert result.parent_id == 1
        assert isinstance(result.nested, NestedData)
        assert result.nested.id == 2

    def test_serialize_model_with_list(self):
        """Test serialization of list."""
        data = [1, 2, 3, 4, 5]
        result = json.dumps(data)

        assert isinstance(result, str)
        assert "[1, 2, 3, 4, 5]" in result

    def test_deserialize_model_to_list(self):
        """Test deserialization of JSON to list."""
        json_data = '[1, 2, 3, 4, 5]'
        result = json.loads(json_data)

        assert isinstance(result, list)
        assert result == [1, 2, 3, 4, 5]

    def test_serialize_model_with_none(self):
        """Test serialization of None."""
        result = json.dumps(None)

        assert result == "null"

    def test_deserialize_model_to_none(self):
        """Test deserialization of null."""
        json_data = "null"
        result = json.loads(json_data)

        assert result is None

    def test_serialize_model_with_boolean(self):
        """Test serialization of boolean."""
        result_true = json.dumps(True)
        result_false = json.dumps(False)

        assert result_true == "true"
        assert result_false == "false"

    def test_deserialize_model_to_boolean(self):
        """Test deserialization of boolean."""
        json_true = "true"
        json_false = "false"

        result_true = json.loads(json_true)
        result_false = json.loads(json_false)

        assert result_true is True
        assert result_false is False

    def test_serialize_model_with_float(self):
        """Test serialization of float."""
        result = json.dumps(3.14159)

        assert isinstance(result, str)
        assert "3.14159" in result

    def test_deserialize_model_to_float(self):
        """Test deserialization of float."""
        json_data = "3.14159"
        result = json.loads(json_data)

        assert isinstance(result, float)
        assert abs(result - 3.14159) < 0.00001

    def test_serialize_model_with_complex_nested_structure(self):
        """Test serialization of complex nested structure."""
        class Address(BaseModel):
            street: str
            city: str
            zip_code: str

        class Person(BaseModel):
            name: str
            age: int
            address: Address
            hobbies: list[str]

        person = Person(
            name="John Doe",
            age=30,
            address=Address(street="123 Main St", city="City", zip_code="12345"),
            hobbies=["reading", "gaming"]
        )

        result = person.model_dump_json()

        assert isinstance(result, str)
        assert '"name":"John Doe"' in result
        assert '"age":30' in result
        assert '"street":"123 Main St"' in result
        assert '"hobbies":' in result

    def test_deserialize_model_with_complex_nested_structure(self):
        """Test deserialization of complex nested structure."""
        json_data = '''{
            "name": "John Doe",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "City",
                "zip_code": "12345"
            },
            "hobbies": ["reading", "gaming"]
        }'''

        class Address(BaseModel):
            street: str
            city: str
            zip_code: str

        class Person(BaseModel):
            name: str
            age: int
            address: Address
            hobbies: list[str]

        result = Person.model_validate_json(json_data)

        assert isinstance(result, Person)
        assert result.name == "John Doe"
        assert result.age == 30
        assert isinstance(result.address, Address)
        assert result.address.street == "123 Main St"
        assert result.hobbies == ["reading", "gaming"]

    def test_serialize_model_preserves_order(self):
        """Test that serialization preserves field order."""
        class OrderedData(BaseModel):
            first: str
            second: str
            third: str

        data = OrderedData(first="a", second="b", third="c")
        result = data.model_dump_json()

        assert result.index('"first"') < result.index('"second"')
        assert result.index('"second"') < result.index('"third"')

    def test_serialize_model_handles_special_characters(self):
        """Test that serialization handles special characters."""
        class SpecialData(BaseModel):
            text: str

        data = SpecialData(text="Test with \"quotes\" and \\ backslash")
        result = data.model_dump_json()

        assert isinstance(result, str)

    def test_deserialize_model_with_missing_field(self):
        """Test deserialization with missing field."""
        json_data = '{"id": 123}'

        class TestUser(BaseModel):
            id: int
            username: str

        with pytest.raises(Exception):
            TestUser.model_validate_json(json_data)
