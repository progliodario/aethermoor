#!/usr/bin/env python3
"""Writes the prologues of the protagonists (data/base/dialogues/<name>/prologue.json) and their texts: a short talk with Lyra at the
Threshold, shown when a new game starts (spec 18, "Prologue"). Run it after changing the texts here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

# protagonist: the lines of Lyra (n1, n2), two answers (c1, c2), her reply to each (r1, r2) and her last line (n3); (en, it) each.
# The first answer sets the flag `<name>.prologue_first`: later dialogues may remember how the Guest took the news.
PROLOGUES = {
    "ren": {
        "n1": ("Welcome, Guest. Your old world has let you go.", "Benvenuto, Ospite. Il tuo vecchio mondo ti ha lasciato andare."),
        "n2": ("You were never late, Ren Takahashi. Not once. I checked.", "Non sei mai arrivato in ritardo, Ren Takahashi. Nemmeno una volta. Ho controllato."),
        "c1": ("Okay, I'm in.", "Va bene, ci sto."),
        "c2": ("Wait... was it the truck?", "Aspetta... è stato il camion?"),
        "r1": ("That was quick. Most people ask about the truck.", "Che rapidità. Di solito chiedono del camion."),
        "r2": ("Let's say the truck played a part.", "Diciamo che il camion ha fatto la sua parte."),
        "n3": ("You will see numbers over what wants to hurt you. Read them. Verdalis begins in a meadow, like most good things.",
               "Vedrai dei numeri sopra ciò che vuole farti male. Leggili. Verdalis comincia in un prato, come quasi tutte le cose buone."),
    },
    "sakura": {
        "n1": ("Welcome, Guest. Your machine says thank you, by the way.", "Benvenuta, Ospite. La tua macchina ti ringrazia, a proposito."),
        "n2": ("You opened a door in the air three minutes before your doctorate, Sakura Mori. I admire the timing.",
               "Hai aperto una porta nell'aria tre minuti prima del dottorato, Sakura Mori. Ammiro il tempismo."),
        "c1": ("Can I at least publish this?", "Posso almeno pubblicarlo?"),
        "c2": ("My calculations were correct!", "I miei calcoli erano giusti!"),
        "r1": ("There are no journals here. There are taverns. It is nearly the same thing.", "Qui non ci sono riviste. Ci sono taverne. È quasi la stessa cosa."),
        "r2": ("They were. That is exactly the problem.", "Lo erano. È proprio questo il problema."),
        "n3": ("Here your numbers come out as light. Aim them away from the villagers. An owl called Newton will keep you company.",
               "Qui i tuoi numeri escono come luce. Puntali lontano dai paesani. Un gufo di nome Newton ti terrà compagnia."),
    },
    "daichi": {
        "n1": ("Welcome, Guest. Sit, if you can. You have earned it.", "Benvenuto, Ospite. Siediti, se riesci. Te lo sei guadagnato."),
        "n2": ("You went back in one more time, Daichi Okabe. The child on the third floor is alive.",
               "Sei rientrato ancora una volta, Daichi Okabe. La bambina del terzo piano è viva."),
        "c1": ("Then it was worth it.", "Allora ne è valsa la pena."),
        "c2": ("Is anyone here in trouble?", "Qui c'è qualcuno in pericolo?"),
        "r1": ("I thought you would say that.", "Immaginavo che l'avresti detto."),
        "r2": ("Always. That is why I chose you.", "Sempre. Per questo ho scelto te."),
        "n3": ("This world burns now and then. You will have an axe, and a shield that does not let go. Do not carry everything alone.",
               "Questo mondo ogni tanto brucia. Avrai un'ascia e uno scudo che non molla. Non portare tutto da solo."),
    },
    "haruka": {
        "n1": ("Welcome, Guest. The dog is fine. I thought you would want to know first.", "Benvenuta, Ospite. Il cane sta bene. Ho pensato che volessi saperlo per prima cosa."),
        "n2": ("You stopped in the rain for a creature nobody owned, Haruka Aizawa. Few do.",
               "Ti sei fermata sotto la pioggia per una creatura che non era di nessuno, Haruka Aizawa. Pochi lo fanno."),
        "c1": ("Thank you. Truly.", "Grazie. Davvero."),
        "c2": ("Who will look after my patients?", "Chi si occuperà dei miei pazienti?"),
        "r1": ("Thank the dog. It made a good case for you.", "Ringrazia il cane. Ha parlato bene di te."),
        "r2": ("Someone kind. I saw to it.", "Qualcuno di gentile. Ci ho pensato io."),
        "n3": ("Where you are going, the creatures hurt and are too proud to say so. A small slime is already waiting for you. Be patient with it.",
               "Dove stai andando, le creature soffrono e sono troppo orgogliose per dirlo. Un piccolo slime ti sta già aspettando. Abbi pazienza con lui."),
    },
    "marco": {
        "n1": ("Welcome, Guest. Dinner for forty is cancelled, I am afraid.", "Benvenuto, Ospite. La cena per quaranta è annullata, temo."),
        "n2": ("A pressure cooker, Marco Ferri. You of all people.", "Una pentola a pressione, Marco Ferri. Proprio tu."),
        "c1": ("It was a matter of units.", "È stata una questione di unità di misura."),
        "c2": ("Did anyone at least taste the sauce?", "Almeno qualcuno ha assaggiato il sugo?"),
        "r1": ("It usually is.", "Di solito lo è."),
        "r2": ("The ceiling did. It had no complaints.", "Il soffitto sì. Non si è lamentato."),
        "n3": ("The world below has never heard of salt, soap or valves. Go gently. A crab has taken a liking to your wrench.",
               "Il mondo di sotto non ha mai sentito parlare di sale, sapone o valvole. Vacci piano. Un granchio si è affezionato alla tua chiave inglese."),
    },
    "yuki": {
        "n1": ("Welcome, Guest. That was a very long jump.", "Benvenuta, Ospite. È stato un salto molto lungo."),
        "n2": ("The painting landed well, Yuki Shirogane. You, less so.", "Il quadro è atterrato bene, Yuki Shirogane. Tu, un po' meno."),
        "c1": ("So what's the catch?", "E dov'è la fregatura?"),
        "c2": ("I never took anything from someone who would miss it.", "Non ho mai preso niente a chi ne avrebbe sentito la mancanza."),
        "r1": ("No catch. No locks either. You will hate it.", "Nessuna fregatura. Nemmeno serrature. Lo odierai."),
        "r2": ("I know. It is the only reason we are talking.", "Lo so. È l'unico motivo per cui stiamo parlando."),
        "n3": ("You will have a pocket no one can search and a shadow with wings. Try giving something back, for once. See how it feels.",
               "Avrai una tasca che nessuno può perquisire e un'ombra con le ali. Prova a restituire qualcosa, per una volta. Senti che effetto fa."),
    },
    "lena": {
        "n1": ("Welcome, Guest. You were curious about this part, I believe.", "Benvenuta, Ospite. Eri curiosa di questa parte, mi pare."),
        "n2": ("You have signed a great many endings, Lena Voss. This one is not yours to sign.",
               "Hai firmato moltissime fini, Lena Voss. Questa non tocca a te firmarla."),
        "c1": ("Cause of death?", "Causa del decesso?"),
        "c2": ("I would like to take notes.", "Vorrei prendere appunti."),
        "r1": ("Curiosity. As you suspected.", "Curiosità. Come sospettavi."),
        "r2": ("You always do. I will speak slowly.", "Lo fai sempre. Parlerò lentamente."),
        "n3": ("Below, you will see what kills before it does. And when it does anyway, you will get one more try. Use it for the living.",
               "Di sotto vedrai ciò che uccide prima che lo faccia. E quando lo farà comunque, avrai un altro tentativo. Usalo per i vivi."),
    },
    "gideon": {
        "n1": ("Welcome, Guest. Yes, you. Do stop glaring.", "Benvenuto, Ospite. Sì, tu. E smettila di fissarmi così."),
        "n2": ("Three hundred years on a throne, Gideon Valmor, and one afternoon to lose it. I did try to be gentle.",
               "Trecento anni su un trono, Gideon Valmor, e un pomeriggio per perderlo. Ho cercato di essere delicata."),
        "c1": ("I demand a rematch.", "Esigo la rivincita."),
        "c2": ("...What do they eat, in this village?", "...Cosa si mangia, in questo villaggio?"),
        "r1": ("Noted. Refused. Ask again in a hundred years.", "Annotato. Respinto. Riprova fra cent'anni."),
        "r2": ("Bread. Stew. They will offer you both. Say thank you.", "Pane. Stufato. Te li offriranno entrambi. Di' grazie."),
        "n3": ("You keep the black sword and a wolf of shadow. Nobody down there has heard of you. Consider it my gift.",
               "Ti restano la spada nera e un lupo d'ombra. Laggiù nessuno ha mai sentito parlare di te. Consideralo il mio regalo."),
    },
}


def add_texts(lang: str, entries: dict[str, str]) -> None:
    """Sets the texts in content.json: the lines that exist are replaced, the new ones are added after the last `dlg.` line."""
    path = DATA / "i18n" / lang / "content.json"
    raw = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    where = {line.split('"')[1]: k for k, line in enumerate(lines) if line.startswith('  "')}
    anchor = max(k for k, line in enumerate(lines) if line.startswith('  "dlg.'))
    for key, value in entries.items():
        text = f'  "{key}": {json.dumps(value, ensure_ascii=False)},'
        if key in where:
            lines[where[key]] = text
        else:
            anchor += 1
            lines.insert(anchor, text)
            where = {k: (v + 1 if v >= anchor else v) for k, v in where.items()}
    path.write_text(newline.join(lines), encoding="utf-8", newline="")


def main() -> None:
    en: dict[str, str] = {}
    it: dict[str, str] = {}
    for name, lines in PROLOGUES.items():
        def key(node: str, name: str = name) -> str:
            return f"dlg.{name}.prologue.{node}"

        def say(node: str, then: str, expression: str | None = None) -> dict:
            out = {"type": "say", "speaker": "goddess_lyra", "text": "$i18n:" + key(node), "next": then}
            if expression:
                out["expression"] = expression
            return out

        doc = {
            "$schema": "../../../../schemas/dialogue.schema.json",
            "id": f"base:dialogue/{name}/prologue",
            "start": "n1",
            "nodes": {
                "n1": say("n1", "n2", "gentle"),
                "n2": say("n2", "ask"),
                "ask": {"type": "choice", "choices": [{"text": "$i18n:" + key("c1"), "next": "first"}, {"text": "$i18n:" + key("c2"), "next": "r2"}]},
                "first": {"type": "set_flag", "flag": f"{name}.prologue_first", "value": True, "next": "r1"},
                "r1": say("r1", "n3"),
                "r2": say("r2", "n3"),
                "n3": say("n3", "end", "gentle"),
            },
        }
        path = DATA / "dialogues" / name / "prologue.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for node, (text_en, text_it) in lines.items():
            en[key(node)], it[key(node)] = text_en, text_it
    add_texts("en", en)
    add_texts("it", it)
    print(f"wrote {len(PROLOGUES)} prologues")


if __name__ == "__main__":
    main()
