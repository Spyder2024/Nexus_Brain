"""Enterprise Synthetic Data Generator for NexusBrain."""

__all__ = ["EnterpriseDataGenerator"]


def __getattr__(name: str):
    if name == "EnterpriseDataGenerator":
        from src.data_gen.company_generator import EnterpriseDataGenerator
        return EnterpriseDataGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
