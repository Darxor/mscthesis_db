from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from .model_mixins import SoftDeletionMixin, TimeAuditMixin, UUIDMixin


class BaseTable(SQLModel, SoftDeletionMixin, TimeAuditMixin, UUIDMixin):
    """Base class for all tables"""

    pass


class ActorTypes(StrEnum):
    """Enum for actor types"""

    HUMAN = "HUMAN"
    LLM = "LLM"
    NLI = "NLI"


class Actor(BaseTable, table=True):
    """An actor is a person or model that suggests or assigns labels"""

    __tablename__ = "actors"  # type: ignore

    name: str
    type: ActorTypes = Field(sa_column=sa.Column(sa.Enum(ActorTypes, create_constraint=True), nullable=False))
    parameters: dict | None = Field(default=None, nullable=True, sa_type=sa.JSON)

    label_sets: list["LabelSet"] = Relationship(back_populates="suggester")
    assignments: list["DocumentLabelAssignment"] = Relationship(back_populates="assigner")


class CorpusCategory(StrEnum):
    """Enum for corpus categories"""

    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    OTHER = "OTHER"


class Corpus(BaseTable, table=True):
    """A corpus is a collection of documents"""

    __tablename__ = "corpora"  # type: ignore

    name: str
    category: CorpusCategory | None = Field(
        sa_column=sa.Column(sa.Enum(CorpusCategory, create_constraint=True), nullable=False)
    )
    description: str | None = None

    documents: list["Document"] = Relationship(back_populates="corpus")
    label_sets: list["LabelSet"] = Relationship(back_populates="corpus")


class Document(BaseTable, table=True):
    """A document is a text that belongs to a corpora"""

    __tablename__ = "documents"  # type: ignore

    corpus_uid: UUID | None = Field(default=None, foreign_key="corpora.uid")
    text: str

    corpus: Corpus | None = Relationship(back_populates="documents")
    assignments: list["DocumentLabelAssignment"] = Relationship(back_populates="document")


class LabelSet(BaseTable, table=True):
    """A label set is a collection of labels that are suggested for a document"""

    __tablename__ = "labelsets"  # type: ignore

    corpus_uid: UUID | None = Field(default=None, foreign_key="corpora.uid")
    suggester_uid: UUID | None = Field(default=None, foreign_key="actors.uid")

    corpus: Corpus | None = Relationship(back_populates="label_sets")
    suggester: Actor | None = Relationship(back_populates="label_sets")
    labels: list["Label"] = Relationship(back_populates="label_set")


class Label(BaseTable, table=True):
    """A label is a single label that belongs to a label set"""

    __tablename__ = "labels"  # type: ignore

    label_set_uid: UUID | None = Field(default=None, foreign_key="labelsets.uid")
    value: str

    label_set: LabelSet | None = Relationship(back_populates="labels")
    assignments: list["DocumentLabelAssignment"] = Relationship(back_populates="label")


class DocumentLabelAssignment(BaseTable, table=True):
    """A document label assignment connects a label with a document"""

    __tablename__ = "document_label_assignments"  # type: ignore

    document_uid: UUID | None = Field(default=None, foreign_key="documents.uid")
    label_uid: UUID | None = Field(default=None, foreign_key="labels.uid")
    assigner_uid: UUID | None = Field(default=None, foreign_key="actors.uid")

    document: Document | None = Relationship(back_populates="assignments")
    label: Label | None = Relationship(back_populates="assignments")
    assigner: Actor | None = Relationship(back_populates="assignments")
