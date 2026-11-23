"""The side stories of the protagonists (spec 18, "Side stories"), played from the first word to the ending with the story of the reference:
only the protagonist with the keepsake hears them, the quests come one after the other, and each ending gives its own thing once."""
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from make_side_stories import STORIES  # noqa: E402
from reference.story import Story  # noqa: E402

DATA = TOOLS.parent / "data" / "base"


class Host:
    """The little a story needs from the world: a bag, a level, a day."""

    def __init__(self, keepsake: str | None) -> None:
        self.inventory: dict[str, int] = {keepsake: 1} if keepsake else {}
        self.level = 30
        self.x = self.y = 0.0

    def grant_xp(self, amount: int) -> None:
        pass

    def day(self) -> int:
        return 1

    def quest_done(self, quest_id: str) -> None:
        pass


def story_for(entry: dict, keepsake: str | None) -> Story:
    dialogue_id = f"base:dialogue/npc/{entry['file']}"
    quests = {f"base:quest/side/{q[0]}": json.loads((DATA / "quests" / "side" / f"{q[0]}.json").read_text(encoding="utf-8"))
              for q in entry["quests"]}
    dialogues = {dialogue_id: json.loads((DATA / "dialogues" / "npc" / f"{entry['file']}.json").read_text(encoding="utf-8"))}
    return Story(Host(keepsake), {"quests": quests, "dialogues": dialogues, "npcs": []})


def talk(story: Story, entry: dict) -> list[str]:
    """Opens the dialogue and reads it to the first choice or the end: the texts said."""
    story.start_dialogue(f"base:dialogue/npc/{entry['file']}")
    said = []
    while story.dialogue is not None and story.dialogue_view()["type"] == "say":
        said.append(story.dialogue_view()["text"])
        story.advance()
    return said


def finish(story: Story, quest: tuple) -> None:
    """Does what the quest asks: the kills, and the things in the bag."""
    for objective in quest[3]:
        if objective["type"] == "kill":
            for _ in range(objective["count"]):
                story.on_kill(objective["enemy"])
        else:
            story.host.inventory[objective["item"]] = objective["count"]
            story._refresh_all()


def test_a_stranger_hears_only_a_line():
    for entry in STORIES:
        story = story_for(entry, None)
        assert talk(story, entry) == [f"$i18n:dlg.side.{entry['file']}.stranger"]
        assert story.dialogue is None and not story.quests


def test_the_protagonist_plays_the_story_to_either_ending():
    for entry in STORIES:
        for side in ("a", "b"):
            story = story_for(entry, f"base:item/keepsake_{entry['protagonist']}")
            for i, quest in enumerate(entry["quests"]):
                said = talk(story, entry)
                assert said[-1] == f"$i18n:dlg.side.{entry['file']}.{quest[0]}.offer", (entry["key"], i, said)
                story.choose(0)  # accept
                assert story.quests[f"base:quest/side/{quest[0]}"]["done"] is False
                assert talk(story, entry)[-1] == f"$i18n:dlg.side.{entry['file']}.{quest[0]}.busy"
                finish(story, quest)
                assert story.quests[f"base:quest/side/{quest[0]}"]["done"] is True
            said = talk(story, entry)
            assert said[-1] == f"$i18n:dlg.side.{entry['file']}.ending", said
            story.choose(0 if side == "a" else 1)
            item = entry["ending"][side][1]
            other = entry["ending"]["b" if side == "a" else "a"][1]
            assert story.host.inventory.get(item) == 1 and other not in story.host.inventory
            assert story.dialogue_view()["text"] == f"$i18n:dlg.side.{entry['file']}.reply_{side}"
            story.advance()
            assert talk(story, entry) == [f"$i18n:dlg.side.{entry['file']}.after"]  # the ending is given once
            assert story.host.inventory.get(item) == 1


def test_every_text_of_the_side_stories_exists_in_both_languages():
    for lang in ("en", "it"):
        texts = {}
        for path in (DATA / "i18n" / lang).glob("*.json"):
            texts.update(json.loads(path.read_text(encoding="utf-8")))
        for entry in STORIES:
            dialogue = json.loads((DATA / "dialogues" / "npc" / f"{entry['file']}.json").read_text(encoding="utf-8"))
            keys = [n["text"] for n in dialogue["nodes"].values() if n["type"] == "say"]
            keys += [c["text"] for n in dialogue["nodes"].values() if n["type"] == "choice" for c in n["choices"]]
            keys += [f"$i18n:speaker.{entry['key']}"]
            for key in keys:
                assert key.removeprefix("$i18n:") in texts, (lang, key)
