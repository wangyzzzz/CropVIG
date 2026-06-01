from __future__ import annotations

import argparse
from pathlib import Path

from crophg.internal.canonical_configs import (
    build_result32b_section_cfg,
    read_base_config,
    write_resolved_config,
)
from models.result33.parallel_launcher import run_result3_3_parallel_launcher
from models.result33.runner import run_result3_3

SECTION_CODE = "3.2B"
SECTION_SCOPE = "internal"
SECTION_SLUG = "representative_vi_window_effects"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"crophg {SECTION_CODE} scaffold entry")
    parser.add_argument("--input-dir", type=str, default="", help="Optional existing result directory")
    parser.add_argument("--output-dir", type=str, default="", help="Optional output directory")
    parser.add_argument("--config", type=str, default="", help="Optional config file")
    parser.add_argument("--n-workers", type=int, default=1, help="Use parallel light runner when greater than 1")
    parser.add_argument("--print-spec", action="store_true", help="Print scaffold metadata and exit")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.print_spec:
        print(f"section={SECTION_CODE}")
        print(f"scope={SECTION_SCOPE}")
        print(f"slug={SECTION_SLUG}")
        return 0
    if not args.config:
        raise ValueError(f"{SECTION_CODE} 需要 --config。")
    repo_root = Path.cwd().resolve()
    config_path = Path(args.config).resolve()
    base_cfg = read_base_config(config_path)

    resolved_cfg = build_result32b_section_cfg(
        base_cfg=base_cfg,
        output_dir=args.output_dir,
    )
    resolved_path = write_resolved_config(cfg=resolved_cfg, section_code=SECTION_CODE, repo_root=repo_root)
    if int(args.n_workers) > 1:
        out_dir = run_result3_3_parallel_launcher(resolved_path, n_workers=int(args.n_workers))
    else:
        out_dir = run_result3_3(resolved_path)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
