"""
Bootstrap script for initializing the database with sample data.

Usage:
    uv run python -m scripts.bootstrap_db
"""

import json
import logging
import sys
from typing import Any

from sqlmodel import Session, SQLModel

from app.db import engine
from app.models import Actor, Corpus, Document, DocumentLabelAssignment, Label, LabelSet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def create_db_and_tables():
    """
    Create all database tables.
    """
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created.")


def build_actors(data) -> tuple[list[Actor], dict[str, Actor]]:
    """
    Build Actor instances and a name lookup.

    Parameters
    ----------
    data : list of dict
        Actor data.

    Returns
    -------
    tuple
        (list of Actor, dict of name to Actor)
    """
    actors: list[Actor] = []
    lookup: dict[str, Actor] = {}

    for d in data:
        actor = Actor.model_validate(d)
        actors.append(actor)
        lookup[actor.name] = actor

    return actors, lookup


def build_corpora(data: list[dict], actors_by_name: dict[str, Actor]) -> list[Corpus]:
    """
    Build Corpus instances and their relationships.

    Parameters
    ----------
    data : list of dict
        Corpus data.
    actors_by_name : dict
        Name to Actor instance.

    Returns
    -------
    list
        List of Corpus instances.
    """
    corpora: list[Corpus] = []

    for c in data:
        label_sets_data: list[dict[str, Any]] = c.pop("label_sets", [])
        documents_list: list[dict[str, Any]] = c.pop("documents", [])
        corpus = Corpus.model_validate(c)
        corpora.append(corpus)

        label_sets: list[LabelSet] = []
        labels_by_value_and_suggester: dict[tuple[str, str], Label] = {}
        for label_set_dict in label_sets_data:
            suggester_name = label_set_dict["suggester"]
            suggester = actors_by_name[suggester_name]
            label_set = LabelSet(suggester=suggester, corpus=corpus)

            label_set.labels = [Label(value=val, label_set=label_set) for val in label_set_dict["labels"]]
            for label in label_set.labels:
                labels_by_value_and_suggester[(label.value, suggester_name)] = label

            label_sets.append(label_set)

        corpus.label_sets = label_sets
        docs: list[Document] = []
        for doc in documents_list:
            assignments: list[dict[str, Any]] = doc.pop("assignments", [])
            document = Document(corpus=corpus, **doc)
            document.assignments = [
                DocumentLabelAssignment(
                    document=document,
                    label=labels_by_value_and_suggester[(a["label"], a["label_set_suggester"])],
                    assigner=actors_by_name[a["assigner"]],
                )
                for a in assignments
            ]

            docs.append(document)

        corpus.documents = docs

    return corpora


def load_data(path) -> tuple[list[Actor], list[Corpus]]:
    """
    Load and build all model objects from JSON.

    Parameters
    ----------
    path : str
        Path to JSON file.

    Returns
    -------
    tuple
        (list of Actor, list of Corpus)
    """
    with open(path) as f:
        data = json.load(f)

    actors, actors_by_name = build_actors(data.get("actors", []))
    corpora = build_corpora(data.get("corpora", []), actors_by_name)

    logger.info(f"Loaded {len(actors)} actors and {len(corpora)} corpora from sample data.")

    return actors, corpora


def main():
    """
    Main entry point.
    """
    logger.info("Starting database bootstrap...")
    try:
        create_db_and_tables()
        actors, corpora = load_data("scripts/sample_data.json")

        with Session(engine) as session:
            for obj in actors + corpora:
                session.add(obj)

            session.commit()

        logger.info("Sample data committed to database.")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
