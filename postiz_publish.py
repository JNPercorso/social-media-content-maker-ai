"""
Адаптер: превращает наш архивный post.json (posts/YYYY-MM-DD_slug.json)
в JSON-структуру, которую реально ожидает Postiz CLI (--json режим).

ВАЖНО — это НЕ та структура, что описана в SKILL.md скилла postiz
(там написано про provider/post — этого поля в установленной версии
CLI не существует, проверено по исходнику node_modules/postiz/dist/index.js).
Реальная структура — та, что CLI сам строит внутри себя из флагов:

{
  "type": "schedule" | "draft",
  "creationMethod": "CLI",
  "date": "ISO8601",
  "shortLink": true,
  "tags": [],
  "posts": [
    {
      "integration": {"id": "<integration-id>"},
      "value": [
        {"content": "...", "image": [{"id": "...", "path": "<postiz-upload-url>"}], "delay": 0}
      ]
    }
  ]
}

Известные грабли:
- Многострочный текст через CLI-флаг -c ломает парсинг аргументов на Windows
  (npx-обёртка перетокенизирует строку) — поэтому ВСЕГДА используем --json,
  никогда -c для постов с переносами строк.
- image — это список объектов {id, path}, не просто список строк с URL.
- date обязателен всегда, даже для немедленной публикации (берём текущее
  время + пару минут).
- Картинку нужно сначала залить через `postiz upload <file>` и взять
  .path из ответа — нельзя передавать локальный путь или произвольный URL.
- X (Twitter) требует обязательное settings.who_can_reply_post
  (один из: everyone, following, mentionedUsers, subscribers, verified) —
  без него API возвращает 400. Скрипт ставит "everyone" по умолчанию для x.

Использование:
    python postiz_publish.py <путь_к_archive.json> <platform> <integration_id> <image_url> [--draft]

platform — ключ из platforms.* нашего архива (linkedin, x, threads, tenchat).
Скрипт печатает готовый JSON в stdout и сохраняет во временный файл
<platform>_post.json в текущей директории — его и передавать в
`postiz posts:create --json <platform>_post.json`.
"""
import json
import sys
from datetime import datetime, timedelta, timezone


def build_postiz_json(archive_path: str, platform: str, integration_id: str, image_url: str, draft: bool = False) -> dict:
    with open(archive_path, encoding="utf-8") as f:
        archive = json.load(f)

    content = archive["platforms"][platform]["content"]
    date = (datetime.now(timezone.utc) + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    image = [{"id": "img1", "path": image_url}] if image_url else []

    post_entry = {
        "integration": {"id": integration_id},
        "value": [
            {"content": content, "image": image, "delay": 0}
        ],
    }
    if platform == "x":
        post_entry["settings"] = {"who_can_reply_post": "everyone"}

    return {
        "type": "draft" if draft else "schedule",
        "creationMethod": "CLI",
        "date": date,
        "shortLink": True,
        "tags": [],
        "posts": [post_entry],
    }


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)

    archive_path, platform, integration_id, image_url = sys.argv[1:5]
    draft = "--draft" in sys.argv[5:]

    data = build_postiz_json(archive_path, platform, integration_id, image_url, draft)

    out_path = f"{platform}_post.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Записано: {out_path}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
