from app.conversation.persona import load_persona, DEFAULT_PERSONA
from app.conversation.policies import POLICIES


def test_persona_has_name():
    assert DEFAULT_PERSONA.name


def test_persona_system_instructions_prohibits_banned_phrases():
    """The instructions should reference banned phrases as prohibitions, not use them."""
    instructions = DEFAULT_PERSONA.system_instructions()
    # Instructions should contain the word "Never" indicating prohibition
    assert "Never" in instructions
    # The banned phrases are cited inside the instructions for prohibition;
    # verify the prohibition clause is present.
    assert "use these banned phrases" in instructions.lower()


def test_persona_instructions_contain_name():
    p = load_persona()
    assert p.name in p.system_instructions()
