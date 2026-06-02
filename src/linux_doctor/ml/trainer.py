"""
ML Training Pipeline — ties all from-scratch components together.

Pipeline:
    JSONL Dataset
        ↓ text_engine.preprocess()
    Token Lists
        ↓ TFIDFVectorizer.fit_transform()
    Feature Matrices (NumPy)
        ↓ Model.fit()  [NaiveBayes | LogisticRegression | LinearSVM]
    Trained Models
        ↓ Evaluator.evaluate()
    Classification Report
        ↓ joblib.dump()
    Saved Model Artifacts
"""

import json
import pickle
from pathlib import Path

import numpy as np

from linux_doctor.infrastructure.logger import log
from linux_doctor.ml.evaluator import Evaluator
from linux_doctor.ml.linear_svm import LinearSVM
from linux_doctor.ml.logistic_regression import LogisticRegression
from linux_doctor.ml.naive_bayes import MultinomialNaiveBayes
from linux_doctor.ml.text_engine import preprocess
from linux_doctor.ml.tfidf_engine import TFIDFVectorizer

DATA_PATH = Path("data/raw/linux_issues.jsonl")
MODEL_DIR = Path("models")


def load_dataset(path: Path) -> tuple[list[list[str]], list[str]]:
    """Load and preprocess dataset from JSONL file."""
    token_lists, labels = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            tokens = preprocess(record["text"])
            token_lists.append(tokens)
            labels.append(record["label"])
    return token_lists, labels


def train_test_split_manual(
    X: np.ndarray, y: list[str], test_ratio: float = 0.2, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Manual stratified train/test split."""
    rng = np.random.default_rng(seed)

    # Group indices by class for stratification
    from collections import defaultdict
    class_indices: dict[str, list[int]] = defaultdict(list)
    for i, label in enumerate(y):
        class_indices[label].append(i)

    train_idx, test_idx = [], []
    for _label, indices in class_indices.items():
        indices_arr = np.array(indices)
        rng.shuffle(indices_arr)
        n_test = max(1, int(len(indices_arr) * test_ratio))
        test_idx.extend(indices_arr[:n_test].tolist())
        train_idx.extend(indices_arr[n_test:].tolist())

    X_train = X[train_idx]
    X_test  = X[test_idx]
    y_train = [y[i] for i in train_idx]
    y_test  = [y[i] for i in test_idx]
    return X_train, X_test, y_train, y_test


def save_model(obj: object, path: Path) -> None:
    """Serialize model using pickle."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    log.info(f"[green]✓ Saved: {path}[/green]")


def train_all(data_path: Path = DATA_PATH) -> None:
    """
    Train Naive Bayes, Logistic Regression, and Linear SVM.
    Evaluate each and save best model.
    """
    log.info("Loading and preprocessing dataset...")
    token_lists, labels = load_dataset(data_path)
    log.info(f"Loaded {len(labels)} samples, {len(set(labels))} classes.")

    # TF-IDF vectorization
    log.info("Fitting TF-IDF vectorizer...")
    vectorizer = TFIDFVectorizer(max_features=3000, min_df=1)
    X = vectorizer.fit_transform(token_lists)
    log.info(f"Vocabulary size: {vectorizer.vocab_size}")

    X_train, X_test, y_train, y_test = train_test_split_manual(X, labels)
    log.info(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

    evaluator = Evaluator()
    results: dict[str, float] = {}

    # --- Naive Bayes ---
    log.info("\n[cyan]Training Multinomial Naive Bayes...[/cyan]")
    nb = MultinomialNaiveBayes(alpha=1.0)
    nb.fit(X_train, y_train)
    nb_preds = nb.predict(X_test)
    nb_report = evaluator.evaluate(y_test, nb_preds)
    nb_report.print()
    results["naive_bayes"] = nb_report.weighted_f1
    save_model(nb, MODEL_DIR / "naive_bayes.pkl")

    # --- Logistic Regression ---
    log.info("\n[cyan]Training Logistic Regression...[/cyan]")
    lr = LogisticRegression(learning_rate=0.3, n_iterations=200, lambda_reg=0.01, verbose=False)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_report = evaluator.evaluate(y_test, lr_preds)
    lr_report.print()
    results["logistic_regression"] = lr_report.weighted_f1
    save_model(lr, MODEL_DIR / "logistic_regression.pkl")

    # --- Linear SVM ---
    log.info("\n[cyan]Training Linear SVM (One-vs-Rest + Hinge Loss)...[/cyan]")
    svm = LinearSVM(learning_rate=0.01, lambda_reg=0.001, n_iterations=200, verbose=False)
    svm.fit(X_train, y_train)
    svm_preds = svm.predict(X_test)
    svm_report = evaluator.evaluate(y_test, svm_preds)
    svm_report.print()
    results["linear_svm"] = svm_report.weighted_f1
    save_model(svm, MODEL_DIR / "linear_svm.pkl")

    # --- Save best model + vectorizer ---
    best_name = max(results, key=results.__getitem__)
    log.info(f"\n[bold green]Best model: {best_name} (Weighted F1={results[best_name]:.4f})[/bold green]")

    best_models = {"naive_bayes": nb, "logistic_regression": lr, "linear_svm": svm}
    save_model(best_models[best_name], MODEL_DIR / "best_model.pkl")
    save_model(vectorizer, MODEL_DIR / "vectorizer.pkl")

    # Summary table
    print("\n── Model Comparison ──")
    for name, score in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {name:<25} Weighted F1 = {score:.4f}")


if __name__ == "__main__":
    train_all()
