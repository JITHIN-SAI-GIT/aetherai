from app.memory.classifier import MemoryClassifier
from app.memory.models import MemoryClassification


clf = MemoryClassifier()


def test_classifies_preference():
    assert clf.classify("I prefer Python over JavaScript") == MemoryClassification.PREFERENCE


def test_classifies_project():
    assert clf.classify("I'm working on a new project") == MemoryClassification.PROJECT


def test_classifies_fact():
    assert clf.classify("My name is Bob") == MemoryClassification.FACT


def test_classifies_greeting_as_ignore():
    assert clf.classify("Hello there!") == MemoryClassification.IGNORE


def test_classifies_temporary():
    assert clf.classify("Just for now, use JSON") == MemoryClassification.TEMPORARY
