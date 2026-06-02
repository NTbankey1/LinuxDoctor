#!/usr/bin/env python3
"""
Training CLI — train, evaluate, and save ML models for Linux Doctor.

Usage:
    # Train all models (default)
    uv run python scripts/train.py

    # Train specific model only
    uv run python scripts/train.py --model svm
    uv run python scripts/train.py --model naive_bayes
    uv run python scripts/train.py --model logistic_regression

    # Custom dataset path
    uv run python scripts/train.py --data data/raw/linux_issues.jsonl

    # Custom output directory
    uv run python scripts/train.py --output models/

    # Quick mode: fewer iterations for testing
    uv run python scripts/train.py --quick

    # Generate dataset then train
    uv run python scripts/train.py --generate

    # Full pipeline: dataset → train → report
    uv run python scripts/generate_dataset.py && uv run python scripts/train.py
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root for imports when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from linux_doctor.ml.trainer import (
    load_dataset,
    train_test_split_manual,
    save_model,
    DATA_PATH,
    MODEL_DIR,
)
from linux_doctor.ml.tfidf_engine import TFIDFVectorizer
from linux_doctor.ml.naive_bayes import MultinomialNaiveBayes
from linux_doctor.ml.logistic_regression import LogisticRegression
from linux_doctor.ml.linear_svm import LinearSVM
from linux_doctor.ml.evaluator import Evaluator
from linux_doctor.infrastructure.logger import log


def train_model(
    name: str,
    X_train, X_test, y_train, y_test,
    evaluator, results, model_dir,
    **kwargs,
):
    """Train a single model by name."""
    if name == "naive_bayes":
        log.info("[cyan]Training Multinomial Naive Bayes...[/cyan]")
        alpha = kwargs.get("alpha", 1.0)
        model = MultinomialNaiveBayes(alpha=alpha)
        model.fit(X_train, y_train)

    elif name == "logistic_regression":
        log.info("[cyan]Training Logistic Regression...[/cyan]")
        lr = kwargs.get("lr", 0.3)
        iters = kwargs.get("iterations", 200)
        reg = kwargs.get("lambda_reg", 0.01)
        model = LogisticRegression(learning_rate=lr, n_iterations=iters, lambda_reg=reg, verbose=False)
        model.fit(X_train, y_train)

    elif name == "linear_svm":
        log.info("[cyan]Training Linear SVM (One-vs-Rest)...[/cyan]")
        lr = kwargs.get("lr", 0.01)
        iters = kwargs.get("iterations", 200)
        reg = kwargs.get("lambda_reg", 0.001)
        model = LinearSVM(learning_rate=lr, lambda_reg=reg, n_iterations=iters, verbose=False)
        model.fit(X_train, y_train)

    else:
        raise ValueError(f"Unknown model: {name}")

    preds = model.predict(X_test)
    report = evaluator.evaluate(y_test, preds)
    report.print()
    results[name] = report.weighted_f1
    save_model(model, model_dir / f"{name}.pkl")
    return model, report


def main():
    parser = argparse.ArgumentParser(
        description="Linux Doctor — ML Training Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model", "-m",
        choices=["all", "naive_bayes", "logistic_regression", "linear_svm"],
        default="all",
        help="Which model to train (default: all)",
    )
    parser.add_argument(
        "--data", "-d",
        type=Path,
        default=DATA_PATH,
        help=f"Dataset path (default: {DATA_PATH})",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=MODEL_DIR,
        help=f"Output directory for model artifacts (default: {MODEL_DIR})",
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick mode: fewer iterations, faster training",
    )
    parser.add_argument(
        "--generate", "-g",
        action="store_true",
        help="Generate dataset before training",
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Export evaluation report as JSON",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=None,
        help="Learning rate override (LR: 0.3, SVM: 0.01)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of training iterations",
    )
    parser.add_argument(
        "--lambda-reg",
        type=float,
        default=None,
        help="Regularization strength",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )

    args = parser.parse_args()

    # ── Generate dataset if requested ──
    if args.generate:
        log.info("[yellow]Generating dataset...[/yellow]")
        from scripts.generate_dataset import generate_samples as gen  # noqa: E402
        samples = gen()
        import random
        random.seed(args.seed)
        random.shuffle(samples)
        args.data.parent.mkdir(parents=True, exist_ok=True)
        with open(args.data, "w") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        from collections import Counter
        counts = Counter(s["label"] for s in samples)
        log.info(f"[green]Generated {len(samples)} samples: {dict(counts)}[/green]")

    # ── Validate data ──
    if not args.data.exists():
        log.error(f"[red]Dataset not found: {args.data}[/red]")
        log.info("Run with --generate to create it, or specify --data")
        sys.exit(1)

    # ── Configure hyperparams ──
    hparams = {}
    if args.lr is not None:
        hparams["lr"] = args.lr
    if args.iterations is not None:
        hparams["iterations"] = args.iterations
    if args.lambda_reg is not None:
        hparams["lambda_reg"] = args.lambda_reg
    if args.quick:
        hparams.setdefault("iterations", 50)

    # ── Load and preprocess ──
    log.info("[bold]Loading and preprocessing dataset...[/bold]")
    token_lists, labels = load_dataset(args.data)
    log.info(f"Loaded {len(labels)} samples, {len(set(labels))} classes: {sorted(set(labels))}")

    # ── TF-IDF ──
    log.info("Fitting TF-IDF vectorizer...")
    vectorizer = TFIDFVectorizer(max_features=3000, min_df=1)
    X = vectorizer.fit_transform(token_lists)
    log.info(f"Vocabulary size: {vectorizer.vocab_size}")

    # ── Train/Test split ──
    X_train, X_test, y_train, y_test = train_test_split_manual(X, labels, test_ratio=0.2, seed=args.seed)
    log.info(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

    # ── Train ──
    evaluator = Evaluator()
    results = {}
    models = {}

    args.output.mkdir(parents=True, exist_ok=True)

    if args.model in ("all", "naive_bayes"):
        m, _ = train_model("naive_bayes", X_train, X_test, y_train, y_test, evaluator, results, args.output, **hparams)
        models["naive_bayes"] = m

    if args.model in ("all", "logistic_regression"):
        m, _ = train_model("logistic_regression", X_train, X_test, y_train, y_test, evaluator, results, args.output, **hparams)
        models["logistic_regression"] = m

    if args.model in ("all", "linear_svm"):
        m, _ = train_model("linear_svm", X_train, X_test, y_train, y_test, evaluator, results, args.output, **hparams)
        models["linear_svm"] = m

    # ── Save best model ──
    best_name = max(results, key=results.__getitem__)
    log.info(f"\n[bold green]Best model: {best_name} (Weighted F1={results[best_name]:.4f})[/bold green]")
    save_model(models[best_name], args.output / "best_model.pkl")
    save_model(vectorizer, args.output / "vectorizer.pkl")

    # ── Summary ──
    print("\n── Model Comparison ──")
    for name, score in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {name:<25} Weighted F1 = {score:.4f}")
    print()

    # ── Export JSON report ──
    if args.report:
        report_path = args.output / "eval_report.json"
        with open(report_path, "w") as f:
            json.dump({
                "dataset": str(args.data),
                "n_samples": len(labels),
                "n_classes": len(set(labels)),
                "vocab_size": vectorizer.vocab_size,
                "train_size": X_train.shape[0],
                "test_size": X_test.shape[0],
                "results": {name: round(score, 4) for name, score in results.items()},
                "best_model": best_name,
                "best_f1": round(results[best_name], 4),
            }, f, indent=2)
        log.info(f"[green]Report saved: {report_path}[/green]")


if __name__ == "__main__":
    main()
