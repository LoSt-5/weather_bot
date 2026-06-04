"""Generate logical and code flowchart PNGs via Graphviz (auto-layout)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import graphviz

OUT_DIR = Path(__file__).resolve().parents[1] / "doc"
DPI = "180"
FONT = "Segoe UI"

_DOT_CANDIDATES = [
    Path(r"C:\Program Files\Graphviz\bin\dot.exe"),
    Path(r"C:\Program Files (x86)\Graphviz\bin\dot.exe"),
]


def _ensure_dot() -> None:
    if shutil.which("dot"):
        return
    for candidate in _DOT_CANDIDATES:
        if candidate.is_file():
            os.environ["PATH"] = str(candidate.parent) + os.pathsep + os.environ.get("PATH", "")
            return
    raise RuntimeError("Graphviz (dot) not found. Install: winget install Graphviz.Graphviz")


def _graph(name: str) -> graphviz.Digraph:
    g = graphviz.Digraph(name, format="png", engine="dot")
    g.attr(
        rankdir="TB",
        dpi=DPI,
        bgcolor="white",
        fontname=FONT,
        nodesep="0.55",
        ranksep="0.8",
        splines="true",
        pad="0.5",
        newrank="true",
    )
    g.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname=FONT,
        fontsize="12",
        margin="0.25,0.16",
        width="2.5",
        penwidth="1.3",
    )
    g.attr("edge", fontname=FONT, fontsize="10", penwidth="1.1", arrowsize="0.7")
    return g


def _render(g: graphviz.Digraph, filename: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_base = OUT_DIR / filename
    g.render(filename=str(out_base), cleanup=True)
    return out_base.with_suffix(".png")


def _add_nodes(g: graphviz.Digraph, nodes: dict[str, tuple[str, str, str, str]]) -> None:
    for nid, (label, fill, edge, shape) in nodes.items():
        g.node(nid, label, shape=shape, fillcolor=fill, color=edge)


def draw_logical() -> Path:
    g = _graph("logical")
    g.attr(label="Weather Bot — логическая схема", labelloc="t", fontsize="20", fontname=FONT)

    nodes = {
        "user": ("Пользователь\nTelegram-клиент", "#EBDEF0", "#6C3483", "box"),
        "tg": ("Telegram API", "#EBDEF0", "#6C3483", "box"),
        "api": ("WeatherAPI.com", "#EBDEF0", "#6C3483", "box"),
        "env": (".env\nBOT_TOKEN, WEATHER_API_KEY", "#FDEBD0", "#CA6F1E", "box"),
        "bot": ("weather_bot\nPython + aiogram 3", "#D6EAF8", "#1A5276", "box"),
        "start": ("Старт\nload_dotenv → Bot + Dispatcher", "#D5F5E3", "#1E8449", "box"),
        "poll": ("Long polling\nожидание update", "#D6EAF8", "#1A5276", "box"),
        "recv": ("Входящее сообщение", "#D6EAF8", "#1A5276", "box"),
        "route": ("Тип входа?", "#FCF3CF", "#B7950B", "diamond"),
        "cmd": ("/start → приветствие", "#D6EAF8", "#1A5276", "box"),
        "loc": ("Геолокация", "#D6EAF8", "#1A5276", "box"),
        "txt": ("Текст: город", "#D6EAF8", "#1A5276", "box"),
        "skip": ("Пусто / команда → стоп", "#FADBD8", "#922B21", "box"),
        "fetch": ("GET current.json\nq = coords или город", "#D6EAF8", "#1A5276", "box"),
        "check": ("HTTP 200?", "#FCF3CF", "#B7950B", "diamond"),
        "ok": ("Формат HTML", "#D6EAF8", "#1A5276", "box"),
        "err": ("Ошибка API / сети", "#FADBD8", "#922B21", "box"),
        "sent": ("Ответ в чат", "#D5F5E3", "#1E8449", "box"),
    }
    _add_nodes(g, nodes)

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("user")
        s.node("tg")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("env")
        s.node("bot")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("cmd")
        s.node("loc")
        s.node("txt")
        s.node("skip")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("ok")
        s.node("err")

    g.edge("user", "tg")
    g.edge("tg", "recv")
    g.edge("env", "bot")
    g.edge("bot", "start")
    g.edge("start", "poll")
    g.edge("poll", "recv")
    g.edge("recv", "route")
    g.edge("route", "cmd", label="/start")
    g.edge("route", "loc", label="location")
    g.edge("route", "txt", label="text")
    g.edge("route", "skip", label="иначе")
    g.edge("cmd", "sent")
    g.edge("loc", "fetch")
    g.edge("txt", "fetch")
    g.edge("fetch", "api", label="HTTP")
    g.edge("api", "check", label="JSON")
    g.edge("check", "ok", label="да")
    g.edge("check", "err", label="нет")
    g.edge("ok", "sent")
    g.edge("err", "sent")
    g.edge("sent", "poll", label="цикл", color="#7F8C8D", constraint="false")
    g.edge("skip", "poll", color="#7F8C8D", constraint="false")

    return _render(g, "diagram_logical")


def draw_code() -> Path:
    g = _graph("code")
    g.attr(label="Weather Bot — схема по коду (bot.py)", labelloc="t", fontsize="20", fontname=FONT)

    nodes = {
        "deps": ("requirements.txt\naiogram · aiohttp · dotenv", "#FDEBD0", "#CA6F1E", "box"),
        "imp": ("Импорты :1–7", "#FDEBD0", "#CA6F1E", "box"),
        "init": ("Инициализация :9–19\nload_dotenv, Bot, Dispatcher", "#D6EAF8", "#1A5276", "box"),
        "main": ("main() :117–118\nstart_polling", "#D5F5E3", "#1E8449", "box"),
        "entry": ("__main__ :120–122\nasyncio.run", "#D6EAF8", "#1A5276", "box"),
        "disp": ("Dispatcher", "#FCF3CF", "#B7950B", "diamond"),
        "hs": ("cmd_start :22–27\n/start", "#D6EAF8", "#1A5276", "box"),
        "hl": ("handle_location :30–53", "#D6EAF8", "#1A5276", "box"),
        "ht": ("handle_text :56–88", "#D6EAF8", "#1A5276", "box"),
        "typ": ("typing :34, :63", "#E8DAEF", "#6C3483", "box"),
        "http": ("HTTP GET :43–53, :72–88\nweatherapi current.json", "#D6EAF8", "#1A5276", "box"),
        "st": ("status == 200?", "#FCF3CF", "#B7950B", "diamond"),
        "sw": ("send_weather_info :90–114", "#D6EAF8", "#1A5276", "box"),
        "el": ("ошибка loc :50–53", "#FADBD8", "#922B21", "box"),
        "et": ("ошибка text :80–88", "#FADBD8", "#922B21", "box"),
        "ke": ("KeyError :112–114", "#FADBD8", "#922B21", "box"),
        "loop": ("следующий update", "#D5F5E3", "#1E8449", "box"),
    }
    _add_nodes(g, nodes)

    with g.subgraph(name="cluster_handlers") as c:
        c.attr(label="Обработчики @dp.message", style="rounded", color="#2874A6", fontcolor="#1A5276")
        for h in ("hs", "hl", "ht"):
            c.node(h)

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("hs")
        s.node("hl")
        s.node("ht")

    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("el")
        s.node("et")

    g.edge("deps", "imp", style="dashed")
    g.edge("imp", "init")
    g.edge("init", "main")
    g.edge("main", "entry")
    g.edge("entry", "disp")
    g.edge("disp", "hs", label="/start")
    g.edge("disp", "hl", label="location")
    g.edge("disp", "ht", label="F.text")
    g.edge("hs", "loop")
    g.edge("hl", "typ")
    g.edge("ht", "typ")
    g.edge("typ", "http")
    g.edge("http", "st")
    g.edge("st", "sw", label="да")
    g.edge("st", "el", label="нет")
    g.edge("st", "et", label="нет")
    g.edge("sw", "loop", label="OK")
    g.edge("sw", "ke", label="KeyError")
    g.edge("ke", "loop")
    g.edge("el", "loop")
    g.edge("et", "loop")
    g.edge("loop", "disp", label="цикл", color="#7F8C8D", constraint="false")

    return _render(g, "diagram_code")


if __name__ == "__main__":
    _ensure_dot()
    print(f"Saved: {draw_logical()}")
    print(f"Saved: {draw_code()}")
