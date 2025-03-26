from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.persistence import SyncPersistenceProtocol
from sqlmodel import Session, SQLModel
from typing import Any, List, TypeVar

T = TypeVar("T")


class SyncPersistenceHandler(SyncPersistenceProtocol[SQLModel]):
    def save(self, session: Session, data: SQLModel) -> SQLModel:
        session.add(data)

        try:
            session.flush()
        except Exception:
            session.rollback()
            raise

        return data

    def save_many(self, session: Session, data: List[SQLModel]) -> List[SQLModel]:
        session.add_all(data)

        try:
            session.flush()
        except Exception:
            session.rollback()
            raise

        return data


class SQLModelFactory(ModelFactory[T]):
    __is_base_factory__ = True
    __sync_persistence__ = SyncPersistenceHandler

    @classmethod
    def create(cls, session, **kwargs: Any) -> T:
        return cls._get_sync_persistence().save(
            session=session, data=cls.build(**kwargs)
        )
