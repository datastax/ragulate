from typing import Any

from ragulate.debug import run_debug

from .utils import remove_sqlite_extension


def setup_debug(subparsers) -> None:  # type: ignore[no-untyped-def]
    """Setup the debug command."""
    debug_parser = subparsers.add_parser(
        "debug",
        help="Show the tru-lens dashboard to debug a recipe.",
    )
    debug_parser.add_argument(
        "-r",
        "--recipe",
        type=str,
        help="A recipe to see the dashboard for.",
        required=True,
    )
    debug_parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port to show the dashboard on, default 8501",
        default=8501,
    )
    debug_parser.set_defaults(func=lambda args: call_debug(**vars(args)))


def call_debug(
    recipe: str,
    port: int,
    **_: Any,
) -> None:
    """Runs the TruLens dashboard."""
    recipe_name = remove_sqlite_extension(recipe)
    run_debug(recipe_name=recipe_name, port=port)
