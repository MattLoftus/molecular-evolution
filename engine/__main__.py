"""
CLI entry point for molecular evolution.

Usage:
    python -m engine evolve [options]
    python -m engine serve
    python -m engine live
"""

import argparse
import sys


def cmd_evolve(args):
    from .evolver import EvolutionConfig, run_campaign

    config = EvolutionConfig(
        run_name=args.name,
        target_name=args.target,
        population_size=args.pop,
        num_generations=args.gens,
        crossover_prob=args.crossover,
        mutation_rate=args.mutation,
        max_tokens=args.max_tokens,
        tournament_size=args.tournament,
        elite_count=args.elite,
        dock_top_n=args.dock_top_n,
        dock_exhaustiveness=args.dock_exhaust,
        scaffold_hop=args.scaffold_hop,
        weight_qed=args.w_qed,
        weight_sa=args.w_sa,
        weight_novelty=args.w_novelty,
        weight_binding=args.w_binding,
        output_dir=args.output,
    )
    run_campaign(config, verbose=True)


def cmd_serve(args):
    from .serve import main
    main()


def cmd_live(args):
    from .ws_server import main
    main()


def main():
    parser = argparse.ArgumentParser(description='Molecular Evolution Engine')
    sub = parser.add_subparsers(dest='command')

    # evolve
    p_evolve = sub.add_parser('evolve', help='Run evolution campaign')
    p_evolve.add_argument('--name', default='default', help='Campaign name')
    p_evolve.add_argument('--pop', type=int, default=100, help='Population size')
    p_evolve.add_argument('--gens', type=int, default=200, help='Number of generations')
    p_evolve.add_argument('--crossover', type=float, default=0.7)
    p_evolve.add_argument('--mutation', type=float, default=0.3)
    p_evolve.add_argument('--max-tokens', type=int, default=30)
    p_evolve.add_argument('--tournament', type=int, default=3)
    p_evolve.add_argument('--elite', type=int, default=5)
    p_evolve.add_argument('--target', default='none', help='Docking target (EGFR)')
    p_evolve.add_argument('--dock-top-n', type=int, default=0, help='Dock top N per gen (0=off)')
    p_evolve.add_argument('--dock-exhaust', type=int, default=8, help='Vina exhaustiveness')
    p_evolve.add_argument('--scaffold-hop', action='store_true', help='Penalize similarity to known drugs')
    p_evolve.add_argument('--w-qed', type=float, default=0.45)
    p_evolve.add_argument('--w-sa', type=float, default=0.35)
    p_evolve.add_argument('--w-novelty', type=float, default=0.20)
    p_evolve.add_argument('--w-binding', type=float, default=0.0)
    p_evolve.add_argument('--output', default='results')

    # serve
    sub.add_parser('serve', help='Start HTTP API server')

    # live
    sub.add_parser('live', help='Start WebSocket + HTTP servers for live evolution')

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    {'evolve': cmd_evolve, 'serve': cmd_serve, 'live': cmd_live}[args.command](args)


if __name__ == '__main__':
    main()
