import os
import sys

import click

from mycoursor.config import load_settings


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """mycoursor - AI-powered code assistant with semantic search."""
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--fresh", is_flag=True, help="Delete existing index and re-index from scratch.")
def index(path: str, fresh: bool):
    """Index a codebase for semantic search."""
    settings = load_settings()

    if not settings.gemini_api_key:
        click.echo("Error: GEMINI_API_KEY not set.", err=True)
        sys.exit(1)
    if not settings.database_url:
        click.echo("Error: DATABASE_URL not set.", err=True)
        sys.exit(1)

    root = os.path.abspath(path)
    click.echo(f"Indexing: {root}")

    from mycoursor.indexer.chunker import chunk_repository
    chunks = chunk_repository(root, settings)
    click.echo(f"Found {len(chunks)} chunk(s) across the repository.")

    if not chunks:
        click.echo("No files to index.")
        return

    if fresh:
        from mycoursor.indexer.store import clear_table
        click.echo("Clearing existing index...")
        clear_table(settings)

    click.echo("Generating embeddings...")
    from mycoursor.indexer.embedder import embed_chunks
    vectors = embed_chunks(chunks, settings)
    click.echo(f"Generated {len(vectors)} embedding(s).")

    click.echo("Storing in database...")
    from mycoursor.indexer.store import upsert_chunks
    count = upsert_chunks(chunks, vectors, settings)
    click.echo(f"Indexed {count} chunk(s) successfully.")


@cli.command()
@click.argument("query")
@click.option("-k", "--top-k", default=None, type=int, help="Number of results.")
def search(query: str, top_k: int | None):
    """Search the indexed codebase."""
    settings = load_settings()

    if not settings.gemini_api_key:
        click.echo("Error: GEMINI_API_KEY not set.", err=True)
        sys.exit(1)

    from mycoursor.retrieval.search import search as do_search
    results = do_search(query, settings, top_k=top_k)

    if not results:
        click.echo("No results found.")
        return

    for i, r in enumerate(results, 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"[{i}] {r.file_path} (lines {r.start_line}-{r.end_line}) score={r.score:.4f}")
        click.echo(f"{'='*60}")
        click.echo(r.text)


@cli.command()
@click.argument("question")
@click.option("-k", "--top-k", default=None, type=int, help="Number of context chunks.")
@click.option("--no-stream", is_flag=True, help="Disable streaming output.")
@click.option("--apply", "do_apply", is_flag=True, help="Auto-apply any edit blocks in the response.")
@click.option("--dry-run", is_flag=True, help="Show what edits would be applied without making changes.")
def ask(question: str, top_k: int | None, no_stream: bool, do_apply: bool, dry_run: bool):
    """Ask a question about the codebase."""
    settings = load_settings()

    if not settings.gemini_api_key:
        click.echo("Error: GEMINI_API_KEY not set.", err=True)
        sys.exit(1)

    click.echo("Searching for relevant code...")
    from mycoursor.retrieval.search import search as do_search
    results = do_search(question, settings, top_k=top_k)
    click.echo(f"Found {len(results)} relevant chunk(s).\n")

    from mycoursor.agent.llm import ask as llm_ask
    response = llm_ask(question, results, settings, stream=not no_stream)

    from mycoursor.agent.parser import parse_edit_blocks, format_edit_summary
    blocks = parse_edit_blocks(response)

    if blocks:
        click.echo(f"\n{format_edit_summary(blocks)}")

        if do_apply or dry_run:
            if do_apply and not dry_run:
                if not click.confirm("\nApply these changes?"):
                    click.echo("Cancelled.")
                    return
            from mycoursor.editor.apply import apply_edits
            edit_results = apply_edits(blocks, dry_run=dry_run)
            click.echo()
            for r in edit_results:
                status = "OK" if r.success else "FAIL"
                click.echo(f"  [{status}] {r.action}: {r.message}")


@cli.command()
@click.argument("response_file", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Preview changes without applying.")
def apply(response_file: str, dry_run: bool):
    """Apply edit blocks from a saved LLM response file."""
    with open(response_file, "r", encoding="utf-8") as f:
        response_text = f.read()

    from mycoursor.agent.parser import parse_edit_blocks, format_edit_summary
    blocks = parse_edit_blocks(response_text)

    if not blocks:
        click.echo("No edit blocks found in the file.")
        return

    click.echo(format_edit_summary(blocks))

    if not dry_run:
        if not click.confirm("\nApply these changes?"):
            click.echo("Cancelled.")
            return

    from mycoursor.editor.apply import apply_edits
    results = apply_edits(blocks, dry_run=dry_run)
    click.echo()
    for r in results:
        status = "OK" if r.success else "FAIL"
        click.echo(f"  [{status}] {r.action}: {r.message}")


@cli.command()
def status():
    """Show index status and configuration."""
    settings = load_settings()

    click.echo("Configuration:")
    click.echo(f"  Embedding model:  {settings.embedding_model}")
    click.echo(f"  LLM model:        {settings.llm_model}")
    click.echo(f"  Database:         {'connected' if settings.database_url else 'NOT SET'}")
    click.echo(f"  Gemini API key:   {'set' if settings.gemini_api_key else 'NOT SET'}")

    try:
        from mycoursor.indexer.store import collection_info
        info = collection_info(settings)
        click.echo(f"\nIndex status:")
        for k, v in info.items():
            click.echo(f"  {k}: {v}")
    except Exception as e:
        click.echo(f"\nIndex status: unavailable ({e})")


def main():
    cli()


if __name__ == "__main__":
    main()
