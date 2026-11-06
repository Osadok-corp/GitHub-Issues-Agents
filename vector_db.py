"""Минимальная векторная БД (ChromaDB) для поиска кода в репозитории.

Использование из командной строки:
    python vector_db.py index https://github.com/owner/repo   # репозиторий с GitHub
    python vector_db.py index demo_repo                       # или локальная папка
    python vector_db.py search "discount is wrong"            # проверить поиск без LLM

Необязательно: переменная окружения GITHUB_TOKEN (повышает лимиты GitHub API).
"""
import argparse
import ast
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from github_parsing import get_repo_raw_urls, parse_code_by_url

DB_PATH = "chroma_db"        # папка, где Chroma хранит индекс на диске
COLLECTION_NAME = "code_chunks"
SKIP_DIRS = {"tests", "test", "docs", "doc", "examples", "benchmarks"}  # шум для поиска бага
BATCH_SIZE = 500             # по сколько чанков отправлять в Chroma за раз


def get_collection(reset=False):
    """Открывает (или пересоздаёт) коллекцию с чанками кода."""
    client = chromadb.PersistentClient(path=DB_PATH)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # коллекции ещё не было
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),  # all-MiniLM-L6-v2 (ONNX, локально)
        configuration={"hnsw": {"space": "cosine"}},    # косинусная метрика
    )


# 1. Получение исходников: {путь_в_репозитории: текст_файла}

def is_wanted(path):
    """Берём только .py файлы вне папок с тестами, документацией и т.п."""
    return path.endswith(".py") and not SKIP_DIRS & set(path.split("/")[:-1])


def download(url):
    try:
        return parse_code_by_url(url)
    except Exception:
        return None  # один неудачный файл не должен ронять всю индексацию


def load_files_from_github(repo_url):
    """Скачивает .py файлы репозитория через функции из github_parsing.py."""
    raw_urls = get_repo_raw_urls(repo_url, token=os.getenv("GITHUB_TOKEN"))
    paths = [p for p in raw_urls if is_wanted(p)]
    print(f"Найдено .py файлов: {len(paths)}. Скачиваю...")
    with ThreadPoolExecutor(max_workers=8) as pool:  # запросы по сети: качаем параллельно
        sources = list(pool.map(download, [raw_urls[p] for p in paths]))
    return {p: s for p, s in zip(paths, sources) if s is not None}


def load_files_from_folder(folder):
    """Для локальной папки"""
    root = Path(folder)
    files = {}
    for path in sorted(root.rglob("*.py")):
        rel_path = path.relative_to(root).as_posix()
        if is_wanted(rel_path):
            files[rel_path] = path.read_text(encoding="utf-8")
    return files


# 2. Чанкинг (один чанк - одна функция или метод)

def chunk_python_source(source, rel_path):
    """Режет текст .py файла на чанки (по функциям и методам классов)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # файл не разобрать (например, Python 2) — пропускаем
    lines = source.splitlines()

    # (узел функции, имя класса или None)
    functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append((node, None))
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append((sub, node.name))

    chunks = []
    for node, class_name in functions:
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        end = node.end_lineno
        qualname = f"{class_name}.{node.name}" if class_name else node.name
        code = "\n".join(lines[start - 1:end])
        chunks.append({
            "id": f"{rel_path}:{qualname}:{start}",
            # Заголовок с путём и именем тоже попадает в эмбеддинг:
            # так по запросу "cart" находится и файл cart.py, а не только тело функции.
            "text": f"# file: {rel_path}\n# function: {qualname}\n{code}",
            "metadata": {"file": rel_path, "name": qualname,
                         "start_line": start, "end_line": end},
        })
    return chunks


# 3. Индексация и поиск

def build_index(repo):
    """repo это URL на GitHub (https://github.com/owner/repo) или путь к локальной папке."""
    if repo.startswith("http"):
        files = load_files_from_github(repo)
    else:
        files = load_files_from_folder(repo)

    chunks = []
    for path, source in files.items():
        chunks += chunk_python_source(source, path)

    collection = get_collection(reset=True)  # каждый раз строим индекс с нуля
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],   # Chroma сама посчитает эмбеддинги
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  в индексе: {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")
    return len(chunks)


def search(query, n_results=3):
    """Возвращает n_results ближайших к запросу фрагментов кода."""
    collection = get_collection()
    result = collection.query(query_texts=[query], n_results=n_results)
    hits = []
    for doc, meta, dist in zip(result["documents"][0],
                               result["metadatas"][0],
                               result["distances"][0]):
        hits.append({**meta, "distance": dist, "code": doc})
    return hits


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index").add_argument("repo")
    sub.add_parser("search").add_argument("query")
    args = parser.parse_args()

    if args.command == "index":
        print(f"Проиндексировано чанков: {build_index(args.repo)}")
    else:
        for hit in search(args.query):
            print(f"{hit['file']}:{hit['start_line']}-{hit['end_line']}  "
                  f"{hit['name']}  (distance={hit['distance']:.3f})")
